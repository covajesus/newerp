"""
Correo HTML propio para abonados v2 (SimpleFactura):
- Boleta/factura: PDF + enlace Klap (sin mail SimpleFactura).
- Nota de crédito v2: plantilla propia sin pago (sin mail SimpleFactura).
- LibreDTE (v1): reenvío vía API LibreDTE (sin cambios).
"""

from __future__ import annotations

import html
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.backend.classes.customer_ticket_class import (
    DTE_CHIP_AMOUNT_CLP,
    DTE_VERSION_V2,
    CustomerTicketClass,
    _chip_applies,
    _is_simplefactura_v2_dte,
    parking_gross_from_dte,
    ticket_payment_total,
)
from app.backend.classes.file_class import FileClass
from app.backend.classes.payments_env import payments_env
from app.backend.db.models import CustomerModel

# Colores marca JIS Parking (intrajis / vuetify theme)
JIS_PRIMARY = "#152d8a"
JIS_PRIMARY_DARK = "#0f2469"
JIS_PRIMARY_LIGHT = "#e6eaf5"
JIS_WARNING = "#e58a00"
JIS_WARNING_DARK = "#de7700"
JIS_SUCCESS = "#2ca87f"
JIS_SUCCESS_LIGHT = "#e5f4ef"
JIS_TEXT = "#1d2630"
JIS_TEXT_MUTED = "#5b6b79"
JIS_BORDER = "#e8ebee"
JIS_BG = "#f8f9fa"
LOGO_CID = "jisparking-logo"


def is_subscriber_v2_dte(db: Session, dte) -> bool:
    """Boleta/factura/NC emitida vía SimpleFactura v2 (no LibreDTE v1)."""
    if not dte:
        return False
    dte_type = int(getattr(dte, "dte_type_id", 0) or 0)
    if dte_type == 61:
        return int(getattr(dte, "dte_version_id", 0) or 0) == DTE_VERSION_V2
    if dte_type == 39:
        return _is_simplefactura_v2_dte(db, dte)
    if dte_type == 33:
        return int(getattr(dte, "dte_version_id", 0) or 0) == DTE_VERSION_V2
    return False


def is_subscriber_v2_credit_note(dte) -> bool:
    return (
        dte is not None
        and int(getattr(dte, "dte_type_id", 0) or 0) == 61
        and int(getattr(dte, "dte_version_id", 0) or 0) == DTE_VERSION_V2
    )


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
    tid = int(dte_type_id)
    if tid == 61:
        return "nota de crédito"
    return "boleta" if tid == 39 else "factura"


def _brand_logo_path() -> Path | None:
    custom = (os.getenv("DTE_EMAIL_LOGO_PATH") or "").strip()
    if custom:
        path = Path(custom)
        if path.is_file():
            return path
    default = Path(__file__).resolve().parents[1] / "static" / "logo.png"
    return default if default.is_file() else None


def _load_brand_logo_bytes() -> bytes | None:
    path = _brand_logo_path()
    if not path:
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def _payable_total(dte) -> int:
    """Monto a pagar (cash/card/total). Ya incluye chip si chip_id=1; no suma 5000 otra vez."""
    return ticket_payment_total(dte)


def _chip_breakdown_rows(dte) -> str:
    """Filas HTML: estacionamiento + chip = total a pagar."""
    chip_id = int(getattr(dte, "chip_id", 0) or 0)
    category_id = int(getattr(dte, "category_id", 1) or 1)
    if not _chip_applies(chip_id, category_id):
        return ""
    parking = parking_gross_from_dte(dte)
    parking_s = html.escape(_format_clp(parking))
    chip_s = html.escape(_format_clp(DTE_CHIP_AMOUNT_CLP))
    return f"""
                <tr>
                  <td style="padding:0 20px 10px;font-size:14px;color:{JIS_TEXT_MUTED};">Estacionamiento</td>
                  <td style="padding:0 20px 10px;font-size:14px;color:{JIS_TEXT};text-align:right;">{parking_s}</td>
                </tr>
                <tr>
                  <td style="padding:0 20px 10px;font-size:14px;color:{JIS_TEXT_MUTED};">Chip</td>
                  <td style="padding:0 20px 10px;font-size:14px;color:{JIS_TEXT};text-align:right;">{chip_s}</td>
                </tr>
    """


def _build_html_body(
    *,
    customer_name: str,
    dte_label: str,
    folio: int,
    issue_date: str,
    total_clp: str,
    payment_link: str | None,
    is_paid: bool,
    has_logo: bool,
    chip_rows: str = "",
    status_label: str,
) -> str:
    name = html.escape(customer_name or "Cliente")
    label = html.escape(dte_label)
    date_s = html.escape(issue_date)
    total_s = html.escape(total_clp)
    folio_s = html.escape(str(folio))
    status_s = html.escape(status_label)
    status_color = JIS_SUCCESS if is_paid else JIS_WARNING

    logo_block = ""
    if has_logo:
        logo_block = f"""
              <img src="cid:{LOGO_CID}" alt="JIS Parking" width="200"
                   style="display:block;margin:0 auto 14px;max-width:200px;height:auto;border:0;" />
        """

    if is_paid:
        pay_block = f"""
          <p style="margin:24px 0 0;padding:14px 18px;background:{JIS_SUCCESS_LIGHT};border-radius:8px;
                    color:{JIS_SUCCESS};font-size:15px;border:1px solid #c0e5d9;">
            Este documento ya se encuentra <strong>pagado</strong>. El PDF va adjunto a este correo.
          </p>
        """
    elif payment_link:
        link = html.escape(payment_link, quote=True)
        pay_block = f"""
          <p style="margin:28px 0 10px;font-size:15px;color:{JIS_TEXT};">
            Puede pagar en línea de forma segura con <strong>Klap</strong>:
          </p>
          <p style="margin:0 0 20px;text-align:center;">
            <a href="{link}"
               style="display:inline-block;background:{JIS_WARNING};color:#ffffff;text-decoration:none;
                      padding:14px 36px;border-radius:8px;font-size:16px;font-weight:bold;
                      box-shadow:0 4px 12px rgba(229,138,0,0.35);">
              Pagar ahora
            </a>
          </p>
          <p style="margin:0;font-size:12px;color:{JIS_TEXT_MUTED};word-break:break-all;line-height:1.5;">
            Si el botón no funciona, copie este enlace en su navegador:<br>
            <a href="{link}" style="color:{JIS_PRIMARY};">{link}</a>
          </p>
        """
    else:
        pay_block = f"""
          <p style="margin:24px 0 0;font-size:14px;color:{JIS_TEXT_MUTED};">
            El PDF del documento va adjunto a este correo.
          </p>
        """

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{JIS_BG};font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{JIS_BG};padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 20px rgba(21,45,138,0.12);border:1px solid {JIS_BORDER};">
          <tr>
            <td style="background:linear-gradient(135deg,{JIS_PRIMARY_DARK} 0%,{JIS_PRIMARY} 100%);
                       padding:28px 32px 22px;text-align:center;">
              {logo_block}
              <p style="margin:0;font-size:13px;color:#ffffff;letter-spacing:0.4px;
                        text-transform:uppercase;font-weight:700;">
                <span style="color:#ffffff;">Documento tributario electr&oacute;nico</span>
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 28px;">
              <p style="margin:0 0 16px;font-size:16px;color:{JIS_TEXT};">
                Estimado/a <strong style="color:{JIS_PRIMARY};">{name}</strong>,
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:{JIS_TEXT_MUTED};line-height:1.55;">
                Adjuntamos su {label} electrónica y los datos para su pago.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                     style="background:{JIS_PRIMARY_LIGHT};border-radius:10px;border:1px solid {JIS_BORDER};">
                <tr>
                  <td style="padding:16px 20px;font-size:14px;color:{JIS_TEXT_MUTED};">Tipo</td>
                  <td style="padding:16px 20px;font-size:14px;color:{JIS_TEXT};text-align:right;text-transform:capitalize;">
                    <strong>{label}</strong>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Folio</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT};text-align:right;">
                    <strong>{folio_s}</strong>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Fecha</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT};text-align:right;">{date_s}</td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Estado</td>
                  <td style="padding:0 20px 16px;font-size:14px;text-align:right;font-weight:bold;color:{status_color};">
                    {status_s}
                  </td>
                </tr>
                {chip_rows}
                <tr>
                  <td style="padding:0 20px 18px;font-size:14px;color:{JIS_TEXT_MUTED};">Total a pagar</td>
                  <td style="padding:0 20px 18px;font-size:20px;color:{JIS_PRIMARY};text-align:right;font-weight:bold;">
                    {total_s}
                  </td>
                </tr>
              </table>
              {pay_block}
            </td>
          </tr>
          <tr>
            <td style="padding:18px 32px;background:{JIS_BG};border-top:3px solid {JIS_WARNING};">
              <p style="margin:0;font-size:12px;color:{JIS_TEXT_MUTED};line-height:1.55;text-align:center;">
                <strong style="color:{JIS_PRIMARY};">JIS Parking SPA</strong> · RUT 76.063.822-6<br>
                Nuestro servicio es un compromiso ·
                <a href="mailto:contacto@jisparking.com" style="color:{JIS_PRIMARY};text-decoration:none;">
                  contacto@jisparking.com
                </a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_credit_note_html_body(
    *,
    customer_name: str,
    folio: int,
    issue_date: str,
    amount_clp: str,
    ref_folio: int | None,
    ref_dte_label: str | None,
    has_logo: bool,
) -> str:
    name = html.escape(customer_name or "Cliente")
    date_s = html.escape(issue_date)
    amount_s = html.escape(amount_clp)
    folio_s = html.escape(str(folio))
    ref_block = ""
    if ref_folio and ref_dte_label:
        ref_block = f"""
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Documento anulado</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT};text-align:right;">
                    <strong>{html.escape(ref_dte_label)} folio {html.escape(str(ref_folio))}</strong>
                  </td>
                </tr>
        """

    logo_block = ""
    if has_logo:
        logo_block = f"""
              <img src="cid:{LOGO_CID}" alt="JIS Parking" width="200"
                   style="display:block;margin:0 auto 14px;max-width:200px;height:auto;border:0;" />
        """

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{JIS_BG};font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{JIS_BG};padding:28px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 20px rgba(21,45,138,0.12);border:1px solid {JIS_BORDER};">
          <tr>
            <td style="background:linear-gradient(135deg,{JIS_PRIMARY_DARK} 0%,{JIS_PRIMARY} 100%);
                       padding:28px 32px 22px;text-align:center;">
              {logo_block}
              <p style="margin:0;font-size:13px;color:#ffffff;letter-spacing:0.4px;
                        text-transform:uppercase;font-weight:700;">
                Nota de cr&eacute;dito electr&oacute;nica
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 28px;">
              <p style="margin:0 0 16px;font-size:16px;color:{JIS_TEXT};">
                Estimado/a <strong style="color:{JIS_PRIMARY};">{name}</strong>,
              </p>
              <p style="margin:0 0 24px;font-size:15px;color:{JIS_TEXT_MUTED};line-height:1.55;">
                Adjuntamos su nota de cr&eacute;dito electr&oacute;nica. Este documento anula el DTE referenciado
                y <strong>no requiere pago</strong>.
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                     style="background:{JIS_PRIMARY_LIGHT};border-radius:10px;border:1px solid {JIS_BORDER};">
                <tr>
                  <td style="padding:16px 20px;font-size:14px;color:{JIS_TEXT_MUTED};">Tipo</td>
                  <td style="padding:16px 20px;font-size:14px;color:{JIS_TEXT};text-align:right;">
                    <strong>Nota de cr&eacute;dito</strong>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Folio NC</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT};text-align:right;">
                    <strong>{folio_s}</strong>
                  </td>
                </tr>
                <tr>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT_MUTED};">Fecha</td>
                  <td style="padding:0 20px 16px;font-size:14px;color:{JIS_TEXT};text-align:right;">{date_s}</td>
                </tr>
                {ref_block}
                <tr>
                  <td style="padding:0 20px 18px;font-size:14px;color:{JIS_TEXT_MUTED};">Monto NC</td>
                  <td style="padding:0 20px 18px;font-size:20px;color:{JIS_PRIMARY};text-align:right;font-weight:bold;">
                    {amount_s}
                  </td>
                </tr>
              </table>
              <p style="margin:24px 0 0;font-size:14px;color:{JIS_TEXT_MUTED};line-height:1.55;">
                El PDF va adjunto a este correo. Si tiene dudas, escr&iacute;banos a
                <a href="mailto:contacto@jisparking.com" style="color:{JIS_PRIMARY};">contacto@jisparking.com</a>.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 32px;background:{JIS_BG};border-top:3px solid {JIS_WARNING};">
              <p style="margin:0;font-size:12px;color:{JIS_TEXT_MUTED};line-height:1.55;text-align:center;">
                <strong style="color:{JIS_PRIMARY};">JIS Parking SPA</strong> · RUT 76.063.822-6<br>
                Nuestro servicio es un compromiso
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

    def send(
        self,
        dte,
        customer=None,
        to_emails=None,
        *,
        ref_folio: int | None = None,
        ref_dte_type_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Envía correo HTML con PDF adjunto.
        Boleta/factura v2: enlace Klap. NC v2: plantilla sin pago. LibreDTE: usar resend LibreDTE.
        """
        if is_subscriber_v2_credit_note(dte):
            return self._send_credit_note_v2(
                dte,
                customer=customer,
                to_emails=to_emails,
                ref_folio=ref_folio,
                ref_dte_type_id=ref_dte_type_id,
            )
        return self._send_payable_document(
            dte,
            customer=customer,
            to_emails=to_emails,
        )

    def _send_credit_note_v2(
        self,
        dte,
        customer=None,
        to_emails=None,
        *,
        ref_folio: int | None = None,
        ref_dte_type_id: int | None = None,
    ) -> dict[str, Any]:
        if not dte or not getattr(dte, "folio", None):
            return {"status": "error", "message": "NC sin folio para envío de correo"}

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
        ref_folio = ref_folio or getattr(dte, "denied_folio", None)
        ref_tid = int(ref_dte_type_id or 39)
        ref_label = _dte_label(ref_tid) if ref_folio else None
        customer_name = (getattr(customer, "customer", None) or "Cliente").strip()
        issue_date = (
            dte.added_date.strftime("%d-%m-%Y")
            if getattr(dte, "added_date", None)
            else ""
        )
        amount = abs(int(getattr(dte, "total", 0) or 0))

        pdf_bytes, pdf_err = self._fetch_pdf_bytes(dte)
        if not pdf_bytes:
            return {
                "status": "error",
                "message": pdf_err or "No se pudo adjuntar el PDF",
            }

        subject = f"JIS Parking - Nota de crédito electrónica folio {folio}"
        logo_bytes = _load_brand_logo_bytes()
        html_body = _build_credit_note_html_body(
            customer_name=customer_name,
            folio=folio,
            issue_date=issue_date,
            amount_clp=_format_clp(amount),
            ref_folio=int(ref_folio) if ref_folio else None,
            ref_dte_label=ref_label,
            has_logo=bool(logo_bytes),
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

        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"nota_credito_{folio}.pdf",
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
            f"[dte-email-nc] sent folio={folio} to={recipients} ref={ref_label} {ref_folio}",
            flush=True,
        )
        return {
            "status": "success",
            "message": "Correo NC enviado",
            "to": recipients,
            "subject": subject,
        }

    def _send_payable_document(
        self,
        dte,
        customer=None,
        to_emails=None,
    ) -> dict[str, Any]:
        """
        Boleta/factura v2: PDF adjunto + enlace Klap (proxy /api/payments/pay/{folio}).
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
        total = _payable_total(dte)
        is_paid = int(getattr(dte, "status_id", 0) or 0) == 5
        status_label = "Pagado" if is_paid else "Pendiente de pago"
        payment_link = None if is_paid else self._payment_link(dte, customer)

        if _chip_applies(
            int(getattr(dte, "chip_id", 0) or 0),
            int(getattr(dte, "category_id", 1) or 1),
        ):
            parking = parking_gross_from_dte(dte)
            print(
                f"[dte-email] folio={folio} chip_id=1 estacionamiento={parking} "
                f"+ chip {DTE_CHIP_AMOUNT_CLP} = total_pago {total}",
                flush=True,
            )

        pdf_bytes, pdf_err = self._fetch_pdf_bytes(dte)
        if not pdf_bytes:
            return {
                "status": "error",
                "message": pdf_err or "No se pudo adjuntar el PDF",
            }

        subject = f"JIS Parking - {dte_label.capitalize()} electronica folio {folio}"
        logo_bytes = _load_brand_logo_bytes()
        html_body = _build_html_body(
            customer_name=customer_name,
            dte_label=dte_label,
            folio=folio,
            issue_date=issue_date,
            total_clp=_format_clp(total),
            payment_link=payment_link,
            is_paid=is_paid,
            has_logo=bool(logo_bytes),
            chip_rows=_chip_breakdown_rows(dte),
            status_label=status_label,
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
