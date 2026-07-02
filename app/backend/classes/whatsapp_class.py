import requests
from app.backend.db.models import CustomerModel, MovementModel, WhatsappTemplateModel, BranchOfficeModel, UserModel, DteModel, CapitulationModel, ExpenseTypeModel, MovementProductModel, ProductModel
import os
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
import json
from app.backend.classes.payments_env import payments_env
load_dotenv()

WHATSAPP_GRAPH_PHONE_NUMBER_ID = "101066132689690"
WHATSAPP_GRAPH_API_VERSION = "v20.0"
WHATSAPP_TEMPLATE_LIBREDTE_ID = 1
WHATSAPP_TEMPLATE_LIBREDTE_TITLE = "envio_dte"
WHATSAPP_TEMPLATE_KLAP_ID = 8
WHATSAPP_TEMPLATE_KLAP_TITLE = "envio_dte_v3"


def whatsapp_access_token() -> str:
    """Meta Graph token for WhatsApp (WHATSAPP_ACCESS_TOKEN, fallback LIBREDTE_TOKEN)."""
    return (
        os.getenv("WHATSAPP_ACCESS_TOKEN")
        or os.getenv("LIBREDTE_TOKEN")
        or ""
    ).strip()


def whatsapp_graph_messages_url() -> str:
    return (
        f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/"
        f"{WHATSAPP_GRAPH_PHONE_NUMBER_ID}/messages"
    )


def _whatsapp_template_libredte(db):
    """Factura LibreDTE: plantilla envio_dte (botón pago LibreDTE)."""
    return (
        db.query(WhatsappTemplateModel)
        .filter(WhatsappTemplateModel.title == WHATSAPP_TEMPLATE_LIBREDTE_TITLE)
        .first()
        or db.query(WhatsappTemplateModel)
        .filter(WhatsappTemplateModel.id == WHATSAPP_TEMPLATE_LIBREDTE_ID)
        .first()
    )


def _whatsapp_template_klap(db):
    """Boleta SimpleFactura + Klap: plantilla envio_dte_v3 (botón /api/payments/pay/…)."""
    return (
        db.query(WhatsappTemplateModel)
        .filter(WhatsappTemplateModel.title == WHATSAPP_TEMPLATE_KLAP_TITLE)
        .first()
        or db.query(WhatsappTemplateModel)
        .filter(WhatsappTemplateModel.id == WHATSAPP_TEMPLATE_KLAP_ID)
        .first()
    )


def validate_whatsapp_access_token() -> dict | None:
    """Return an error dict when the Meta token is missing or invalid."""
    token = whatsapp_access_token()
    if not token:
        return {
            "status": "error",
            "message": "WHATSAPP_ACCESS_TOKEN / LIBREDTE_TOKEN is not configured",
            "whatsapp_accepted": "rejected",
        }
    try:
        response = requests.get(
            f"https://graph.facebook.com/{WHATSAPP_GRAPH_API_VERSION}/me",
            params={"access_token": token},
            timeout=15,
        )
        if response.status_code == 200:
            return None
        payload = response.json() if response.content else {}
        error = payload.get("error") or {}
        return {
            "status": "error",
            "message": (
                "Invalid or expired WhatsApp token (Meta Graph API). "
                "Renew WHATSAPP_ACCESS_TOKEN in Meta Business."
            ),
            "status_code": response.status_code,
            "response": payload,
            "whatsapp_error_code": error.get("code"),
            "whatsapp_accepted": "rejected",
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Could not validate WhatsApp token: {exc}",
            "whatsapp_accepted": "rejected",
        }


def payment_proxy_public_url(pay_id: str) -> str:
    """Public URL that redirects to the payment gateway checkout (folio or legacy order_id)."""
    base = payments_env(
        "PAYMENTS_WHATSAPP_PROXY_PUBLIC_BASE",
        default="https://intrajisbackend.com/api/payments/pay",
    ).rstrip("/")
    return f"{base}/{pay_id}"


def _whatsapp_document_pdf_url(db, dte_data) -> tuple[str | None, dict | None]:
    """Public PDF URL for WhatsApp template header; ensures file is in the web-served files dir."""
    from fastapi import HTTPException
    from app.backend.classes.file_class import FileClass
    from app.backend.classes.customer_bill_class import CustomerBillClass
    from app.backend.classes.customer_ticket_class import CustomerTicketClass

    folio = int(getattr(dte_data, "folio", 0) or 0)
    if folio <= 0:
        return None, {"status": "error", "message": "DTE sin folio para PDF WhatsApp"}

    remote_path = f"{folio}.pdf"
    fc = FileClass(db)
    try:
        fc.download(remote_path)
        return fc.get(remote_path), None
    except HTTPException:
        pass

    dte_type_id = int(getattr(dte_data, "dte_type_id", 0) or 0)
    if dte_type_id == 39:
        pdf_result = CustomerTicketClass(db).save_simplefactura_pdf_ticket(folio, dte_type_id=dte_type_id)
    elif dte_type_id == 33:
        pdf_result = CustomerBillClass(db).save_pdf_bill(folio)
    else:
        return None, {"status": "error", "message": f"Tipo DTE {dte_type_id} no soportado para PDF WhatsApp"}

    if not isinstance(pdf_result, dict) or pdf_result.get("status") != "success":
        return None, pdf_result or {"status": "error", "message": "No se pudo obtener PDF"}

    return pdf_result.get("url") or fc.get(remote_path), None


def _parse_whatsapp_graph_response(response) -> dict:
    try:
        response_data = response.json() if response.content else {}
    except Exception as exc:
        return {
            "status": "error",
            "status_code": response.status_code,
            "response": response.text,
            "error": str(exc),
            "whatsapp_accepted": "rejected",
        }

    graph_error = (response_data.get("error") or {}) if isinstance(response_data, dict) else {}
    messages = response_data.get("messages") if isinstance(response_data, dict) else None
    message_status = None
    if isinstance(messages, list) and messages:
        message_status = messages[0].get("message_status")

    if response.status_code != 200:
        return {
            "status": "error",
            "status_code": response.status_code,
            "response": response_data,
            "message": graph_error.get("message") or "Error al enviar WhatsApp",
            "whatsapp_error_code": graph_error.get("code"),
            "whatsapp_accepted": "rejected",
        }

    return {
        "status": "success",
        "status_code": response.status_code,
        "response": response_data,
        "message_status": message_status,
        "whatsapp_accepted": "accepted" if message_status == "accepted" else "pending",
    }


def _payments_whatsapp_url_data(
    order_id: str,
    redirect_url: str,
    *,
    document_folio: int | str | None = None,
) -> str:
    """
    Dynamic {{1}} suffix for the WhatsApp template URL button.

    Proxy mode (default): Meta template base
    https://intrajisbackend.com/api/payments/pay/{{1}}
    and we send the document folio so the same message works after a rejected payment.

    Direct mode: template uses PAYMENTS_WHATSAPP_URL_BASE + {{1}}.
    """
    mode = payments_env("PAYMENTS_WHATSAPP_URL_MODE", default="proxy").strip().lower()
    if mode == "direct":
        redirect_url = (redirect_url or "").strip()
        if not redirect_url:
            return ""
        base = payments_env(
            "PAYMENTS_WHATSAPP_URL_BASE",
            default="https://pagos-pasarela.multicaja.cl/",
        ).rstrip("/") + "/"
        if redirect_url.startswith(base):
            return redirect_url[len(base):]
        parsed = urlparse(redirect_url)
        suffix = (parsed.path or "").lstrip("/")
        if parsed.query:
            suffix = f"{suffix}?{parsed.query}"
        return suffix
    folio = document_folio or order_id or ""
    return str(folio).strip()


def _libredte_issue_date_from_emitido_info(response: requests.Response, fallback_date=None) -> str:
    """
    LibreDTE /dte_emitidos/info puede devolver un objeto JSON; si falla el parseo o viene un
    formato inesperado (p. ej. string), no usar claves tipo dict sobre un str (evita
    «string indices must be integers»).
    """
    issue_date = None
    try:
        data = response.json()
    except Exception:
        body = (response.text or "").strip().strip('"')
        if len(body) >= 10 and body[4] == "-" and body[7] == "-":
            issue_date = body[:10]
        return issue_date or (_fmt_yyyy_mm_dd(fallback_date) if fallback_date else datetime.now().strftime("%Y-%m-%d"))

    if isinstance(data, dict):
        issue_date = data.get("fecha") or data.get("FchEmis") or data.get("fch_emis")
        if issue_date and not isinstance(issue_date, str):
            issue_date = str(issue_date)[:10]
    elif isinstance(data, str):
        s = data.strip().strip('"')
        if len(s) >= 10 and s[4] == "-" and s[7] == "-":
            issue_date = s[:10]

    if not issue_date:
        issue_date = _fmt_yyyy_mm_dd(fallback_date) if fallback_date else datetime.now().strftime("%Y-%m-%d")
    return issue_date[:10] if issue_date else datetime.now().strftime("%Y-%m-%d")


def _fmt_yyyy_mm_dd(dt) -> str:
    if dt is None:
        return datetime.now().strftime("%Y-%m-%d")
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    s = str(dt).strip()
    return s[:10] if len(s) >= 10 else datetime.now().strftime("%Y-%m-%d")


class WhatsappClass:
    def __init__(self, db):
        self.db = db

    def send_text_message(self, to_phone: str, body: str):
        """
        Envía un mensaje de texto por la API Graph (mismo token y phone_number_id que el resto del proyecto).
        Útil para respuestas del webhook (conversación dentro de la ventana de 24h).
        """
        try:
            token = os.getenv("LIBREDTE_TOKEN")
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"
            phone_str = str(to_phone).strip()
            if not phone_str.startswith("56"):
                customer_phone = "56" + phone_str.lstrip("0")
            else:
                customer_phone = phone_str

            payload = {
                "messaging_product": "whatsapp",
                "to": customer_phone,
                "type": "text",
                "text": {"preview_url": False, "body": (body or "")[:4096]},
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            try:
                response_data = response.json()
            except Exception:
                response_data = {"raw": response.text}
            ok = response.status_code == 200
            if not ok:
                print(f"[WhatsappClass.send_text_message] {response.status_code} {response_data}")
            return {
                "status": "success" if ok else "error",
                "status_code": response.status_code,
                "response": response_data,
            }
        except Exception as e:
            print(f"[WhatsappClass.send_text_message] {e}")
            return {"status": "error", "error": str(e)}

    def send(self, dte_data, customer_rut):
        if int(getattr(dte_data, "dte_type_id", 0) or 0) == 39:
            print("[send] Boleta → send_v2_invoice (SimpleFactura/Klap)", flush=True)
            return self.send_v2_invoice(dte_data, customer_rut)

        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == customer_rut).first()
        whatsapp_template = _whatsapp_template_libredte(self.db)
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        pdf_url, pdf_error = _whatsapp_document_pdf_url(self.db, dte_data)
        if pdf_error:
            return {**pdf_error, "whatsapp_accepted": "rejected"}
        image = pdf_url

        token = whatsapp_access_token()

        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        issued_dte_info_url = "https://libredte.cl/api/dte/dte_emitidos/info/"+ str(dte_data.dte_type_id) +"/"+ str(dte_data.folio) +"/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

        headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

        issued_dte_info_response = requests.get(issued_dte_info_url, headers=headers, timeout=45)

        print(issued_dte_info_response.text)
        issued_date_for_payment_link = _libredte_issue_date_from_emitido_info(issued_dte_info_response, getattr(dte_data, "added_date", None))

        url_data = str(dte_data.dte_type_id) + '/' + str(dte_data.folio) + '/76063822/' + issued_date_for_payment_link + '/' + str(dte_data.total)
        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        added_date_str = dte_data.added_date.strftime('%d-%m-%Y')

        if dte_data.chip_id == 1:
            total = dte_data.total + 5000

        required_fields = {
            "DTE type": dte_data.dte_type_id,
            "Folio": dte_data.folio,
            "Date": added_date_str,
            "Total": dte_data.total,
            "Branch": branch_office.branch_office,
            "Supervisor": user.full_name,
            "Phone": user.phone,
            "Email": user.email
        }

        for label, value in required_fields.items():
            if value is None or str(value).strip() == "":
                raise ValueError(f"El campo '{label}' está vacío o no definido.")
            
        if dte_data.dte_type_id == 39:
            dte_type = "boleta"
        else:
            dte_type = "factura"

        phone_str = str(customer.phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer_phone}",
                    "type": "template",
                    "template": {
                        "name": whatsapp_template.title,
                        "language": {"code": "es"},
                        "components": [
                            {
                                "type": "header",
                                "parameters": [
                                    {
                                        "type": "document",
                                        "document": {
                                            "link": image,
                                            "filename": f"{dte_data.folio}.pdf"
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": str(dte_type)},
                                    {"type": "text", "text": str(dte_data.folio)},
                                    {"type": "text", "text": added_date_str},
                                    {"type": "text", "text": str(dte_data.total)},
                                    {"type": "text", "text": branch_office.branch_office},
                                    {"type": "text", "text": user.full_name},
                                    {"type": "text", "text": user.phone},
                                    {"type": "text", "text": user.email},
                                ]
                            },
                            {
                                "type": "button",
                                "index": "0",
                                "sub_type": "url",
                                "parameters": [
                                    {"type": "text", "text": url_data}
                                ]
                            }
                        ]
                    }
                }
        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)
        
        # Devolver la respuesta del envío de WhatsApp
        try:
            response_data = response.json()
            return {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_data,
                "whatsapp_accepted": "accepted" if response.status_code == 200 else "rejected"
            }
        except Exception as e:
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text,
                "error": str(e),
                "whatsapp_accepted": "rejected"
            }

    def send_v2_invoice(self, dte_data, customer_rut, pdf_url=None, phone_override=None):
        """
        WhatsApp post-emisión v2 (gateway + online payment).
        Plantilla Meta: envio_dte_v3 (botón → /api/payments/pay/{order_id}).
        """
        from app.backend.classes.payment_gateway_class import PaymentGatewayClass
        from app.backend.classes.customer_ticket_class import CustomerTicketClass

        folio = getattr(dte_data, "folio", None)

        customer = (
            self.db.query(CustomerModel)
            .filter(CustomerModel.rut == customer_rut)
            .first()
        )
        if not customer:
            result = {"status": "skipped", "message": "Cliente no encontrado"}
            print(f"[v2] WhatsApp folio={folio} skipped: {result['message']}", flush=True)
            return result

        phone_raw = phone_override if phone_override else customer.phone
        if not phone_raw or str(phone_raw).strip() == "":
            result = {"status": "skipped", "message": "Cliente sin teléfono"}
            print(f"[v2] WhatsApp folio={folio} skipped: {result['message']} rut={customer_rut}", flush=True)
            return result

        whatsapp_template = _whatsapp_template_klap(self.db)
        if not whatsapp_template or not whatsapp_template.title:
            result = {
                "status": "error",
                "message": f"Plantilla WhatsApp {WHATSAPP_TEMPLATE_KLAP_TITLE} no encontrada",
            }
            print(f"[v2] WhatsApp folio={folio} error: {result['message']}", flush=True)
            return result
        if whatsapp_template.title != WHATSAPP_TEMPLATE_KLAP_TITLE:
            print(
                f"[v2] WhatsApp folio={folio} warning: template id={whatsapp_template.id} "
                f"title={whatsapp_template.title!r} (expected {WHATSAPP_TEMPLATE_KLAP_TITLE})",
                flush=True,
            )

        branch_office = (
            self.db.query(BranchOfficeModel)
            .filter(BranchOfficeModel.id == dte_data.branch_office_id)
            .first()
        )
        if not branch_office:
            result = {"status": "error", "message": "Sucursal no encontrada"}
            print(f"[v2] WhatsApp folio={folio} error: {result['message']}", flush=True)
            return result

        user = (
            self.db.query(UserModel)
            .filter(UserModel.rut == branch_office.principal_supervisor)
            .first()
        )
        if not user:
            result = {"status": "error", "message": "Supervisor de sucursal no encontrado"}
            print(f"[v2] WhatsApp folio={folio} error: {result['message']}", flush=True)
            return result

        document_url = pdf_url
        if not document_url:
            pdf_result = CustomerTicketClass(self.db).save_simplefactura_pdf_ticket(
                dte_data.folio,
                dte_type_id=dte_data.dte_type_id,
            )
            if pdf_result.get("status") != "success":
                print(f"[v2] PDF para WhatsApp folio={folio}: {pdf_result}", flush=True)
            document_url = pdf_result.get("url") or (
                f"https://intrajisbackend.com/files/{dte_data.folio}.pdf"
            )

        print(f"[v2] WhatsApp folio={folio} creating payment order total={dte_data.total}", flush=True)
        order_result = PaymentGatewayClass().create_subscriber_dte_order(dte_data, customer)
        if order_result.get("status") != "success":
            result = {
                "status": "error",
                "message": order_result.get("message") or "Failed to create payment order",
                "payments": order_result,
            }
            print(f"[v2] WhatsApp folio={folio} payment order failed: {result}", flush=True)
            return result

        order_id = order_result.get("order_id")
        redirect_url = order_result.get("redirect_url")
        url_data = _payments_whatsapp_url_data(
            order_id,
            redirect_url,
            document_folio=folio,
        )
        if not url_data:
            result = {
                "status": "error",
                "message": "Payment order missing order_id/redirect_url for WhatsApp button",
                "payments": order_result,
            }
            print(f"[v2] WhatsApp folio={folio} error: {result['message']}", flush=True)
            return result
        payment_link = payment_proxy_public_url(url_data)

        from app.backend.classes.dte_payment_data_class import DtePaymentDataClass

        DtePaymentDataClass(self.db).record_order_created(
            dte=dte_data,
            customer=customer,
            order_id=str(order_id or ""),
            reference_id=str(folio),
            gateway_response=order_result.get("response"),
        )

        token = whatsapp_access_token()
        graph_url = whatsapp_graph_messages_url()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        added_date_str = dte_data.added_date.strftime("%d-%m-%Y")

        required_fields = {
            "DTE type": dte_data.dte_type_id,
            "Folio": dte_data.folio,
            "Date": added_date_str,
            "Total": dte_data.total,
            "Branch": branch_office.branch_office,
            "Supervisor": user.full_name,
            "Phone": user.phone,
            "Email": user.email,
        }
        for label, value in required_fields.items():
            if value is None or str(value).strip() == "":
                result = {
                    "status": "error",
                    "message": f"El campo '{label}' está vacío o no definido.",
                }
                print(f"[v2] WhatsApp folio={folio} error: {result['message']}", flush=True)
                return result

        dte_type = "boleta" if int(dte_data.dte_type_id) == 39 else "factura"

        phone_str = str(phone_raw).strip()
        customer_phone = phone_str if phone_str.startswith("56") else "56" + phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": f"{customer_phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": document_url,
                                    "filename": f"{dte_data.folio}.pdf",
                                },
                            }
                        ],
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(dte_type)},
                            {"type": "text", "text": str(dte_data.folio)},
                            {"type": "text", "text": added_date_str},
                            {"type": "text", "text": str(dte_data.total)},
                            {"type": "text", "text": branch_office.branch_office},
                            {"type": "text", "text": user.full_name},
                            {"type": "text", "text": user.phone},
                            {"type": "text", "text": user.email},
                        ],
                    },
                    {
                        "type": "button",
                        "index": "0",
                        "sub_type": "url",
                        "parameters": [{"type": "text", "text": url_data}],
                    },
                ],
            },
        }

        print(
            f"[v2] WhatsApp template={whatsapp_template.title} url_data={url_data} payment_link={payment_link}",
            flush=True,
        )
        print(payload, flush=True)

        token_error = validate_whatsapp_access_token()
        if token_error:
            print(f"[v2] WhatsApp folio={folio} token check failed: {token_error}", flush=True)
            token_error["payments"] = {
                "order_id": order_id,
                "redirect_url": redirect_url,
                "payment_link": payment_link,
                "url_data": url_data,
                "template": whatsapp_template.title,
            }
            return token_error

        try:
            response = requests.post(graph_url, json=payload, headers=headers, timeout=45)
            print(response.text, flush=True)
            response_data = response.json() if response.content else {}
            graph_error = (response_data.get("error") or {}) if isinstance(response_data, dict) else {}
            if response.status_code != 200 and graph_error.get("code") == 190:
                result = {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": (
                        "Invalid or expired WhatsApp token (Meta error 190). "
                        "Renew WHATSAPP_ACCESS_TOKEN in Meta Business."
                    ),
                    "response": response_data,
                    "whatsapp_error_code": 190,
                    "whatsapp_accepted": "rejected",
                    "payments": {
                        "order_id": order_id,
                        "redirect_url": redirect_url,
                        "payment_link": payment_link,
                        "url_data": url_data,
                        "template": whatsapp_template.title,
                    },
                }
                print(f"[v2] WhatsApp folio={folio} Meta 190: renew WHATSAPP_ACCESS_TOKEN", flush=True)
                return result
            result = {
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response": response_data,
                "whatsapp_accepted": "accepted" if response.status_code == 200 else "rejected",
                "payments": {
                    "order_id": order_id,
                    "redirect_url": redirect_url,
                    "payment_link": payment_link,
                    "url_data": url_data,
                    "template": whatsapp_template.title,
                },
            }
            print(
                f"[v2] WhatsApp folio={folio} send status={result['status']} "
                f"http={response.status_code} accepted={result['whatsapp_accepted']}",
                flush=True,
            )
            if result["status"] != "success":
                print(f"[v2] WhatsApp folio={folio} graph response: {response_data}", flush=True)
            return result
        except Exception as exc:
            result = {
                "status": "error",
                "error": str(exc),
                "whatsapp_accepted": "rejected",
                "payments": order_result,
            }
            print(f"[v2] WhatsApp folio={folio} exception: {exc}", flush=True)
            return result

    def check_whatsapp_balance(self):
        """
        Valida si WhatsApp tiene crédito disponible haciendo una verificación.
        Retorna True si tiene crédito, False si no tiene (error de pago).
        """
        try:
            token = os.getenv("LIBREDTE_TOKEN")
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Intentar enviar un mensaje de prueba usando template al número del administrador
            # Esto nos permite detectar el error de pago sin procesar DTEs reales
            test_phone = "56976357193"
            
            # Usar template simple (asumiendo que existe un template de texto simple)
            # Si no existe, se puede crear uno o usar otro template existente
            whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
            
            if not whatsapp_template:
                print("⚠️ No se encontró template de WhatsApp para validación")
                return False
            
            # Usar template con mensaje "Test"
            payload = {
                "messaging_product": "whatsapp",
                "to": test_phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "Test"}
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            print(f"Respuesta de validación de balance: {response_data}")
            
            # Verificar si hay error de pago
            if "error" in response_data:
                error_code = response_data.get("error", {}).get("code")
                error_message = response_data.get("error", {}).get("message", "")
                
                print(f"Error detectado - Código: {error_code}, Mensaje: {error_message}")
                
                if error_code == 131042 or "Payment required" in error_message or "(#131042)" in str(error_message):
                    print("⚠️ Error de pago detectado: WhatsApp no tiene crédito")
                    return False
            
            # Si el status code es 200, tiene crédito
            if response.status_code == 200:
                print("✅ WhatsApp tiene crédito disponible")
                return True
            
            # Si hay otro error, asumimos que no tiene crédito para ser conservadores
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"Error al validar balance de WhatsApp: {str(e)}")
            # En caso de error, asumimos que no tiene crédito para ser conservadores
            return False

    def send_notification_to_admin(self, message):
        """
        Envía un mensaje de notificación al número de administrador (976357193) usando template.
        """
        try:
            token = os.getenv("LIBREDTE_TOKEN")
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            admin_phone = "56976357193"
            
            # Obtener template (usar template 1 como base, o el que sea apropiado)
            whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 1).first()
            
            if not whatsapp_template:
                print("⚠️ No se encontró template de WhatsApp para notificación")
                return {
                    "status": "error",
                    "error": "Template no encontrado"
                }
            
            # Usar template con el mensaje (usando "Test" como parámetro)
            payload = {
                "messaging_product": "whatsapp",
                "to": admin_phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": "Test"}
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()
            
            print(f"Notificación enviada a administrador: {response_data}")
            return {
                "status": "success" if response.status_code == 200 else "error",
                "response": response_data
            }
            
        except Exception as e:
            print(f"Error al enviar notificación a administrador: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def movements(self, movement_id):
        movement = self.db.query(MovementModel).filter(MovementModel.id == movement_id).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == movement.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 4).first()
        
        # Obtener los productos del movimiento
        movement_products = self.db.query(MovementProductModel, ProductModel).join(
            ProductModel, ProductModel.id == MovementProductModel.product_id
        ).filter(MovementProductModel.movement_id == movement_id).all()
        
        # Crear lista de nombres de productos separados por coma
        products = ", ".join([product_model.description for movement_product, product_model in movement_products])
        
        phone = user.phone  # Ej: '912345678'
        supervisor_name = user.full_name
        movement_id = movement.id

        # URL de la API
        url = 'https://graph.facebook.com/v20.0/101066132689690/messages'

        token = os.getenv("LIBREDTE_TOKEN")

        # Cabeceras
        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            phone = "56" + phone_str
        else:
            phone = phone_str

        # Payload en formato JSON
        payload = {
            "messaging_product": "whatsapp",
            "to": f"{phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(supervisor_name)},
                            {"type": "text", "text": str(movement_id)},
                            {"type": "text", "text": str(products)}
                        ]
                    }
                ]
            }
        }

        print(payload)

        # Enviar la solicitud POST
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Mostrar la respuesta
        print(response.text)

    def reject_capitulation(self, capitulation_id):
        capitulation = self.db.query(CapitulationModel).filter(CapitulationModel.id == capitulation_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == capitulation.user_rut).first()
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 3).first()
        expense_type = self.db.query(ExpenseTypeModel).filter(ExpenseTypeModel.id == capitulation.expense_type_id).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == capitulation.branch_office_id).first()

        phone = user.phone  # Ej: '912345678'
        full_name = user.full_name
        capitulation_id = capitulation.id
        amount_value = capitulation.amount
        capitulation_date_value = capitulation.added_date.strftime('%d-%m-%Y') if capitulation.added_date else 'N/A'
        expense_type_name = expense_type.expense_type
        branch_office_name = branch_office.branch_office
        rejection_reason = capitulation.why_was_rejected

        # URL de la API
        url = 'https://graph.facebook.com/v20.0/101066132689690/messages'

        token = os.getenv("LIBREDTE_TOKEN")

        # Cabeceras
        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            phone = "56" + phone_str
        else:
            phone = phone_str

        # Payload en formato JSON
        payload = {
            "messaging_product": "whatsapp",
            "to": f"{phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": full_name},
                            {"type": "text", "text": capitulation_id},
                            {"type": "text", "text": amount_value},
                            {"type": "text", "text": capitulation_date_value},
                            {"type": "text", "text": expense_type_name},
                            {"type": "text", "text": branch_office_name},
                            {"type": "text", "text": rejection_reason},
                        ]
                    }
                ]
            }
        }

        # Enviar la solicitud POST
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Mostrar la respuesta
        print(response.text)
    
    def resend(self, dte_id, phone):
        dte_data = self.db.query(DteModel).filter(DteModel.id == dte_id).first()
        if not dte_data:
            return {"status": "error", "message": "DTE no encontrado"}

        # Boletas (SimpleFactura v2 + Klap): plantilla envio_dte_v3
        if int(dte_data.dte_type_id or 0) == 39:
            print("[resend] Boleta → send_v2_invoice (envio_dte_v3 / Klap)", flush=True)
            return self.send_v2_invoice(dte_data, dte_data.rut, phone_override=phone)

        # Facturas: plantilla envio_dte + pago LibreDTE
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        issued_dte_info_url = (
            "https://libredte.cl/api/dte/dte_emitidos/info/"
            + str(dte_data.dte_type_id)
            + "/"
            + str(dte_data.folio)
            + "/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"
        )
        issued_dte_info_response = requests.get(
            issued_dte_info_url,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=45,
        )
        libredte_body = (issued_dte_info_response.text or "").strip()
        if issued_dte_info_response.status_code != 200 or "No existe el documento" in libredte_body:
            return {
                "status": "error",
                "message": "Factura no encontrada en LibreDTE para reenvío WhatsApp",
                "whatsapp_accepted": "rejected",
            }

        whatsapp_template = _whatsapp_template_libredte(self.db)
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte_data.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()

        pdf_url, pdf_error = _whatsapp_document_pdf_url(self.db, dte_data)
        if pdf_error:
            return {**pdf_error, "whatsapp_accepted": "rejected"}
        image = pdf_url

        print(issued_dte_info_response.text)
        issued_date_for_payment_link = _libredte_issue_date_from_emitido_info(
            issued_dte_info_response, getattr(dte_data, "added_date", None)
        )

        url_data = (
            str(dte_data.dte_type_id)
            + "/"
            + str(dte_data.folio)
            + "/76063822/"
            + issued_date_for_payment_link
            + "/"
            + str(dte_data.total)
        )

        if not whatsapp_template or not whatsapp_template.title:
            return {
                "status": "error",
                "message": f"Plantilla WhatsApp {WHATSAPP_TEMPLATE_LIBREDTE_TITLE} no encontrada",
                "whatsapp_accepted": "rejected",
            }
        if not branch_office:
            return {"status": "error", "message": "Sucursal no encontrada", "whatsapp_accepted": "rejected"}
        if not user:
            return {"status": "error", "message": "Supervisor no encontrado", "whatsapp_accepted": "rejected"}

        token_error = validate_whatsapp_access_token()
        if token_error:
            return token_error

        token = whatsapp_access_token()
        graph_url = whatsapp_graph_messages_url()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        added_date_str = dte_data.added_date.strftime('%d-%m-%Y')
        dte_type = "factura"

        phone_str = str(phone).strip()
        customer_phone = phone_str if phone_str.startswith("56") else "56" + phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": f"{customer_phone}",
            "type": "template",
            "template": {
                "name": whatsapp_template.title,
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {
                                    "link": image,
                                    "filename": f"{dte_data.folio}.pdf",
                                },
                            }
                        ],
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(dte_type)},
                            {"type": "text", "text": str(dte_data.folio)},
                            {"type": "text", "text": added_date_str},
                            {"type": "text", "text": str(dte_data.total)},
                            {"type": "text", "text": branch_office.branch_office},
                            {"type": "text", "text": user.full_name},
                            {"type": "text", "text": user.phone},
                            {"type": "text", "text": user.email},
                        ],
                    },
                    {
                        "type": "button",
                        "index": "0",
                        "sub_type": "url",
                        "parameters": [{"type": "text", "text": url_data}],
                    },
                ],
            },
        }
        print(
            f"[resend] factura folio={dte_data.folio} template={whatsapp_template.title} pdf={image}",
            flush=True,
        )
        print(payload, flush=True)
        response = requests.post(graph_url, json=payload, headers=headers, timeout=45)
        print(response.text, flush=True)
        return _parse_whatsapp_graph_response(response)

    def dtes_data(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-05')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                issued_dte_collection_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                issued_dte_collection_response = requests.get(issued_dte_collection_url, headers=headers)
                print(issued_dte_collection_response.text)

                data = issued_dte_collection_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        payment_detail_dict = json.loads(data["datos"])
                        authorization_code = payment_detail_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data2(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-06')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                issued_dte_collection_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                issued_dte_collection_response = requests.get(issued_dte_collection_url, headers=headers)
                print(issued_dte_collection_response.text)

                data = issued_dte_collection_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        payment_detail_dict = json.loads(data["datos"])
                        authorization_code = payment_detail_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data3(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-04')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                issued_dte_collection_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                issued_dte_collection_response = requests.get(issued_dte_collection_url, headers=headers)
                print(issued_dte_collection_response.text)

                data = issued_dte_collection_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        payment_detail_dict = json.loads(data["datos"])
                        authorization_code = payment_detail_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")


    def dtes_data4(self):
        dtes = (
            self.db.query(DteModel)
            .filter(DteModel.status_id == 5)
            .filter(DteModel.dte_type_id == 39)
            .filter(DteModel.payment_type_id == 2)
            .filter(DteModel.dte_version_id == 1)
            .filter(DteModel.period == '2025-03')
            .all()
        )

        for dte in dtes:
            try:
                print(dte.folio)

                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

                issued_dte_collection_url = f"https://libredte.cl/api/dte/dte_emitidos/cobro/{dte.dte_type_id}/{dte.folio}/76063822?getXML=0&getDetalle=0&getDatosDte=0&getTed=0&getResolucion=0&getEmailEnviados=0&getLinks=0&getReceptor=0&getSucursal=0&getUsuario=0"

                headers = {
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json"
                }

                issued_dte_collection_response = requests.get(issued_dte_collection_url, headers=headers)
                print(issued_dte_collection_response.text)

                data = issued_dte_collection_response.json()

                if isinstance(data, dict):
                    if data.get("pagado") is not None and data.get("datos") is not None:
                        payment_detail_dict = json.loads(data["datos"])
                        authorization_code = payment_detail_dict["detailOutput"]["authorizationCode"]

                        print("Authorization Code:", authorization_code)

                        dte_detail = (
                            self.db.query(DteModel)
                            .filter(DteModel.status_id == dte.status_id)
                            .filter(DteModel.dte_type_id == dte.dte_type_id)
                            .filter(DteModel.dte_version_id == dte.dte_version_id)
                            .filter(DteModel.period == dte.period)
                            .first()
                        )

                        dte_detail.payment_date = data["pagado"]
                        dte_detail.comment = f'Código de autorización: {authorization_code}'
                        dte_detail.payment_comment = f'Código de autorización: {authorization_code}'
                        self.db.commit()
                    else:
                        print("Datos o pagado no disponibles para el DTE con folio", dte.folio)
                else:
                    print(f"Respuesta inesperada para DTE folio {dte.folio}: {data}")
            except Exception as e:
                print(f"❌ Error procesando DTE folio {dte.folio}: {e}")

    def cron_to_resend(self):
        dtes = self.db.query(DteModel).filter(DteModel.status_id == 4).filter(DteModel.dte_type_id == 39).filter(DteModel.dte_version_id == 1).filter(DteModel.period == '2025-08').all()

        for dte in dtes:
            print(dte.folio)
            
            customer = self.db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
            
            self.resend(dte.id, customer.phone)

    def notify_payment(self, folio):
        dte = self.db.query(DteModel).filter(DteModel.folio == folio).first()
        customer = self.db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte.branch_office_id).first()
        user = self.db.query(UserModel).filter(UserModel.rut == branch_office.principal_supervisor).first()
        phone = user.phone
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 2).first()

        token = os.getenv("LIBREDTE_TOKEN")

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer_phone}",
                    "type": "template",
                    "template": {
                        "name": whatsapp_template.title,
                        "language": {
                            "code": "es"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": user.full_name},
                                    {"type": "text", "text": str(folio)},
                                    {"type": "text", "text": str(dte.rut)},
                                    {"type": "text", "text": customer.customer},
                                    {"type": "text", "text": branch_office.branch_office},
                                    {"type": "text", "text": str(dte.total)},
                                    {"type": "text", "text": datetime.strptime(dte.payment_date, '%Y-%m-%d').strftime('%d-%m-%Y')},
                                ]
                            }
                        ]
                    }
                }

        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)


    def status_capitulation(self, rut, amount):
        user = self.db.query(UserModel).filter(UserModel.rut == rut).first()
        phone = user.phone
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 5).first()

        token = os.getenv("LIBREDTE_TOKEN")

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        phone_str = str(phone).strip()
        if not phone_str.startswith("56"):
            customer_phone = "56" + phone_str
        else:
            customer_phone = phone_str

        payload = {
                    "messaging_product": "whatsapp",
                    "to": f"{customer_phone}",
                    "type": "template",
                    "template": {
                        "name": whatsapp_template.title,
                        "language": {
                            "code": "es"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": user.full_name},
                                    {"type": "text", "text": amount},
                                    {"type": "text", "text": 'Pagadas'},
                                ]
                            }
                        ]
                    }
                }

        print(payload)
        response = requests.post(url, json=payload, headers=headers)

        print(response.text)

    def rejected_deposit_notification(self, deposit_data, deposit_id):
        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 6).first()

        """
        Envía notificación WhatsApp cuando un depósito es rechazado
        """
        try:
            # Obtener datos de la sucursal
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == deposit_data.branch_office_id
            ).first()
            
            if not branch_office:
                print(f"No se encontró la sucursal con ID: {deposit_data.branch_office_id}")
                return
            
            # Obtener datos del supervisor principal
            user = self.db.query(UserModel).filter(
                UserModel.rut == branch_office.principal_supervisor
            ).first()
            
            if not user:
                print(f"No se encontró el supervisor principal con RUT: {branch_office.principal_supervisor}")
                return

            # Token de WhatsApp
            token = os.getenv("LIBREDTE_TOKEN")
            url = "https://graph.facebook.com/v20.0/101066132689690/messages"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Formatear fecha de depósito
            deposit_date_formatted = 'No especificada'
            if hasattr(deposit_data, 'deposit_date') and deposit_data.deposit_date:
                try:
                    # Si viene en formato DD-MM-YYYY, mantenerlo
                    if '-' in str(deposit_data.deposit_date) and len(str(deposit_data.deposit_date).split('-')) == 3:
                        deposit_date_formatted = str(deposit_data.deposit_date)
                    else:
                        # Si viene en otro formato, intentar convertir
                        from datetime import datetime
                        date_obj = datetime.strptime(str(deposit_data.deposit_date), '%Y-%m-%d')
                        deposit_date_formatted = date_obj.strftime('%d-%m-%Y')
                except:
                    deposit_date_formatted = str(deposit_data.deposit_date)

            # Obtener motivo del rechazo
            rejection_reason = "Motivo no especificado"
            if hasattr(deposit_data, 'reject_reason_id') and deposit_data.reject_reason_id:
                if deposit_data.reject_reason_id == 1:
                    rejection_reason = "Fotografía no corresponde"
                elif deposit_data.reject_reason_id == 2:
                    rejection_reason = "Monto no cuadra"
                else:
                    rejection_reason = f"Razón ID: {deposit_data.reject_reason_id}"

            payload = {
                "messaging_product": "whatsapp",
                "to": user.phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {"code": "es"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": user.full_name},
                                {"type": "text", "text": str(deposit_id)},
                                {"type": "text", "text": branch_office.branch_office},
                                {"type": "text", "text": deposit_date_formatted},
                                {"type": "text", "text": rejection_reason},
                            ]
                        }
                    ]
                }
            }

            print("Enviando notificación de depósito rechazado...")
            print(payload)
            
            response = requests.post(url, json=payload, headers=headers)
            print(f"Respuesta WhatsApp: {response.text}")
            
            return response.json()
            
        except Exception as e:
            print(f"Error al enviar notificación WhatsApp: {str(e)}")
            return None

    def _normalize_whatsapp_phone_cl(self, phone: str) -> str:
        digits = "".join(c for c in str(phone).strip() if c.isdigit())
        if not digits:
            raise ValueError("Teléfono vacío")
        if digits.startswith("56"):
            return digits
        return "56" + digits

    def send_folio_low_stock_alerts(self, segment_id: int, available: int) -> list[dict]:
        whatsapp_recipient_phone_numbers = [
            "569964423773",
            "56990202757",
            "56976357193",
        ]

        whatsapp_template = self.db.query(WhatsappTemplateModel).filter(WhatsappTemplateModel.id == 7).first()

        token = os.getenv('LIBREDTE_TOKEN')

        url = "https://graph.facebook.com/v20.0/101066132689690/messages"

        headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

        segment_number_text = str(segment_id)
        available_folio_count_text = str(int(available))
        outcomes: list[dict] = []
        if not token:
            return [{"to": r, "ok": False, "error": "LIBREDTE_TOKEN no configurado"} for r in whatsapp_recipient_phone_numbers]
        if not whatsapp_template or not whatsapp_template.title:
            return [{"to": r, "ok": False, "error": "Plantilla WhatsApp id=7 no encontrada o sin title"} for r in whatsapp_recipient_phone_numbers]
        for raw in whatsapp_recipient_phone_numbers:
            try:
                to_phone = self._normalize_whatsapp_phone_cl(raw)
            except ValueError as e:
                outcomes.append({"to": raw, "ok": False, "error": str(e)})
                continue
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "template",
                "template": {
                    "name": whatsapp_template.title,
                    "language": {
                        "code": "es"
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": segment_number_text},
                                {"type": "text", "text": available_folio_count_text},
                            ]
                        }
                    ]
                }
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                try:
                    resp_json = response.json()
                except Exception:
                    resp_json = {"raw": response.text}
                outcomes.append({
                    "to": to_phone,
                    "http_status": response.status_code,
                    "ok": response.status_code == 200,
                    "response": resp_json,
                    "template": whatsapp_template.title,
                })
            except Exception as e:
                outcomes.append({"to": to_phone, "ok": False, "error": str(e)})
        return outcomes