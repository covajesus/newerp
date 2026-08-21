"""Cotizaciones de abonados (no DTE SII)."""

from __future__ import annotations

import html
import io
import os
import re
import secrets
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import requests
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
from app.backend.classes.whatsapp_class import (
    WHATSAPP_TEMPLATE_QUOTATION_TITLE,
    _whatsapp_template_quotation,
    whatsapp_access_token,
    whatsapp_graph_messages_url,
)
from app.backend.db.models import (
    BranchOfficeModel,
    CustomerDteItemModel,
    CustomerModel,
    DteModel,
    DteReferenceModel,
    QuotationItemModel,
    QuotationModel,
    QuotationReferenceModel,
    UserModel,
)

DTE_VERSION_V2 = 2
STATUS_DRAFT = 1
STATUS_SENT = 2
STATUS_CONVERTED = 3
STATUS_ANNULLED = 4
RENEW_FIXED = 1
RENEW_MONTHLY = 2
JIS_PRIMARY = "#152d8a"
ISSUER_RUT = "76.063.822-6"
ISSUER_NAME = "JIS PARKING SPA"
ISSUER_GIRO = "ESTACIONAMIENTO DE VEHÍCULOS Y PARQUÍMETROS, VENTA DE PRODUCTOS FARMACEUTICOS"
ISSUER_HQ = "Casa matriz: Matucana 40, Estación Central"
ISSUER_PHONE = "+56 2 26825312"
ISSUER_EMAIL = "contacto@jisparking.com"
_MONTHS_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
_WEEKDAYS_ES = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


class QuotationClass:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _clean_str(value) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        return s or None

    @staticmethod
    def _format_clp(amount: int) -> str:
        try:
            n = int(amount)
        except (TypeError, ValueError):
            return "$ 0"
        return f"$ {n:,.0f}".replace(",", ".")

    @staticmethod
    def _format_clp_plain(amount: int) -> str:
        try:
            n = int(amount)
        except (TypeError, ValueError):
            return "0"
        return f"{n:,.0f}".replace(",", ".")

    @staticmethod
    def _format_date_short(dt: Optional[datetime]) -> str:
        d = dt or datetime.now()
        return d.strftime("%d-%m-%Y")

    @staticmethod
    def _format_date_long(dt: Optional[datetime]) -> str:
        d = dt or datetime.now()
        return f"{_WEEKDAYS_ES[d.weekday()]} {d.day} de {_MONTHS_ES[d.month - 1]} del {d.year}"

    def _branch_contact(self, branch: Optional[BranchOfficeModel]) -> dict[str, str]:
        """Contacto comercial para WhatsApp / pie de PDF (supervisor de sucursal)."""
        name = "JIS Parking"
        phone = ISSUER_PHONE.replace("+56 ", "").replace(" ", "")
        email = ISSUER_EMAIL
        if not branch:
            return {"name": name, "phone": phone, "email": email}
        supervisor_key = getattr(branch, "principal_supervisor", None)
        user = None
        if supervisor_key not in (None, "", 0):
            user = (
                self.db.query(UserModel)
                .filter(UserModel.rut == supervisor_key)
                .first()
            )
            if not user:
                user = (
                    self.db.query(UserModel)
                    .filter(UserModel.id == supervisor_key)
                    .first()
                )
        if user:
            name = (user.full_name or name).strip() or name
            if user.phone and str(user.phone).strip():
                phone = re.sub(r"\D", "", str(user.phone)) or phone
            if user.email and "@" in str(user.email):
                email = str(user.email).strip()
        return {"name": name, "phone": phone, "email": email}

    def _logo_path(self) -> Optional[str]:
        env_logo = (os.getenv("DTE_EMAIL_LOGO_PATH") or "").strip()
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            env_logo,
            # Prefer RGB version for ReportLab (RGBA often renders blank)
            os.path.join(here, "..", "static", "logo_pdf.png"),
            os.path.join(here, "..", "static", "logo.png"),
            os.path.join(here, "..", "..", "..", "static", "logo.png"),
            os.path.join(here, "..", "..", "..", "files", "logo.png"),
            "/var/www/intrajisbackend.com/public_html/app/backend/static/logo_pdf.png",
            "/var/www/intrajisbackend.com/public_html/app/backend/static/logo.png",
            "/var/www/intrajisbackend.com/public_html/files/logo.png",
            "/var/www/intrajisbackend.com/public_html/assets/logo.png",
            "/var/www/intrajisbackend.com/public_html/static/logo.png",
        ]
        for path in candidates:
            if not path:
                continue
            full = os.path.abspath(path)
            if os.path.isfile(full):
                return full
        return None

    def _logo_flowable(self, width_cm: float = 2.4, height_cm: float = 2.4):
        logo_path = self._logo_path()
        if not logo_path:
            return ""
        try:
            # ReportLab can drop RGBA logos; flatten onto white then embed.
            from PIL import Image as PILImage

            src = PILImage.open(logo_path)
            if src.mode in ("RGBA", "LA", "P"):
                rgba = src.convert("RGBA")
                bg = PILImage.new("RGBA", rgba.size, (255, 255, 255, 255))
                flat = PILImage.alpha_composite(bg, rgba).convert("RGB")
            else:
                flat = src.convert("RGB")
            buf = io.BytesIO()
            flat.save(buf, format="PNG")
            buf.seek(0)
            img = Image(buf, width=width_cm * cm, height=height_cm * cm)
            img.hAlign = "LEFT"
            return img
        except Exception as e:
            print(f"Quotation PDF logo error ({logo_path}): {e}")
            try:
                img = Image(logo_path, width=width_cm * cm, height=height_cm * cm)
                img.hAlign = "LEFT"
                return img
            except Exception as e2:
                print(f"Quotation PDF logo fallback error: {e2}")
                return ""

    def _normalize_items(self, items) -> list[dict]:
        normalized = []
        if not items:
            return normalized
        for idx, item in enumerate(items, start=1):
            if hasattr(item, "model_dump"):
                plain = item.model_dump()
            elif isinstance(item, dict):
                plain = item
            else:
                plain = {
                    "quantity": getattr(item, "quantity", None),
                    "unit_amount": getattr(item, "unit_amount", None),
                    "amount": getattr(item, "amount", None),
                    "description": getattr(item, "description", None),
                    "item_code": getattr(item, "item_code", None),
                    "item_name": getattr(item, "item_name", None),
                    "unit_measure": getattr(item, "unit_measure", None),
                    "discount_amount": getattr(item, "discount_amount", None),
                    "dsc_item": getattr(item, "dsc_item", None),
                }
            try:
                q = int(plain.get("quantity") or 0)
                u = int(plain.get("unit_amount") or 0)
            except (TypeError, ValueError):
                continue
            detail = (plain.get("description") or "").strip()
            name = self._clean_str(plain.get("item_name"))
            code = self._clean_str(plain.get("item_code"))
            if q < 1 or u < 0 or (not detail and not name and not code):
                continue
            try:
                total = int(plain["amount"]) if plain.get("amount") is not None else q * u
            except (TypeError, ValueError):
                total = q * u
            if total <= 0:
                total = q * u
            try:
                da = int(plain.get("discount_amount") or 0)
            except (TypeError, ValueError):
                da = 0
            dsc = self._clean_str(plain.get("dsc_item")) or detail or name or code
            normalized.append(
                {
                    "line_number": idx,
                    "quantity": q,
                    "unit_amount": u,
                    "total_amount": total,
                    "description": detail if detail else "-",
                    "item_code": code,
                    "item_name": name,
                    "unit_measure": self._clean_str(plain.get("unit_measure")) or "Und",
                    "discount_amount": da,
                    "dsc_item": dsc,
                }
            )
        return normalized

    def _normalize_references(self, references) -> list[dict]:
        """Same fields as dte_references / factura category 2. Empty lines are dropped."""
        out: list[dict] = []
        if not references:
            return out
        for ref in references:
            if hasattr(ref, "model_dump"):
                plain = ref.model_dump()
            elif isinstance(ref, dict):
                plain = ref
            else:
                plain = {
                    "reference_type_id": getattr(ref, "reference_type_id", None),
                    "reference_date_id": getattr(ref, "reference_date_id", None),
                    "reference_code": getattr(ref, "reference_code", None),
                    "reference_description": getattr(ref, "reference_description", None),
                }
            type_id = self._clean_str(plain.get("reference_type_id"))
            date_id = self._clean_str(plain.get("reference_date_id"))
            code = self._clean_str(plain.get("reference_code"))
            desc = self._clean_str(plain.get("reference_description"))
            if not any([type_id, date_id, code, desc]):
                continue
            out.append(
                {
                    "reference_type_id": type_id,
                    "reference_date_id": date_id,
                    "reference_code": code,
                    "reference_description": desc,
                }
            )
        return out

    def _compute_totals(self, items: list[dict], chip_id: int = 0) -> tuple[int, int, int]:
        """Líneas en neto (como factura grupal V2 cat. 3). Chip se suma al bruto."""
        net = sum(int(i["total_amount"]) for i in items)
        tax = round(net * 0.19)
        total = net + tax
        if int(chip_id or 0) == 1:
            total += 5000
        return net, tax, total

    def _next_quotation_number(self) -> str:
        year = datetime.now().year
        prefix = f"COT-{year}-"
        last = (
            self.db.query(QuotationModel.quotation_number)
            .filter(QuotationModel.quotation_number.like(f"{prefix}%"))
            .order_by(desc(QuotationModel.id))
            .first()
        )
        seq = 1
        if last and last[0]:
            m = re.search(r"(\d+)$", last[0])
            if m:
                seq = int(m.group(1)) + 1
        return f"{prefix}{seq:04d}"

    def _replace_items(self, quotation_id: int, items: list[dict]):
        self.db.query(QuotationItemModel).filter(
            QuotationItemModel.quotation_id == quotation_id
        ).delete(synchronize_session=False)
        now = datetime.now()
        for item in items:
            self.db.add(
                QuotationItemModel(
                    quotation_id=quotation_id,
                    line_number=item["line_number"],
                    quantity=item["quantity"],
                    unit_amount=item["unit_amount"],
                    total_amount=item["total_amount"],
                    description=item["description"],
                    item_code=item.get("item_code"),
                    item_name=item.get("item_name"),
                    unit_measure=item.get("unit_measure"),
                    discount_amount=int(item.get("discount_amount") or 0),
                    dsc_item=item.get("dsc_item"),
                    status_id=1,
                    added_date=now,
                    updated_date=now,
                )
            )

    def _replace_references(self, quotation_id: int, references: list[dict]):
        self.db.query(QuotationReferenceModel).filter(
            QuotationReferenceModel.quotation_id == quotation_id
        ).delete(synchronize_session=False)
        now = datetime.now()
        for ref in references:
            self.db.add(
                QuotationReferenceModel(
                    quotation_id=quotation_id,
                    reference_type_id=ref.get("reference_type_id"),
                    reference_date_id=ref.get("reference_date_id"),
                    reference_code=ref.get("reference_code"),
                    reference_description=ref.get("reference_description"),
                    added_date=now,
                )
            )

    def _load_references(self, quotation_id: int) -> list[dict]:
        rows = (
            self.db.query(QuotationReferenceModel)
            .filter(QuotationReferenceModel.quotation_id == quotation_id)
            .order_by(QuotationReferenceModel.id.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "reference_type_id": r.reference_type_id,
                "reference_date_id": r.reference_date_id,
                "reference_code": r.reference_code,
                "reference_description": r.reference_description,
            }
            for r in rows
        ]

    def _serialize(self, q: QuotationModel, include_items: bool = False) -> dict:
        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == q.branch_office_id)
            .first()
        )
        data = {
            "id": q.id,
            "quotation_number": q.quotation_number,
            "branch_office_id": q.branch_office_id,
            "branch_office": branch.branch_office if branch else None,
            "branch_office_address": (
                (getattr(branch, "address", None) or "").strip() or None
            )
            if branch
            else None,
            "rut": q.rut,
            "customer": q.customer,
            "email": q.email,
            "phone": q.phone,
            "activity": q.activity,
            "address": q.address,
            "region_id": q.region_id,
            "commune_id": q.commune_id,
            "period": q.period,
            "period_label": HelperClass.period_detail_label(q.period or ""),
            "renew_mode": q.renew_mode,
            "send_email": int(getattr(q, "send_email", 1) or 0),
            "send_whatsapp": int(getattr(q, "send_whatsapp", 0) or 0),
            "status_id": q.status_id,
            "chip_id": q.chip_id,
            "subtotal": q.subtotal,
            "tax": q.tax,
            "total": q.total,
            "last_sent_at": q.last_sent_at.strftime("%d-%m-%Y %H:%M") if q.last_sent_at else None,
            "last_sent_channel": q.last_sent_channel,
            "email_read": int(getattr(q, "email_read", 0) or 0),
            "email_read_at": (
                q.email_read_at.strftime("%d-%m-%Y %H:%M")
                if getattr(q, "email_read_at", None)
                else None
            ),
            "converted_dte_id": q.converted_dte_id,
            "source_quotation_id": q.source_quotation_id,
            "added_date": q.added_date.strftime("%d-%m-%Y") if q.added_date else None,
            "updated_date": q.updated_date.strftime("%d-%m-%Y") if q.updated_date else None,
        }
        if include_items:
            rows = (
                self.db.query(QuotationItemModel)
                .filter(QuotationItemModel.quotation_id == q.id)
                .order_by(QuotationItemModel.line_number)
                .all()
            )
            data["items"] = [
                {
                    "id": r.id,
                    "line_number": r.line_number,
                    "quantity": r.quantity,
                    "unit_amount": r.unit_amount,
                    "total_amount": r.total_amount,
                    "amount": r.total_amount,
                    "description": r.description,
                    "dsc_item": r.dsc_item,
                    "item_code": r.item_code,
                    "item_name": r.item_name,
                    "unit_measure": r.unit_measure,
                    "discount_amount": r.discount_amount,
                }
                for r in rows
            ]
            data["references"] = self._load_references(q.id)
        return data

    # ------------------------------------------------------------------ CRUD
    def get_all(self, page: int = 1, items_per_page: int = 10):
        return self.search(page=page, items_per_page=items_per_page)

    def search(
        self,
        *,
        page: int = 1,
        items_per_page: int = 10,
        rut: Optional[str] = None,
        customer: Optional[str] = None,
        period: Optional[str] = None,
        renew_mode: Optional[int] = None,
        status_id: Optional[int] = None,
        branch_office_id: Optional[int] = None,
    ):
        try:
            q = self.db.query(QuotationModel).filter(QuotationModel.status_id != STATUS_ANNULLED)
            if rut:
                q = q.filter(QuotationModel.rut.like(f"%{rut.strip()}%"))
            if customer:
                q = q.filter(QuotationModel.customer.like(f"%{customer.strip()}%"))
            if period:
                q = q.filter(QuotationModel.period == period.strip())
            if renew_mode is not None:
                q = q.filter(QuotationModel.renew_mode == int(renew_mode))
            if status_id is not None:
                q = q.filter(QuotationModel.status_id == int(status_id))
            if branch_office_id:
                q = q.filter(QuotationModel.branch_office_id == int(branch_office_id))

            total_items = q.count()
            total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
            if page < 1:
                page = 1
            if total_items == 0:
                return {
                    "total_items": 0,
                    "total_pages": 0,
                    "current_page": page,
                    "items_per_page": items_per_page,
                    "data": [],
                }
            if page > total_pages:
                return {"status": "error", "message": "Invalid page number"}

            rows = (
                q.order_by(desc(QuotationModel.id))
                .offset((page - 1) * items_per_page)
                .limit(items_per_page)
                .all()
            )
            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": [self._serialize(r) for r in rows],
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get(self, quotation_id: int):
        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q or q.status_id == STATUS_ANNULLED:
            return {"status": "error", "message": "Cotización no encontrada"}
        return {"status": "success", "data": self._serialize(q, include_items=True)}

    def prefill_from_dte(self, dte_id: int) -> dict:
        """Payload to create a quotation from an emitted subscriber ticket/bill."""
        dte = self.db.query(DteModel).filter(DteModel.id == int(dte_id)).first()
        if not dte:
            return {"status": "error", "message": "DTE no encontrado"}
        if int(dte.dte_type_id or 0) not in (33, 39):
            return {"status": "error", "message": "Solo boletas (39) o facturas (33)"}

        customer = None
        if dte.rut:
            customer = (
                self.db.query(CustomerModel)
                .filter(CustomerModel.rut == str(dte.rut).strip())
                .first()
            )

        item_rows = (
            self.db.query(CustomerDteItemModel)
            .filter(CustomerDteItemModel.dte_id == dte.id)
            .order_by(CustomerDteItemModel.line_number.asc(), CustomerDteItemModel.id.asc())
            .all()
        )
        items = []
        for r in item_rows:
            try:
                q = int(r.quantity or 0)
                u = int(r.unit_amount or 0)
            except (TypeError, ValueError):
                continue
            if q < 1 or u < 0:
                continue
            items.append(
                {
                    "item_code": (r.item_code or "").strip() or "",
                    "item_name": (r.item_name or "").strip() or "",
                    "quantity": q,
                    "unit_measure": (r.unit_measure or "").strip() or "Und",
                    "unit_amount": u,
                    "discount": int(getattr(r, "discount_amount", 0) or 0),
                    "description": (r.description or "").strip() or (getattr(r, "dsc_item", None) or "").strip() or "",
                }
            )

        if not items:
            total = int(dte.total or 0)
            net = int(round(total / 1.19)) if total > 0 else 0
            if net <= 0:
                return {"status": "error", "message": "El DTE no tiene líneas ni monto para cotizar"}
            items.append(
                {
                    "item_code": "",
                    "item_name": "Servicio de estacionamiento",
                    "quantity": 1,
                    "unit_measure": "Und",
                    "unit_amount": net,
                    "discount": 0,
                    "description": HelperClass.period_detail_label(dte.period or datetime.now().strftime("%Y-%m")),
                }
            )

        period = (dte.period or datetime.now().strftime("%Y-%m")).strip()

        ref_rows = (
            self.db.query(DteReferenceModel)
            .filter(DteReferenceModel.dte_id == dte.id)
            .order_by(DteReferenceModel.id.asc())
            .all()
        )
        references = []
        for r in ref_rows:
            type_id = (r.reference_type_id or "").strip() or None
            date_id = (r.reference_date_id or "").strip() or None
            code = (r.reference_code or "").strip() or None
            desc = (r.reference_description or "").strip() or None
            if not any([type_id, date_id, code, desc]):
                continue
            references.append(
                {
                    "reference_type_id": type_id,
                    "reference_date_id": date_id,
                    "reference_code": code,
                    "reference_description": desc,
                }
            )

        return {
            "status": "success",
            "data": {
                "source_dte_id": dte.id,
                "source_folio": dte.folio,
                "source_dte_type_id": dte.dte_type_id,
                "branch_office_id": dte.branch_office_id,
                "rut": str(dte.rut).strip() if dte.rut else None,
                "customer": (customer.customer if customer else None),
                "email": (customer.email if customer else None),
                "phone": (customer.phone if customer else None),
                "activity": (customer.activity if customer else None),
                "address": (customer.address if customer else None),
                "region_id": (customer.region_id if customer else None),
                "commune_id": (customer.commune_id if customer else None),
                "period": period,
                "renew_mode": RENEW_FIXED,
                "send_email": 1,
                "send_whatsapp": 0,
                "chip_id": int(dte.chip_id or 0),
                "items": items,
                "references": references,
            },
        }

    def store(self, form_data) -> dict:
        items = self._normalize_items(getattr(form_data, "items", []) or [])
        if not items:
            return {"status": "error", "message": "La cotización requiere al menos una línea"}
        period = (getattr(form_data, "period", None) or datetime.now().strftime("%Y-%m")).strip()
        chip_id = int(getattr(form_data, "chip_id", 0) or 0)
        # Mes a mes: detalle de mes en description si viene vacío o genérico
        period_label = HelperClass.period_detail_label(period)
        for it in items:
            desc = (it.get("description") or "").strip()
            if not desc or desc == "-":
                it["description"] = period_label
                if not it.get("dsc_item"):
                    it["dsc_item"] = period_label

        subtotal, tax, total = self._compute_totals(items, chip_id=0)
        now = datetime.now()
        row = QuotationModel(
            quotation_number=self._next_quotation_number(),
            branch_office_id=int(form_data.branch_office_id),
            rut=str(form_data.rut).strip(),
            customer=self._clean_str(getattr(form_data, "customer", None)),
            email=self._clean_str(getattr(form_data, "email", None)),
            phone=self._clean_str(getattr(form_data, "phone", None)),
            activity=self._clean_str(getattr(form_data, "activity", None)),
            address=self._clean_str(getattr(form_data, "address", None)),
            region_id=getattr(form_data, "region_id", None),
            commune_id=getattr(form_data, "commune_id", None),
            period=period,
            renew_mode=int(getattr(form_data, "renew_mode", RENEW_FIXED) or RENEW_FIXED),
            send_email=1 if int(getattr(form_data, "send_email", 1) or 0) else 0,
            send_whatsapp=1 if int(getattr(form_data, "send_whatsapp", 0) or 0) else 0,
            status_id=STATUS_DRAFT,
            chip_id=chip_id,
            subtotal=subtotal,
            tax=tax,
            total=total,
            added_date=now,
            updated_date=now,
        )
        try:
            self.db.add(row)
            self.db.flush()
            self._replace_items(row.id, items)
            refs = self._normalize_references(getattr(form_data, "references", []) or [])
            self._replace_references(row.id, refs)
            self.db.commit()
            self.db.refresh(row)
            return {
                "status": "success",
                "message": "Cotización guardada",
                "id": row.id,
                "quotation_number": row.quotation_number,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def update(self, quotation_id: int, form_data) -> dict:
        row = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not row or row.status_id == STATUS_ANNULLED:
            return {"status": "error", "message": "Cotización no encontrada"}
        if row.status_id == STATUS_CONVERTED:
            return {"status": "error", "message": "Cotización ya convertida; no se puede editar"}

        items = self._normalize_items(getattr(form_data, "items", []) or [])
        if not items:
            return {"status": "error", "message": "La cotización requiere al menos una línea"}

        period = (getattr(form_data, "period", None) or row.period or "").strip()
        chip_id = int(getattr(form_data, "chip_id", row.chip_id) or 0)
        subtotal, tax, total = self._compute_totals(items, chip_id=0)

        row.branch_office_id = int(form_data.branch_office_id)
        row.rut = str(form_data.rut).strip()
        row.customer = self._clean_str(getattr(form_data, "customer", None))
        row.email = self._clean_str(getattr(form_data, "email", None))
        row.phone = self._clean_str(getattr(form_data, "phone", None))
        row.activity = self._clean_str(getattr(form_data, "activity", None))
        row.address = self._clean_str(getattr(form_data, "address", None))
        row.region_id = getattr(form_data, "region_id", None)
        row.commune_id = getattr(form_data, "commune_id", None)
        row.period = period
        row.renew_mode = int(getattr(form_data, "renew_mode", row.renew_mode) or RENEW_FIXED)
        row.send_email = 1 if int(getattr(form_data, "send_email", row.send_email) or 0) else 0
        row.send_whatsapp = 1 if int(getattr(form_data, "send_whatsapp", row.send_whatsapp) or 0) else 0
        row.chip_id = chip_id
        row.subtotal = subtotal
        row.tax = tax
        row.total = total
        row.updated_date = datetime.now()

        try:
            self._replace_items(row.id, items)
            refs = self._normalize_references(getattr(form_data, "references", []) or [])
            self._replace_references(row.id, refs)
            self.db.commit()
            return {"status": "success", "message": "Cotización actualizada", "id": row.id}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def annul(self, quotation_id: int) -> dict:
        row = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not row:
            return {"status": "error", "message": "Cotización no encontrada"}
        if row.status_id == STATUS_CONVERTED:
            return {"status": "error", "message": "No se puede anular una cotización convertida"}
        row.status_id = STATUS_ANNULLED
        row.updated_date = datetime.now()
        try:
            self.db.commit()
            return {"status": "success", "message": "Cotización anulada"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------ PDF
    def build_pdf_bytes(self, quotation_id: int) -> tuple[Optional[bytes], Optional[str]]:
        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q:
            return None, "Cotización no encontrada"
        items = (
            self.db.query(QuotationItemModel)
            .filter(QuotationItemModel.quotation_id == q.id)
            .order_by(QuotationItemModel.line_number)
            .all()
        )
        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == q.branch_office_id)
            .first()
        )
        contact = self._branch_contact(branch)
        branch_name = (getattr(branch, "branch_office", None) or "—") if branch else "—"
        branch_address = (getattr(branch, "address", None) or "").strip() if branch else ""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.1 * cm,
            bottomMargin=1.2 * cm,
        )
        styles = getSampleStyleSheet()
        company = ParagraphStyle(
            "q_company",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.HexColor(JIS_PRIMARY),
            alignment=TA_LEFT,
            spaceAfter=3,
            leading=17,
        )
        giro_style = ParagraphStyle(
            "q_giro",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.black,
        )
        tiny = ParagraphStyle(
            "q_tiny",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.black,
        )
        tiny_b = ParagraphStyle(
            "q_tiny_b",
            parent=tiny,
            fontName="Helvetica-Bold",
        )
        small = ParagraphStyle(
            "q_small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        )
        small_b = ParagraphStyle("q_small_b", parent=small, fontName="Helvetica-Bold")
        label = ParagraphStyle(
            "q_label",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
        )
        right = ParagraphStyle(
            "q_right",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            alignment=TA_RIGHT,
            leading=11,
        )
        center = ParagraphStyle(
            "q_center",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            alignment=TA_CENTER,
            leading=13,
        )
        center_rut = ParagraphStyle(
            "q_center_rut",
            parent=center,
            fontSize=11,
            textColor=colors.HexColor("#c62828"),
            leading=14,
        )
        center_title = ParagraphStyle(
            "q_center_title",
            parent=center,
            fontSize=12,
            textColor=colors.black,
            leading=15,
        )
        item_main = ParagraphStyle(
            "q_item_main",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
        )
        item_sub = ParagraphStyle(
            "q_item_sub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#333333"),
        )

        story = []
        usable_w = letter[0] - doc.leftMargin - doc.rightMargin

        # ----- Header: logo + emisor | caja RUT/COTIZACIÓN/N° -----
        logo_cell = self._logo_flowable(2.35, 2.35)
        issuer_lines = [
            Paragraph(html.escape(ISSUER_NAME), company),
            Paragraph(html.escape(ISSUER_GIRO), giro_style),
            Paragraph(html.escape(branch_address or "—"), tiny),
            Paragraph(f"Sucursal: {html.escape(str(branch_name))}", tiny),
            Paragraph(html.escape(ISSUER_HQ), tiny),
            Paragraph(
                f"<b>{html.escape(ISSUER_PHONE)} / {html.escape(ISSUER_EMAIL)}</b>",
                tiny,
            ),
        ]
        header_left = Table(
            [[logo_cell, issuer_lines]],
            colWidths=[2.55 * cm, usable_w - 2.55 * cm - 6.1 * cm],
        )
        header_left.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ("RIGHTPADDING", (1, 0), (1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        box_data = [
            [Paragraph(f"R.U.T.: {html.escape(ISSUER_RUT)}", center_rut)],
            [Paragraph("COTIZACIÓN", center_title)],
            [Paragraph(f"N° {html.escape(q.quotation_number or '')}", center)],
        ]
        box = Table(box_data, colWidths=[6.0 * cm])
        box.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.6, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        top = Table(
            [[header_left, box]],
            colWidths=[usable_w - 6.1 * cm, 6.1 * cm],
        )
        top.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )
        story.append(top)
        story.append(Spacer(1, 14))

        # ----- Cliente (izq) + meta (der), como en la foto -----
        phone_show = (q.phone or "").strip()
        email_show = (q.email or "").strip()
        contacto_cliente = " / ".join([p for p in [phone_show, email_show] if p]) or "—"
        period_label = HelperClass.period_detail_label(q.period or "") or (q.period or "—")
        fecha_larga = self._format_date_long(q.added_date)

        receptor_rows = [
            [Paragraph("R.U.T.", label), Paragraph(html.escape(q.rut or "—"), small)],
            [Paragraph("Razón social", label), Paragraph(html.escape(q.customer or "—"), small)],
            [Paragraph("Giro", label), Paragraph(html.escape(q.activity or "—"), small)],
            [Paragraph("Dirección", label), Paragraph(html.escape(q.address or "—"), small)],
            [Paragraph("Contacto", label), Paragraph(html.escape(contacto_cliente), small)],
            [Paragraph("Período", label), Paragraph(html.escape(period_label), small)],
        ]
        rec_table = Table(receptor_rows, colWidths=[2.6 * cm, 8.2 * cm])
        rec_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        meta_rows = [
            [Paragraph(html.escape(fecha_larga), right)],
            [Paragraph("Venta: crédito", right)],
            [Paragraph(f"Vendedor: {html.escape(contact['email'])}", right)],
        ]
        meta_table = Table(meta_rows, colWidths=[7.0 * cm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        mid = Table([[rec_table, meta_table]], colWidths=[10.9 * cm, 7.0 * cm])
        mid.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(mid)
        story.append(Spacer(1, 14))

        # ----- Tabla de ítems -----
        th = ParagraphStyle("q_th", parent=small_b, alignment=TA_CENTER)
        th_left = ParagraphStyle("q_th_l", parent=small_b, alignment=TA_LEFT)
        rows = [
            [
                Paragraph("Item", th_left),
                Paragraph("Cant.", th),
                Paragraph("Unidad", th),
                Paragraph("P. unitario", th),
                Paragraph("Total item", th),
            ]
        ]
        for it in items:
            main_txt = (it.description or it.dsc_item or it.item_name or "—").strip()
            sub_txt = (it.item_name or "").strip()
            if sub_txt and sub_txt.lower() == main_txt.lower():
                sub_txt = ""
            if not (it.description or it.dsc_item) and sub_txt:
                # Si solo hay nombre, úsalo como línea principal
                main_txt = sub_txt
                sub_txt = ""
            parts = [Paragraph(html.escape(main_txt), item_main)]
            if sub_txt:
                parts.append(Paragraph(html.escape(sub_txt), item_sub))
            item_cell = parts if len(parts) > 1 else parts[0]
            if isinstance(item_cell, list):
                item_inner = Table([[p] for p in parts], colWidths=[8.0 * cm])
                item_inner.setStyle(
                    TableStyle(
                        [
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ]
                    )
                )
                item_cell = item_inner
            rows.append(
                [
                    item_cell,
                    Paragraph(str(it.quantity or 0), ParagraphStyle("qc", parent=small, alignment=TA_CENTER)),
                    Paragraph(
                        html.escape(str(it.unit_measure or "1")),
                        ParagraphStyle("qu", parent=small, alignment=TA_CENTER),
                    ),
                    Paragraph(self._format_clp_plain(it.unit_amount or 0), right),
                    Paragraph(self._format_clp_plain(it.total_amount or 0), right),
                ]
            )

        items_table = Table(
            rows,
            colWidths=[8.0 * cm, 1.7 * cm, 2.0 * cm, 2.9 * cm, 3.2 * cm],
            repeatRows=1,
        )
        items_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("ALIGN", (1, 0), (2, -1), "CENTER"),
                    ("ALIGN", (3, 0), (4, -1), "RIGHT"),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 12))

        # ----- Totales (alineados a la derecha, limpios) -----
        totals = [
            [Paragraph("Neto", small_b), Paragraph(self._format_clp(q.subtotal or 0), right)],
            [Paragraph("IVA 19%", small_b), Paragraph(self._format_clp(q.tax or 0), right)],
            [
                Paragraph("Total", ParagraphStyle("q_tot_l", parent=small_b, fontSize=10)),
                Paragraph(
                    f"<b>{self._format_clp(q.total or 0)}</b>",
                    ParagraphStyle("q_tot_r", parent=right, fontSize=10, fontName="Helvetica-Bold"),
                ),
            ],
        ]
        tot_table = Table(totals, colWidths=[3.2 * cm, 3.6 * cm], hAlign="RIGHT")
        tot_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
                    ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f5f5f5")),
                ]
            )
        )
        story.append(tot_table)
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Documento informativo. No constituye boleta ni factura electrónica ante el SII.",
                ParagraphStyle(
                    "q_note",
                    parent=tiny,
                    textColor=colors.HexColor("#666666"),
                    fontSize=7.5,
                ),
            )
        )
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                f"Contacto comercial: {html.escape(contact['name'])} · "
                f"{html.escape(contact['phone'])} · {html.escape(contact['email'])}",
                tiny,
            )
        )

        try:
            doc.build(story)
            return buffer.getvalue(), None
        except Exception as e:
            return None, str(e)

    def save_pdf_public(self, quotation_id: int) -> dict:
        """Genera PDF y lo publica en /files para WhatsApp (link público)."""
        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q:
            return {"status": "error", "message": "Cotización no encontrada"}
        pdf_bytes, pdf_err = self.build_pdf_bytes(quotation_id)
        if not pdf_bytes:
            return {"status": "error", "message": pdf_err or "No se pudo generar el PDF"}

        safe_number = re.sub(r"[^A-Za-z0-9_-]+", "-", q.quotation_number or str(quotation_id))
        remote_path = f"quotations/{safe_number}.pdf"
        try:
            fc = FileClass(self.db)
            fc.temporal_upload(pdf_bytes, remote_path)
            return {
                "status": "success",
                "url": fc.get(remote_path),
                "filename": f"{safe_number}.pdf",
                "path": remote_path,
            }
        except Exception as e:
            return {"status": "error", "message": f"No se pudo publicar el PDF: {e}"}

    # ------------------------------------------------------------------ send
    def _smtp_settings(self) -> dict[str, Any]:
        password = (os.getenv("DTE_EMAIL_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
        return {
            "server": (os.getenv("DTE_EMAIL_SMTP_SERVER") or "smtp.gmail.com").strip(),
            "port": int(os.getenv("DTE_EMAIL_SMTP_PORT") or "465"),
            "user": (os.getenv("DTE_EMAIL_SMTP_USER") or "contacto@jisparking.com").strip(),
            "password": password,
            "from_name": (os.getenv("DTE_EMAIL_FROM_NAME") or "JIS Parking").strip(),
        }

    def send_email(self, quotation_id: int, to_email: Optional[str] = None) -> dict:
        from email.mime.image import MIMEImage
        from app.backend.classes.dte_subscriber_email_class import (
            LOGO_CID,
            _build_quotation_html_body,
            _load_brand_logo_bytes,
        )

        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q or q.status_id == STATUS_ANNULLED:
            return {"status": "error", "message": "Cotización no encontrada"}

        recipients = []
        if to_email:
            recipients = [e.strip() for e in str(to_email).replace(";", ",").split(",") if "@" in e]
        if not recipients and q.email:
            recipients = [e.strip() for e in str(q.email).replace(";", ",").split(",") if "@" in e]
        if not recipients:
            cust = self.db.query(CustomerModel).filter(CustomerModel.rut == q.rut).first()
            if cust and cust.email:
                recipients = [e.strip() for e in str(cust.email).replace(";", ",").split(",") if "@" in e]
        if not recipients:
            return {"status": "skipped", "message": "Sin correo destinatario"}

        smtp = self._smtp_settings()
        if not smtp["password"]:
            return {
                "status": "error",
                "message": "SMTP no configurado (DTE_EMAIL_SMTP_PASSWORD o SMTP_PASSWORD)",
            }

        pdf_bytes, pdf_err = self.build_pdf_bytes(quotation_id)
        if not pdf_bytes:
            return {"status": "error", "message": pdf_err or "No se pudo generar el PDF"}

        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == q.branch_office_id)
            .first()
        )
        contact = self._branch_contact(branch)
        logo_bytes = _load_brand_logo_bytes()
        # Tracking pixel: new token on each send; reset read flag
        token = secrets.token_urlsafe(24)
        q.email_read_token = token
        q.email_read = 0
        q.email_read_at = None
        public_base = os.getenv(
            "PUBLIC_API_BASE_URL",
            "https://intrajisbackend.com/api",
        ).rstrip("/")
        tracking_pixel_url = f"{public_base}/quotations/email_open/{token}.gif"

        subject = f"JIS Parking - Cotización {q.quotation_number}"
        html_body = _build_quotation_html_body(
            customer_name=q.customer or "Cliente",
            quotation_number=q.quotation_number or str(quotation_id),
            issue_date=self._format_date_short(q.added_date),
            period_label=HelperClass.period_detail_label(q.period or ""),
            total_clp=self._format_clp(q.total or 0),
            contact_name=contact["name"],
            contact_phone=contact["phone"],
            contact_email=contact["email"],
            has_logo=bool(logo_bytes),
            tracking_pixel_url=tracking_pixel_url,
        )

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{smtp['from_name']} <{smtp['user']}>"
        msg["To"] = ", ".join(recipients)

        related = MIMEMultipart("related")
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html", "utf-8"))
        related.attach(alt)
        if logo_bytes:
            logo_part = MIMEImage(logo_bytes, _subtype="png")
            logo_part.add_header("Content-ID", f"<{LOGO_CID}>")
            logo_part.add_header("Content-Disposition", "inline", filename="jisparking-logo.png")
            related.attach(logo_part)
        msg.attach(related)

        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"{q.quotation_number or 'quotation'}.pdf",
        )
        msg.attach(part)

        try:
            with smtplib.SMTP_SSL(smtp["server"], smtp["port"], timeout=30) as server:
                server.login(smtp["user"], smtp["password"])
                server.sendmail(smtp["user"], recipients, msg.as_string())
            q.last_sent_at = datetime.now()
            q.last_sent_channel = "email"
            if q.status_id == STATUS_DRAFT:
                q.status_id = STATUS_SENT
            q.updated_date = datetime.now()
            self.db.commit()
            return {"status": "success", "message": "Correo enviado", "to": recipients}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error SMTP: {e}"}

    def mark_email_read(self, token: str) -> bool:
        """Marca email_read=1 cuando el cliente abre el correo (píxel)."""
        token = (token or "").strip()
        if token.endswith(".gif"):
            token = token[:-4]
        if not token:
            return False
        q = (
            self.db.query(QuotationModel)
            .filter(QuotationModel.email_read_token == token)
            .first()
        )
        if not q:
            return False
        if int(getattr(q, "email_read", 0) or 0) != 1:
            q.email_read = 1
            q.email_read_at = datetime.now()
            q.updated_date = datetime.now()
            self.db.commit()
        return True

    def send_whatsapp(self, quotation_id: int, phone: Optional[str] = None) -> dict:
        """
        Dispara plantilla Meta `quotation` (header documento PDF + body {{1}}..{{6}}).

        Plantilla:
          Cotización N° {{1}}, del día {{2}} por un monto total de {{3}}...
          contactar a: {{4}} 📞 {{5}} o al email 📧 {{6}}.
        """
        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q or q.status_id == STATUS_ANNULLED:
            return {"status": "error", "message": "Cotización no encontrada"}

        phone_raw = phone or q.phone
        if not phone_raw:
            cust = self.db.query(CustomerModel).filter(CustomerModel.rut == q.rut).first()
            phone_raw = cust.phone if cust else None
        if not phone_raw or not str(phone_raw).strip():
            return {"status": "skipped", "message": "Sin teléfono destinatario"}

        digits = re.sub(r"\D", "", str(phone_raw))
        if digits.startswith("569") and len(digits) >= 11:
            wa_to = digits
        elif digits.startswith("9") and len(digits) == 9:
            wa_to = "56" + digits
        elif digits.startswith("56"):
            wa_to = digits
        else:
            wa_to = "56" + digits

        token = whatsapp_access_token()
        if not token:
            return {"status": "error", "message": "WHATSAPP_ACCESS_TOKEN no configurado"}

        whatsapp_template = _whatsapp_template_quotation(self.db)
        if not whatsapp_template or not whatsapp_template.title:
            return {
                "status": "error",
                "message": (
                    f"Plantilla WhatsApp '{WHATSAPP_TEMPLATE_QUOTATION_TITLE}' no encontrada en "
                    "whatsapp_templates. Ejecuta tools/sql/seed_whatsapp_template_quotation.sql"
                ),
            }
        template_name = whatsapp_template.title

        pdf_pub = self.save_pdf_public(quotation_id)
        if pdf_pub.get("status") != "success" or not pdf_pub.get("url"):
            return {
                "status": "error",
                "message": pdf_pub.get("message") or "PDF no disponible para WhatsApp",
                "pdf": pdf_pub,
            }

        branch = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == q.branch_office_id)
            .first()
        )
        contact = self._branch_contact(branch)

        var1 = str(q.quotation_number or quotation_id)
        var2 = self._format_date_short(q.added_date)
        var3 = self._format_clp(q.total or 0)
        var4 = contact["name"] or "JIS Parking"
        var5 = contact["phone"] or "226825312"
        var6 = contact["email"] or ISSUER_EMAIL

        # Meta rechaza parámetros vacíos
        body_params = [
            {"type": "text", "text": v if str(v).strip() else "-"}
            for v in (var1, var2, var3, var4, var5, var6)
        ]

        payload = {
            "messaging_product": "whatsapp",
            "to": wa_to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": pdf_pub["url"],
                                    "filename": pdf_pub.get("filename") or f"{var1}.pdf",
                                },
                            }
                        ],
                    },
                    {"type": "body", "parameters": body_params},
                ],
            },
        }

        try:
            resp = requests.post(
                whatsapp_graph_messages_url(),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                err = (data.get("error") or {}) if isinstance(data, dict) else {}
                return {
                    "status": "error",
                    "message": err.get("message") or "Error WhatsApp",
                    "response": data,
                    "payload_preview": {
                        "to": wa_to,
                        "template": template_name,
                        "vars": [var1, var2, var3, var4, var5, var6],
                        "pdf": pdf_pub.get("url"),
                    },
                }
            q.last_sent_at = datetime.now()
            q.last_sent_channel = "whatsapp"
            if q.status_id == STATUS_DRAFT:
                q.status_id = STATUS_SENT
            q.updated_date = datetime.now()
            self.db.commit()
            return {
                "status": "success",
                "message": "WhatsApp enviado",
                "to": wa_to,
                "template": template_name,
                "pdf": pdf_pub.get("url"),
                "response": data,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    # ------------------------------------------------------------------ renew / convert
    def renew_period(self, period: str) -> dict:
        """Clona cotizaciones mes a mes (renew_mode=2) del período anterior al nuevo."""
        current_period = HelperClass.fix_current_dte_period(period)
        last_period = HelperClass.fix_last_dte_period(period)
        period_detail = HelperClass.period_detail_label(current_period)

        sources = (
            self.db.query(QuotationModel)
            .filter(QuotationModel.period == last_period)
            .filter(QuotationModel.renew_mode == RENEW_MONTHLY)
            .filter(QuotationModel.status_id.in_([STATUS_DRAFT, STATUS_SENT, STATUS_CONVERTED]))
            .all()
        )
        if not sources:
            return {"status": "success", "message": "No data found", "created": 0}

        # Evitar duplicados si ya existen para el período nuevo
        existing_keys = {
            (r.rut, r.branch_office_id)
            for r in self.db.query(QuotationModel)
            .filter(QuotationModel.period == current_period)
            .filter(QuotationModel.renew_mode == RENEW_MONTHLY)
            .filter(QuotationModel.status_id != STATUS_ANNULLED)
            .all()
        }

        created = 0
        try:
            for src in sources:
                key = (src.rut, src.branch_office_id)
                if key in existing_keys:
                    continue
                items = (
                    self.db.query(QuotationItemModel)
                    .filter(QuotationItemModel.quotation_id == src.id)
                    .order_by(QuotationItemModel.line_number)
                    .all()
                )
                now = datetime.now()
                clone = QuotationModel(
                    quotation_number=self._next_quotation_number(),
                    branch_office_id=src.branch_office_id,
                    rut=src.rut,
                    customer=src.customer,
                    email=src.email,
                    phone=src.phone,
                    activity=src.activity,
                    address=src.address,
                    region_id=src.region_id,
                    commune_id=src.commune_id,
                    period=current_period,
                    renew_mode=RENEW_MONTHLY,
                    send_email=int(getattr(src, "send_email", 1) or 0),
                    send_whatsapp=int(getattr(src, "send_whatsapp", 0) or 0),
                    status_id=STATUS_DRAFT,
                    chip_id=0,
                    subtotal=src.subtotal,
                    tax=src.tax,
                    total=src.total,
                    source_quotation_id=src.id,
                    added_date=now,
                    updated_date=now,
                )
                self.db.add(clone)
                self.db.flush()
                for it in items:
                    self.db.add(
                        QuotationItemModel(
                            quotation_id=clone.id,
                            line_number=it.line_number,
                            quantity=it.quantity,
                            unit_amount=it.unit_amount,
                            total_amount=it.total_amount,
                            description=period_detail,
                            dsc_item=period_detail,
                            item_code=it.item_code,
                            item_name=it.item_name,
                            unit_measure=it.unit_measure,
                            discount_amount=it.discount_amount or 0,
                            status_id=1,
                            added_date=now,
                            updated_date=now,
                        )
                    )
                for ref in self._load_references(src.id):
                    self.db.add(
                        QuotationReferenceModel(
                            quotation_id=clone.id,
                            reference_type_id=ref.get("reference_type_id"),
                            reference_date_id=ref.get("reference_date_id"),
                            reference_code=ref.get("reference_code"),
                            reference_description=ref.get("reference_description"),
                            added_date=now,
                        )
                    )
                existing_keys.add(key)
                created += 1
            self.db.commit()
            return {
                "status": "success",
                "message": f"Renovadas {created} cotizaciones",
                "created": created,
                "period": current_period,
                "from_period": last_period,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}

    def convert_to_dte(self, quotation_id: int, dte_type_id: int, rol_id: int = 1) -> dict:
        """Crea borrador V2 (boleta 39 / factura 33) desde la cotización."""
        if int(dte_type_id) not in (33, 39):
            return {"status": "error", "message": "dte_type_id debe ser 33 o 39"}

        q = self.db.query(QuotationModel).filter(QuotationModel.id == quotation_id).first()
        if not q or q.status_id == STATUS_ANNULLED:
            return {"status": "error", "message": "Cotización no encontrada"}
        if q.status_id == STATUS_CONVERTED and q.converted_dte_id:
            return {
                "status": "error",
                "message": "Cotización ya convertida",
                "dte_id": q.converted_dte_id,
            }

        items = (
            self.db.query(QuotationItemModel)
            .filter(QuotationItemModel.quotation_id == q.id)
            .order_by(QuotationItemModel.line_number)
            .all()
        )
        if not items:
            return {"status": "error", "message": "Cotización sin líneas"}

        status_id = 2 if int(rol_id) in (1, 2) else 1
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        q_refs = self._load_references(q.id)
        # 2 = con referencias (como factura), 3 = solo detalle grupal
        category_id = 2 if q_refs else 3
        dte = DteModel(
            branch_office_id=q.branch_office_id,
            cashier_id=0,
            dte_type_id=int(dte_type_id),
            dte_version_id=DTE_VERSION_V2,
            status_id=status_id,
            rut=q.rut,
            folio=0,
            chip_id=int(q.chip_id or 0),
            category_id=category_id,
            payment_term_id=1,
            cash_amount=int(q.total or 0),
            card_amount=0,
            subtotal=int(q.subtotal or 0),
            tax=int(q.tax or 0),
            discount=0,
            total=int(q.total or 0),
            period=q.period,
            quantity=sum(int(i.quantity or 0) for i in items),
            expense_type_id=25,
            added_date=now,
            updated_date=datetime.now(),
        )
        try:
            self.db.add(dte)
            self.db.flush()
            for it in items:
                self.db.add(
                    CustomerDteItemModel(
                        dte_id=dte.id,
                        line_number=it.line_number,
                        quantity=it.quantity,
                        unit_amount=it.unit_amount,
                        total_amount=it.total_amount,
                        description=it.description or "-",
                        item_code=it.item_code,
                        item_name=it.item_name,
                        unit_measure=it.unit_measure,
                        discount_amount=int(it.discount_amount or 0),
                        dsc_item=it.dsc_item,
                        status_id=1,
                        added_date=datetime.now(),
                        updated_date=datetime.now(),
                    )
                )
            for ref in q_refs:
                self.db.add(
                    DteReferenceModel(
                        dte_id=dte.id,
                        reference_type_id=ref.get("reference_type_id"),
                        reference_date_id=ref.get("reference_date_id"),
                        reference_code=ref.get("reference_code"),
                        reference_description=ref.get("reference_description"),
                        added_date=datetime.now(),
                    )
                )
            q.converted_dte_id = dte.id
            q.status_id = STATUS_CONVERTED
            q.updated_date = datetime.now()
            self.db.commit()
            self.db.refresh(dte)

            edit_path = (
                f"/customer_bill_v2/edit/{dte.id}"
                if int(dte_type_id) == 33
                else f"/customer_ticket_v2/edit/{dte.id}"
            )
            return {
                "status": "success",
                "message": "Borrador V2 creado",
                "dte_id": dte.id,
                "dte_type_id": int(dte_type_id),
                "redirect": edit_path,
            }
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
