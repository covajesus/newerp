import json
import os
import tempfile
import urllib.request
from datetime import datetime
from io import BytesIO
from pathlib import Path

import qrcode
import qrcode.constants
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.backend.db.models import DeliveryAddressTagModel, RegionModel, CommuneModel

TAG_LOGO_URL = "https://intrajis.com/assets/logo-1jO0MaUN.png"
TAG_LOGO_USER_AGENT = "Mozilla/5.0 (compatible; JISParking-ERP/1.0)"


def _fpdf_output_bytes(pdf: FPDF) -> bytes:
    """fpdf2: dest='S'; fpdf antiguo: str → latin-1. Evita TypeError con bytes(str)."""
    try:
        out = pdf.output(dest="S")
    except TypeError:
        out = pdf.output()
    if isinstance(out, (bytes, bytearray, memoryview)):
        return bytes(out)
    if isinstance(out, str):
        return out.encode("latin-1")
    raise TypeError(f"pdf.output() tipo inesperado: {type(out)}")


def _title_case_words(s: str) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    return " ".join(
        (w[0].upper() + w[1:].lower()) if w else "" for w in t.split()
    )


def _format_envio_display(digits: str) -> str:
    d = "".join(c for c in (digits or "") if c.isdigit())
    if len(d) <= 4:
        return d
    head = d[:4]
    rest = d[4:]
    parts = []
    while len(rest) > 3:
        parts.insert(0, rest[-3:])
        rest = rest[:-3]
    if rest:
        parts.insert(0, rest)
    dotted = ".".join(parts)
    return f"{head} - {dotted}"


def _shipment_digits(tag_id: int, region_id: int, commune_id: int) -> str:
    """Al menos 8 dígitos para Nº envío / QR numérico (misma idea que etiqueta postal)."""
    return f"{int(tag_id):04d}{int(region_id):03d}{int(commune_id):03d}"


def _qr_payload(data: dict) -> str:
    """JSON compacto con datos del tag (escaneable)."""
    addr_commune = ", ".join(
        x
        for x in [
            (data.get("address") or "").strip(),
            (data.get("commune_name") or "").strip(),
        ]
        if x
    )
    payload = {
        "t": "delivery_address_tag",
        "id": data["id"],
        "sucursal": (data.get("branch_office") or "").strip(),
        "supervisor": (data.get("supervisor") or "").strip(),
        "supervisor_rut": (data.get("supervisor_rut") or "").strip(),
        "direccion": addr_commune,
        "region": (data.get("region_name") or "").strip(),
        "telefono": (data.get("phone") or "").strip(),
        "empresa": (data.get("company_name") or "").strip(),
        "empresa_rut": (data.get("company_rut") or "").strip(),
        "empresa_tel": (data.get("company_phone") or "").strip(),
        "empresa_dir": (data.get("company_address") or "").strip(),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _datetime_es_cl() -> str:
    now = datetime.now()
    h24 = now.hour
    h12 = h24 % 12 or 12
    suf = "a. m." if h24 < 12 else "p. m."
    return f"{now.day:02d}-{now.month:02d}-{now.year} / {h12}:{now.minute:02d} {suf}"


def _resolve_logo_path() -> str | None:
    base = Path(__file__).resolve().parent.parent
    for name in ("static/logo.png", "static/jis_logo.png", "assets/logo.png"):
        p = base / name
        if p.is_file():
            return str(p)
    return None


def _logo_png_bytes() -> bytes | None:
    p = _resolve_logo_path()
    if p:
        try:
            raw = Path(p).read_bytes()
            if raw:
                return raw
        except OSError:
            pass
    try:
        req = urllib.request.Request(
            TAG_LOGO_URL,
            headers={"User-Agent": TAG_LOGO_USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read() or None
    except Exception:
        return None


def _draw_qr_mm(pdf: FPDF, qr_payload: str, x: float, y: float, w_mm: float) -> bool:
    """
    Incrusta QR en el PDF. PIL RGB + fallbacks (BytesIO / archivo) por compatibilidad fpdf2/Pillow.
    """
    try:
        qr = qrcode.QRCode(
            version=None,
            box_size=3,
            border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
        )
        qr.add_data(qr_payload)
        qr.make(fit=True)
        im = qr.make_image(fill_color="black", back_color="white")
    except Exception:
        return False

    im_rgb = im.convert("RGB") if im.mode != "RGB" else im

    try:
        pdf.image(im_rgb, x=x, y=y, w=w_mm, h=w_mm)
        return True
    except Exception:
        pass
    try:
        buf = BytesIO()
        im_rgb.save(buf, format="PNG")
        buf.seek(0)
        pdf.image(buf, x=x, y=y, w=w_mm, h=w_mm)
        return True
    except Exception:
        pass
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            im_rgb.save(tmp.name, format="PNG")
            path = tmp.name
        try:
            pdf.image(path, x=x, y=y, w=w_mm, h=w_mm)
            return True
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        return False


def _draw_logo_mm(pdf: FPDF, x: float, y: float, w_mm: float) -> bool:
    raw = _logo_png_bytes()
    if not raw:
        return False
    try:
        pdf.image(BytesIO(raw), x=x, y=y, w=w_mm, h=0)
        return True
    except Exception:
        pass
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            path = tmp.name
        try:
            pdf.image(path, x=x, y=y, w=w_mm, h=0)
            return True
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        return False


class DeliveryAddressTagClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all_with_names(self):
        """Listado para etiquetas: incluye nombres de región y comuna."""
        try:
            rows = (
                self.db.query(
                    DeliveryAddressTagModel,
                    RegionModel.region.label("region_name"),
                    CommuneModel.commune.label("commune_name"),
                )
                .outerjoin(RegionModel, RegionModel.id == DeliveryAddressTagModel.region_id)
                .outerjoin(CommuneModel, CommuneModel.id == DeliveryAddressTagModel.commune_id)
                .order_by(DeliveryAddressTagModel.branch_office.asc())
                .all()
            )
            if not rows:
                return []

            out = []
            for tag, region_name, commune_name in rows:
                out.append(
                    {
                        "id": tag.id,
                        "region_id": tag.region_id,
                        "commune_id": tag.commune_id,
                        "branch_office": tag.branch_office,
                        "address": tag.address,
                        "supervisor_rut": tag.supervisor_rut,
                        "supervisor": tag.supervisor,
                        "phone": tag.phone,
                        "company_name": tag.company_name,
                        "company_rut": tag.company_rut,
                        "company_phone": tag.company_phone,
                        "company_address": tag.company_address,
                        "region_name": region_name,
                        "commune_name": commune_name,
                        "added_date": tag.added_date.isoformat() if tag.added_date else None,
                        "updated_date": tag.updated_date.isoformat() if tag.updated_date else None,
                    }
                )
            return out
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_one_with_names(self, tag_id: int):
        row = (
            self.db.query(
                DeliveryAddressTagModel,
                RegionModel.region.label("region_name"),
                CommuneModel.commune.label("commune_name"),
            )
            .outerjoin(RegionModel, RegionModel.id == DeliveryAddressTagModel.region_id)
            .outerjoin(CommuneModel, CommuneModel.id == DeliveryAddressTagModel.commune_id)
            .filter(DeliveryAddressTagModel.id == tag_id)
            .first()
        )
        if not row:
            return None
        tag, region_name, commune_name = row
        return {
            "id": tag.id,
            "region_id": tag.region_id,
            "commune_id": tag.commune_id,
            "branch_office": tag.branch_office or "",
            "supervisor": tag.supervisor or "",
            "supervisor_rut": tag.supervisor_rut or "",
            "address": tag.address or "",
            "phone": tag.phone,
            "company_name": tag.company_name or "",
            "company_rut": tag.company_rut or "",
            "company_phone": tag.company_phone or "",
            "company_address": tag.company_address or "",
            "region_name": region_name or "",
            "commune_name": commune_name or "",
        }

    def generate_pdf_bytes(self, tag_id: int) -> bytes | None:
        """
        PDF etiqueta envío alargada (vertical): logo JIS en cabecera, DE, QR, Nº envío, A, datos.
        Formato ~100×148 mm (estilo segunda referencia).
        """
        data = self.get_one_with_names(tag_id)
        if not data:
            return None
        if not (data["supervisor"] or "").strip():
            return None
        if not (data["address"] or "").strip():
            return None

        W = 100.0
        H = 148.0
        M = 4.0
        inner_w = W - 2 * M

        addr_commune = ", ".join(
            x
            for x in [
                (data["address"] or "").strip(),
                (data["commune_name"] or "").strip(),
            ]
            if x
        )
        full_dir = ", ".join(
            x
            for x in [addr_commune, _title_case_words(data["region_name"] or "")]
            if x
        )

        digits = _shipment_digits(data["id"], data["region_id"], data["commune_id"])
        envio_txt = _format_envio_display(digits)
        city_a = ((data.get("commune_name") or "").strip() or (data.get("branch_office") or "").strip()).upper()

        pdf = FPDF(orientation="P", unit="mm", format=(W, H))
        pdf.set_auto_page_break(False)
        pdf.set_margins(M, M, M)
        pdf.add_page()

        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.35)
        pdf.rect(M, M, inner_w, H - 2 * M)

        y0 = M + 1.2
        header_h = 16.0
        logo_col_w = 16.0
        date_col_w = 34.0

        if not _draw_logo_mm(pdf, M + 0.5, y0 + 0.3, logo_col_w):
            pdf.set_xy(M + 0.5, y0 + 4)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(logo_col_w, 4, "JIS", align="L")

        title_x = M + logo_col_w + 1.5
        title_w = max(20.0, inner_w - logo_col_w - 1.5 - date_col_w)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(title_x, y0 + 5)
        pdf.cell(title_w, 5, "ETIQUETA DE ENVÍO", align="C")

        pdf.set_font("Helvetica", "", 6)
        pdf.set_text_color(50, 50, 50)
        dt = _datetime_es_cl()
        tw = pdf.get_string_width(dt)
        pdf.set_xy(W - M - tw - 0.5, y0 + 2)
        pdf.cell(tw, 4, dt)
        pdf.set_text_color(0, 0, 0)

        header_bottom = y0 + header_h
        pdf.line(M, header_bottom, W - M, header_bottom)
        y = header_bottom + 2.2

        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(M + 1, y)
        pdf.cell(8, 4, "DE:")
        pdf.set_font("Helvetica", "", 7)
        de_name = (data["company_name"] or "").strip() or "JIS Parking SpA"
        pdf.set_xy(M + 10, y)
        pdf.multi_cell(inner_w - 11, 3.3, de_name, align="L")
        y = pdf.get_y() + 1.8

        pdf.line(M, y, W - M, y)
        y += 3

        qr_payload = _qr_payload(data)
        qr_mm = 40.0
        qr_pad = 1.5
        qr_block_h = qr_mm + qr_pad * 2 + 4.5
        pdf.set_line_width(0.25)
        pdf.rect(M, y, inner_w, qr_block_h)

        qr_x = M + (inner_w - qr_mm) / 2
        qr_y = y + qr_pad
        if not _draw_qr_mm(pdf, qr_payload, qr_x, qr_y, qr_mm):
            pdf.set_xy(M + 2, qr_y + qr_mm / 2 - 4)
            pdf.set_font("Helvetica", "", 6)
            pdf.multi_cell(inner_w - 4, 3, "(QR no disponible)", align="C")

        pdf.set_font("Helvetica", "", 6.5)
        tw_e = pdf.get_string_width(envio_txt)
        pdf.set_xy(W - M - tw_e - 1.5, y + qr_block_h - 4.5)
        pdf.cell(tw_e, 3, envio_txt)

        y = y + qr_block_h + 2.5
        pdf.set_line_width(0.35)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_xy(M + 1, y)
        pdf.cell(inner_w, 4, "Nº ENVÍO")
        y += 4.2
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_xy(M + 1, y)
        pdf.cell(inner_w, 7, envio_txt)
        y += 8.5

        pdf.line(M, y, W - M, y)
        y += 3

        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(M + 1, y)
        pdf.cell(6, 4, "A:")
        y += 4.2
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_xy(M + 1, y)
        pdf.cell(inner_w - 2, 8, city_a[:80])
        y += 9

        pdf.line(M, y, W - M, y)
        y += 2.5

        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(M + 1, y)
        pdf.cell(12, 3.5, "Para:")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_xy(M + 13, y)
        pdf.multi_cell(inner_w - 14, 3.2, (data["supervisor"] or "").strip(), align="L")
        y = pdf.get_y() + 0.5

        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(M + 1, y)
        pdf.cell(12, 3.5, "Dir.:")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_xy(M + 13, y)
        pdf.multi_cell(inner_w - 14, 3.2, full_dir or "—", align="L")
        y = pdf.get_y() + 0.5

        tel_s = (data.get("phone") or "").strip() or "—"
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_xy(M + 1, y)
        pdf.cell(12, 3.5, "Tel.:")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_xy(M + 13, y)
        pdf.multi_cell(inner_w - 14, 3.2, tel_s, align="L")
        y = pdf.get_y() + 0.5

        obs = f"Sucursal: {(data.get('branch_office') or '').strip()} · Sup. RUT: {(data.get('supervisor_rut') or '').strip()}"
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_xy(M + 1, y)
        pdf.cell(14, 3, "Obs.:")
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_xy(M + 15, y)
        pdf.multi_cell(inner_w - 16, 3, obs, align="L")

        return _fpdf_output_bytes(pdf)
