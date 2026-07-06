"""
Correo HTML propio para abonados v2 (SimpleFactura): PDF adjunto + enlace Klap.
Reemplaza POST /dte/enviar/mail de SimpleFactura.
"""

from __future__ import annotations

import html
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from sqlalchemy.orm import Session

from app.backend.classes.customer_ticket_class import (
    DTE_VERSION_V2,
    CustomerTicketClass,
    _is_simplefactura_v2_dte,
)
from app.backend.classes.file_class import FileClass
from app.backend.classes.payments_env import payments_env
from app.backend.db.models import CustomerModel


def is_subscriber_v2_dte(db: Session, dte) -> bool:
    """Boleta/factura emitida vía SimpleFactura invoiceV2 (no LibreDTE v1)."""
    if not dte:
        return False
    dte_type = int(getattr(dte, "dte_type_id", 0) or 0)
    if dte_type == 39:
        return _is_simplefactura_v2_dte(db, dte)
    if dte_type == 33:
        return int(getattr(dte, "dte_version_id", 0) or 0) == DTE_VERSION_V2
    return False


def _format_clp(amount: int) -> str:
    try:
        n = int(amount)
    except (TypeError, ValueError):
        return "0"
    return f"${n:,.0f}".replace(",", ".")


def _normalize_recipients(to_emails) -> list[str]:
    if isinstance(to_emails, str):
        parts = [p.strip() for p in to_emails.replace(";", ",").split(",")]
    elif to_emails:
        parts = [str(e).strip() for e in to_emails]
    else:
        parts = []
    return [e for e in parts if e and "@" in e]


def _smtp_settings() -> dict[str, Any]:
    password = (os.getenv("DTE_EMAIL_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
    return {
        "server": (os.getenv("DTE_EMAIL_SMTP_SERVER") or "smtp.gmail.com").strip(),
        "port": int(os.getenv("DTE_EMAIL_SMTP_PORT") or "465"),
        "user": (os.getenv("DTE_EMAIL_SMTP_USER") or "contacto@jisparking.com").strip(),
        "password": password,
        "from_name": (os.getenv("DTE_EMAIL_FROM_NAME") or "JIS Parking").strip(),
    }


def _dte_label(dte_type_id: int) -> str:
    return "boleta" if int(dte_type_id) == 39 else "factura"


def _build_html_body(
    *,
    customer_name: str,
    dte_label: str,
    folio: int,
    issue_date: str,
    total_clp: str,
    payment_link: str | None,
    is_paid: bool,
) -> str:
    name = html.escape(customer_name or "Cliente")
    label = html.escape(dte_label)
    date_s = html.escape(issue_date)
    total_s = html.escape(total_clp)
    folio_s = html.escape(str(folio))

    if is_paid:
        pay_block = """
          <p style="margin:24px 0 0;padding:14px 18px;background:#e8f5e9;border-radius:8px;color:#2e7d32;font-size:15px;">
            Este documento ya se encuentra <strong>pagado</strong>. El PDF va adjunto a este correo.
          </p>
        """
    elif payment_link:
        link = html.escape(payment_link, quote=True)
        pay_block = f"""
          <p style="margin:28px 0 8px;font-size:15px;color:#333;">
            Puede pagar en línea de forma segura con Klap:
          </p>
          <p style="margin:0 0 20px;text-align:center;">
            <a href="{link}"
               style="display:inline-block;background:#00a651;color:#ffffff;text-decoration:none;
                      padding:14px 32px;border-radius:8px;font-size:16px;font-weight:bold;">
              Pagar ahora
            </a>
          </p>
          <p style="margin:0;font-size:12px;color:#777;word-break:break-all;">
            Si el botón no funciona, copie este enlace en su navegador:<br>
            <a href="{link}" style="color:#1a3a5c;">{link}</a>
          </p>
        """
    else:
        pay_block = """
          <p style="margin:24px 0 0;font-size:14px;color:#666;">
            El PDF del documento va adjunto a este correo.
          </p>
        """

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f0f2f5;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <tr>
            <td style="background:#1a3a5c;padding:28px 32px;">
              <p style="margin:0;font-size:22px;font-weight:bold;color:#ffffff;letter-spacing:0.5px;">JIS Parking</p>
              <p style="margin:6px 0 0;font-size:13px;color:#b8c9dc;">Documento tributario electrónico</p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;font-size:16px;color:#333;">Estimado/a <strong>{name}</strong>,</p>
              <p style="margin:0 0 24px;font-size:15px;color:#444;line-height:1.5;">
                Adjuntamos su {label} electrónica y los datos para su pago.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                     style="background:#f8f9fb;border-radius:8px;border:1px solid #e8eaed;">
                <tr>
                  <td style="padding:16px 20px;font-size:14px;color:#555;">Tipo</td>
                  <td style="padding:16px 20px;font-size:14px;color:#222;text-align:right;text-transform:capitalize;"><strong>{label}</strong></td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:#555;">Folio</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:#222;text-align:right;"><strong>{folio_s}</strong></td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:#555;">Fecha</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:#222;text-align:right;">{date_s}</td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:#555;">Total</td>
                  <td style="padding:0 20px 16px;font-size:18px;color:#1a3a5c;text-align:right;font-weight:bold;">{total_s}</td>
                </tr>
              </table>
              {pay_block}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;background:#f8f9fb;border-top:1px solid #e8eaed;">
              <p style="margin:0;font-size:12px;color:#888;line-height:1.5;">
                JIS Parking SPA · RUT 76.063.822-6<br>
                Este es un correo automático; ante dudas contacte a su sucursal.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


class DteSubscriberEmailClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)

    def _resolve_customer(self, dte, customer):
        if customer is not None:
            return customer
        rut = getattr(dte, "rut", None)
        if not rut:
            return None
        return self.db.query(CustomerModel).filter(CustomerModel.rut == rut).first()

    def _fetch_pdf_bytes(self, dte) -> tuple[bytes | None, str | None]:
        folio = int(getattr(dte, "folio", 0) or 0)
        dte_type = int(getattr(dte, "dte_type_id", 39) or 39)
        if folio <= 0:
            return None, "DTE sin folio"

        remote_path = f"{folio}.pdf"
        try:
            return self.file_class.download(remote_path), None
        except Exception:
            pass

        pdf_result = CustomerTicketClass(self.db).save_simplefactura_pdf_ticket(
            folio,
            dte_type_id=dte_type,
        )
        if pdf_result.get("status") != "success":
            return None, pdf_result.get("message") or "No se pudo obtener el PDF"

        try:
            return self.file_class.download(remote_path), None
        except Exception as exc:
            return None, f"PDF guardado pero no legible: {exc}"

    def _payment_link(self, dte, customer) -> str | None:
        if int(getattr(dte, "status_id", 0) or 0) == 5:
            return None
        folio = int(getattr(dte, "folio", 0) or 0)
        if folio <= 0:
            return None
        proxy_base = payments_env(
            "PAYMENTS_WHATSAPP_PROXY_PUBLIC_BASE",
            default="https://intrajisbackend.com/api/payments/pay",
        ).rstrip("/")
        return f"{proxy_base}/{folio}"

    def send(self, dte, customer=None, to_emails=None) -> dict[str, Any]:
        """
        Envía correo HTML con PDF adjunto y enlace Klap (proxy /api/payments/pay/{folio}).
        """
        if not dte or not getattr(dte, "folio", None):
            return {"status": "error", "message": "DTE sin folio para envío de correo"}

        recipients = _normalize_recipients(to_emails)
        customer = self._resolve_customer(dte, customer)
        if not recipients and customer and getattr(customer, "email", None):
            recipients = _normalize_recipients(customer.email)
        if not recipients:
            return {"status": "skipped", "message": "Sin correo destinatario"}

        smtp = _smtp_settings()
        if not smtp["password"]:
            return {
                "status": "error",
                "message": "SMTP no configurado (DTE_EMAIL_SMTP_PASSWORD o SMTP_PASSWORD)",
            }

        folio = int(dte.folio)
        dte_type = int(getattr(dte, "dte_type_id", 39) or 39)
        dte_label = _dte_label(dte_type)
        customer_name = (getattr(customer, "customer", None) or "Cliente").strip()
        issue_date = (
            dte.added_date.strftime("%d-%m-%Y")
            if getattr(dte, "added_date", None)
            else ""
        )
        total = int(getattr(dte, "total", 0) or 0)
        is_paid = int(getattr(dte, "status_id", 0) or 0) == 5
        payment_link = None if is_paid else self._payment_link(dte, customer)

        pdf_bytes, pdf_err = self._fetch_pdf_bytes(dte)
        if not pdf_bytes:
            return {
                "status": "error",
                "message": pdf_err or "No se pudo adjuntar el PDF",
            }

        subject = f"JIS Parking — {dte_label.capitalize()} electrónica folio {folio}"
        html_body = _build_html_body(
            customer_name=customer_name,
            dte_label=dte_label,
            folio=folio,
            issue_date=issue_date,
            total_clp=_format_clp(total),
            payment_link=payment_link,
            is_paid=is_paid,
        )

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{smtp['from_name']} <{smtp['user']}>"
        msg["To"] = ", ".join(recipients)

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt)

        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"{dte_label}_{folio}.pdf",
        )
        msg.attach(attachment)

        try:
            with smtplib.SMTP_SSL(smtp["server"], smtp["port"]) as server:
                server.login(smtp["user"], smtp["password"])
                server.sendmail(smtp["user"], recipients, msg.as_string())
        except smtplib.SMTPAuthenticationError:
            return {"status": "error", "message": "Error de autenticación SMTP"}
        except smtplib.SMTPException as exc:
            return {"status": "error", "message": f"Error SMTP: {exc}"}
        except Exception as exc:
            return {"status": "error", "message": f"Error al enviar correo: {exc}"}

        print(
            f"[dte-email] sent folio={folio} tipo={dte_type} to={recipients} "
            f"klap={'yes' if payment_link else 'no'}",
            flush=True,
        )
        return {
            "status": "success",
            "message": "Correo enviado",
            "to": recipients,
            "payment_link": payment_link,
            "subject": subject,
        }
