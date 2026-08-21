"""Cotizaciones de abonados (no DTE SII)."""

from __future__ import annotations

import html
import io
import os
import re
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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.backend.classes.helper_class import HelperClass
from app.backend.classes.whatsapp_class import (
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
)

DTE_VERSION_V2 = 2
STATUS_DRAFT = 1
STATUS_SENT = 2
STATUS_CONVERTED = 3
STATUS_ANNULLED = 4
RENEW_FIXED = 1
RENEW_MONTHLY = 2
JIS_PRIMARY = "#152d8a"


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
            return "0"
        return f"${n:,.0f}".replace(",", ".")

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

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm,
        )
        styles = getSampleStyleSheet()
        title = ParagraphStyle(
            "q_title",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=colors.HexColor(JIS_PRIMARY),
            alignment=TA_LEFT,
            spaceAfter=4,
        )
        small = ParagraphStyle("q_small", parent=styles["Normal"], fontSize=9, leading=12)
        right = ParagraphStyle("q_right", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT)
        center = ParagraphStyle("q_center", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER)

        story = []
        issuer_name = "JIS Parking SpA"
        issuer_rut = "76.XXX.XXX-X"
        if branch:
            issuer_name = getattr(branch, "branch_office", None) or issuer_name

        header_left = [
            Paragraph(f"<b>{html.escape(issuer_name)}</b>", title),
            Paragraph("Cotización comercial (no es documento tributario SII)", small),
        ]
        box_data = [
            [Paragraph("<b>RUT</b>", center)],
            [Paragraph(html.escape(issuer_rut), center)],
            [Paragraph("<b>COTIZACIÓN</b>", center)],
            [Paragraph(f"<b>N° {html.escape(q.quotation_number or '')}</b>", center)],
        ]
        box = Table(box_data, colWidths=[5.5 * cm])
        box.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor(JIS_PRIMARY)),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(JIS_PRIMARY)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor(JIS_PRIMARY)),
                    ("TEXTCOLOR", (0, 2), (-1, 2), colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        top = Table([[header_left, box]], colWidths=[11 * cm, 6 * cm])
        top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(top)
        story.append(Spacer(1, 10))

        fecha = q.added_date.strftime("%d-%m-%Y") if q.added_date else datetime.now().strftime("%d-%m-%Y")
        receptor = [
            [Paragraph("<b>Señor(es)</b>", small), Paragraph(html.escape(q.customer or ""), small)],
            [Paragraph("<b>RUT</b>", small), Paragraph(html.escape(q.rut or ""), small)],
            [Paragraph("<b>Giro</b>", small), Paragraph(html.escape(q.activity or ""), small)],
            [Paragraph("<b>Dirección</b>", small), Paragraph(html.escape(q.address or ""), small)],
            [Paragraph("<b>Período</b>", small), Paragraph(html.escape(HelperClass.period_detail_label(q.period or "")), small)],
            [Paragraph("<b>Fecha</b>", small), Paragraph(fecha, small)],
        ]
        rec_table = Table(receptor, colWidths=[3 * cm, 14 * cm])
        rec_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(rec_table)
        story.append(Spacer(1, 12))

        rows = [
            [
                Paragraph("<b>#</b>", center),
                Paragraph("<b>Nombre</b>", small),
                Paragraph("<b>Detalle</b>", small),
                Paragraph("<b>Cant.</b>", center),
                Paragraph("<b>P. Unit.</b>", right),
                Paragraph("<b>Total</b>", right),
            ]
        ]
        for it in items:
            rows.append(
                [
                    Paragraph(str(it.line_number), center),
                    Paragraph(html.escape(it.item_name or "-"), small),
                    Paragraph(html.escape(it.description or "-"), small),
                    Paragraph(str(it.quantity), center),
                    Paragraph(self._format_clp(it.unit_amount), right),
                    Paragraph(self._format_clp(it.total_amount), right),
                ]
            )
        items_table = Table(rows, colWidths=[1 * cm, 4.5 * cm, 5.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm])
        items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eaf5")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfd6e4")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
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
        tot_table = Table(totals, colWidths=[4 * cm, 3 * cm], hAlign="RIGHT")
        tot_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#e6eaf5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(JIS_PRIMARY)),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tot_table)
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Documento informativo. No constituye boleta ni factura electrónica ante el SII.",
                ParagraphStyle("q_note", parent=small, textColor=colors.gray),
            )
        )

        try:
            doc.build(story)
            return buffer.getvalue(), None
        except Exception as e:
            return None, str(e)

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

        subject = f"JIS Parking - Cotización {q.quotation_number}"
        body = f"""
        <div style="font-family:Arial,sans-serif;color:#1d2630;">
          <h2 style="color:{JIS_PRIMARY};">Cotización {html.escape(q.quotation_number or '')}</h2>
          <p>Estimado(a) {html.escape(q.customer or 'Cliente')},</p>
          <p>Adjuntamos la cotización correspondiente al período
             <b>{html.escape(HelperClass.period_detail_label(q.period or ''))}</b>.</p>
          <p>Total: <b>{html.escape(self._format_clp(q.total or 0))}</b></p>
          <p style="color:#5b6b79;font-size:12px;">Este documento no es un DTE del SII.</p>
        </div>
        """
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{smtp['from_name']} <{smtp['user']}>"
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body, "html", "utf-8"))

        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"{q.quotation_number or 'cotizacion'}.pdf",
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

    def send_whatsapp(self, quotation_id: int, phone: Optional[str] = None) -> dict:
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

        text = (
            f"JIS Parking — Cotización {q.quotation_number}\n"
            f"Cliente: {q.customer or q.rut}\n"
            f"Período: {HelperClass.period_detail_label(q.period or '')}\n"
            f"Total: {self._format_clp(q.total or 0)}\n"
            f"(Documento informativo, no es DTE SII). Se envió también por correo si corresponde."
        )
        payload = {
            "messaging_product": "whatsapp",
            "to": wa_to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        try:
            resp = requests.post(
                whatsapp_graph_messages_url(),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload,
                timeout=30,
            )
            data = resp.json() if resp.content else {}
            if resp.status_code >= 400:
                return {
                    "status": "error",
                    "message": (data.get("error") or {}).get("message") or "Error WhatsApp",
                    "response": data,
                }
            q.last_sent_at = datetime.now()
            q.last_sent_channel = "whatsapp"
            if q.status_id == STATUS_DRAFT:
                q.status_id = STATUS_SENT
            q.updated_date = datetime.now()
            self.db.commit()
            return {"status": "success", "message": "WhatsApp enviado", "to": wa_to, "response": data}
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
