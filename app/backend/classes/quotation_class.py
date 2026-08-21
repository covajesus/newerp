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
    QuotationItemModel,
    QuotationModel,
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
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "logo.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "files", "logo.png"),
            "/var/www/intrajisbackend.com/public_html/files/logo.png",
            "/var/www/intrajisbackend.com/public_html/assets/logo.png",
        ]
        for path in candidates:
            full = os.path.abspath(path)
            if os.path.isfile(full):
                return full
        return None

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
        branch_address = (getattr(branch, "address", None) or "") if branch else ""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=1.4 * cm,
            rightMargin=1.4 * cm,
            topMargin=1.0 * cm,
            bottomMargin=1.2 * cm,
        )
        styles = getSampleStyleSheet()
        company = ParagraphStyle(
            "q_company",
            parent=styles["Heading1"],
            fontSize=13,
            textColor=colors.HexColor(JIS_PRIMARY),
            alignment=TA_LEFT,
            spaceAfter=2,
            leading=16,
        )
        small = ParagraphStyle("q_small", parent=styles["Normal"], fontSize=8.5, leading=11)
        tiny = ParagraphStyle("q_tiny", parent=styles["Normal"], fontSize=7.5, leading=9)
        right = ParagraphStyle("q_right", parent=styles["Normal"], fontSize=8.5, alignment=TA_RIGHT, leading=11)
        center = ParagraphStyle("q_center", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, leading=11)
        center_b = ParagraphStyle(
            "q_center_b",
            parent=styles["Normal"],
            fontSize=11,
            alignment=TA_CENTER,
            leading=13,
            textColor=colors.HexColor(JIS_PRIMARY),
        )

        story = []

        logo_cell: Any = ""
        logo_path = self._logo_path()
        if logo_path:
            try:
                logo_cell = Image(logo_path, width=2.2 * cm, height=2.2 * cm)
            except Exception:
                logo_cell = ""

        issuer_lines = [
            Paragraph(f"<b>{html.escape(ISSUER_NAME)}</b>", company),
            Paragraph(html.escape(ISSUER_GIRO), tiny),
            Paragraph(html.escape(branch_address or ISSUER_HQ), tiny),
            Paragraph(f"Sucursal: {html.escape(str(branch_name))}", tiny),
            Paragraph(html.escape(ISSUER_HQ), tiny),
            Paragraph(f"{html.escape(ISSUER_PHONE)} / {html.escape(ISSUER_EMAIL)}", tiny),
        ]
        header_left = Table([[logo_cell, issuer_lines]], colWidths=[2.4 * cm, 9.2 * cm])
        header_left.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        box_data = [
            [Paragraph(f"<b>R.U.T.: {html.escape(ISSUER_RUT)}</b>", center)],
            [Paragraph("<b>COTIZACIÓN</b>", center_b)],
            [Paragraph(f"<b>N° {html.escape(q.quotation_number or '')}</b>", center)],
        ]
        box = Table(box_data, colWidths=[5.8 * cm])
        box.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.2, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f3f5f9")),
                ]
            )
        )
        top = Table([[header_left, box]], colWidths=[11.6 * cm, 6 * cm])
        top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(top)
        story.append(Spacer(1, 8))

        fecha_larga = self._format_date_long(q.added_date)
        meta = Table(
            [
                [Paragraph(html.escape(fecha_larga), right)],
                [Paragraph("Venta: crédito", right)],
                [Paragraph(f"Vendedor: {html.escape(contact['email'])}", right)],
            ],
            colWidths=[17.6 * cm],
        )
        meta.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "RIGHT")]))
        story.append(meta)
        story.append(Spacer(1, 6))

        phone_show = q.phone or ""
        email_show = q.email or ""
        contacto_cliente = " / ".join([p for p in [phone_show, email_show] if p]) or "—"
        receptor = [
            [Paragraph("<b>R.U.T.</b>", small), Paragraph(html.escape(q.rut or "—"), small)],
            [Paragraph("<b>Razón social</b>", small), Paragraph(html.escape(q.customer or "—"), small)],
            [Paragraph("<b>Giro</b>", small), Paragraph(html.escape(q.activity or "—"), small)],
            [Paragraph("<b>Dirección</b>", small), Paragraph(html.escape(q.address or "—"), small)],
            [Paragraph("<b>Contacto</b>", small), Paragraph(html.escape(contacto_cliente), small)],
            [
                Paragraph("<b>Período</b>", small),
                Paragraph(html.escape(HelperClass.period_detail_label(q.period or "")), small),
            ],
        ]
        rec_table = Table(receptor, colWidths=[3.2 * cm, 14.4 * cm])
        rec_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(rec_table)
        story.append(Spacer(1, 10))

        rows = [
            [
                Paragraph("<b>Item</b>", small),
                Paragraph("<b>Cant.</b>", center),
                Paragraph("<b>Unidad</b>", center),
                Paragraph("<b>P. unitario</b>", right),
                Paragraph("<b>Total item</b>", right),
            ]
        ]
        for it in items:
            name = html.escape(it.item_name or "—")
            detail = html.escape(it.description or "")
            item_html = f"<b>{name}</b>"
            if detail and detail != name:
                item_html += f"<br/><font size='7'>{detail}</font>"
            rows.append(
                [
                    Paragraph(item_html, small),
                    Paragraph(str(it.quantity or 0), center),
                    Paragraph(html.escape(it.unit_measure or "1"), center),
                    Paragraph(self._format_clp_plain(it.unit_amount or 0), right),
                    Paragraph(self._format_clp_plain(it.total_amount or 0), right),
                ]
            )
        items_table = Table(rows, colWidths=[8.2 * cm, 1.8 * cm, 2.0 * cm, 2.8 * cm, 2.8 * cm])
        items_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(items_table)
        story.append(Spacer(1, 10))

        totals = [
            [Paragraph("<b>Neto</b>", right), Paragraph(self._format_clp(q.subtotal or 0), right)],
            [Paragraph("<b>IVA 19%</b>", right), Paragraph(self._format_clp(q.tax or 0), right)],
            [Paragraph("<b>Total</b>", right), Paragraph(f"<b>{self._format_clp(q.total or 0)}</b>", right)],
        ]
        tot_table = Table(totals, colWidths=[3.5 * cm, 3.2 * cm], hAlign="RIGHT")
        tot_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.black),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#e6eaf5")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(tot_table)
        story.append(Spacer(1, 14))
        story.append(
            Paragraph(
                "Documento informativo. No constituye boleta ni factura electrónica ante el SII.",
                ParagraphStyle("q_note", parent=tiny, textColor=colors.gray),
            )
        )
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
        dte = DteModel(
            branch_office_id=q.branch_office_id,
            cashier_id=0,
            dte_type_id=int(dte_type_id),
            dte_version_id=DTE_VERSION_V2,
            status_id=status_id,
            rut=q.rut,
            folio=0,
            chip_id=int(q.chip_id or 0),
            category_id=3,
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
