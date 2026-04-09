import os
import tempfile
import urllib.request
from io import BytesIO

from sqlalchemy.orm import Session
from fpdf import FPDF

from app.backend.db.models import DeliveryAddressTagModel, RegionModel, CommuneModel

TAG_LOGO_URL = "https://intrajis.com/assets/logo-1jO0MaUN.png"
TAG_LOGO_USER_AGENT = "Mozilla/5.0 (compatible; JISParking-ERP/1.0)"


def _title_case_words(s: str) -> str:
    t = (s or "").strip()
    if not t:
        return ""
    return " ".join(
        (w[0].upper() + w[1:].lower()) if w else "" for w in t.split()
    )


def _company_rut_line(company_rut: str) -> str:
    r = (company_rut or "").strip()
    if not r:
        return "Rut —"
    if r.lower().startswith("rut "):
        return r
    return f"Rut {r}"


def _fpdf_output_bytes(pdf: FPDF) -> bytes:
    """fpdf2 suele aceptar dest='S'; fpdf antiguo devuelve str → hay que codificar."""
    try:
        out = pdf.output(dest="S")
    except TypeError:
        out = pdf.output()
    if isinstance(out, (bytes, bytearray, memoryview)):
        return bytes(out)
    if isinstance(out, str):
        return out.encode("latin-1")
    raise TypeError(f"pdf.output() tipo inesperado: {type(out)}")


def _add_logo_mm(pdf: FPDF, x: float, y: float, w_mm: float) -> bool:
    """Descarga el logo y lo dibuja; compatible con fpdf clásico (solo ruta a archivo)."""
    try:
        req = urllib.request.Request(
            TAG_LOGO_URL,
            headers={"User-Agent": TAG_LOGO_USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        if not raw:
            return False
        try:
            pdf.image(BytesIO(raw), x=x, y=y, w=w_mm)
            return True
        except Exception:
            pass
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(raw)
            path = tmp.name
        try:
            pdf.image(path, x=x, y=y, w=w_mm)
            return True
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except Exception:
        return False


def _draw_double_rect(pdf: FPDF, x: float, y: float, w: float, h: float, gap: float) -> None:
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.45)
    pdf.rect(x, y, w, h, style="D")
    pdf.set_line_width(0.35)
    pdf.rect(x + gap, y + gap, w - 2 * gap, h - 2 * gap, style="D")


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
            "supervisor": tag.supervisor or "",
            "supervisor_rut": tag.supervisor_rut or "",
            "address": tag.address or "",
            "company_name": tag.company_name or "",
            "company_rut": tag.company_rut or "",
            "company_phone": tag.company_phone or "",
            "company_address": tag.company_address or "",
            "region_name": region_name or "",
            "commune_name": commune_name or "",
        }

    def generate_pdf_bytes(self, tag_id: int) -> bytes | None:
        """
        PDF etiqueta envío cuadrada (doble borde, bloque supervisor + Remite).
        Retorna bytes o None si no existe el id.
        """
        data = self.get_one_with_names(tag_id)
        if not data:
            return None
        if not (data["supervisor"] or "").strip():
            return None
        if not (data["address"] or "").strip():
            return None

        # Página cuadrada (misma anchura y altura en mm).
        W = 100.0
        H = 100.0
        M = 5.0
        pad_x = M + 3.0
        inner_w = W - 2 * pad_x
        gap_blocks = 3.5

        addr_commune = ", ".join(
            x
            for x in [
                (data["address"] or "").strip(),
                (data["commune_name"] or "").strip(),
            ]
            if x
        )
        top_lines = [
            data["supervisor"].strip(),
            data["supervisor_rut"].strip(),
            addr_commune,
            _title_case_words(data["region_name"] or ""),
        ]

        pdf = FPDF(orientation="P", unit="mm", format=(W, H))
        pdf.set_auto_page_break(False)
        pdf.set_margins(M, M, M)
        pdf.add_page()

        box_w = W - 2 * M
        box_h = H - 2 * M
        _draw_double_rect(pdf, M, M, box_w, box_h, 0.7)

        x = pad_x
        y = M + 4.0

        logo_w = 16.0
        x_logo = W - pad_x - logo_w
        y_logo = M + 3.0
        _add_logo_mm(pdf, x_logo, y_logo, logo_w)
        inner_w_top = max(20.0, inner_w - logo_w - 2.0)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        line_h_top = 4.6
        for line in top_lines:
            pdf.set_xy(x, y)
            # Sin new_x/new_y: compatible con fpdf antiguo (p. ej. servidor sin fpdf2 completo).
            pdf.multi_cell(inner_w_top, line_h_top, line, align="L")
            y = pdf.get_y()

        y += gap_blocks

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(x, y)
        pdf.multi_cell(inner_w, 4.0, "Remite :", align="L")
        y = pdf.get_y()

        pdf.set_font("Helvetica", "", 8.5)
        bottom_lines = [
            (data["company_name"] or "").strip(),
            _company_rut_line(data["company_rut"] or ""),
            (data["company_address"] or "").strip(),
            (data["company_phone"] or "").strip(),
        ]
        line_h_bot = 4.0
        for line in bottom_lines:
            pdf.set_xy(x, y)
            pdf.multi_cell(inner_w, line_h_bot, line, align="L")
            y = pdf.get_y()

        return _fpdf_output_bytes(pdf)
