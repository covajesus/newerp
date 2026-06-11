"""
Proxy and webhooks for Klap Order API (Boleta2 / Factura2).

Docs: https://api.pasarela.multicaja.cl/docs/ecommerce_api_payments
"""
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backend.classes.dte_payment_data_class import DtePaymentDataClass
from app.backend.classes.klap_class import KlapClass, normalize_gateway_order_id
from app.backend.classes.payments_env import payments_env
from app.backend.db.database import get_db
from app.backend.db.models import CustomerModel, DteModel

klap_payments = APIRouter(prefix="/payments", tags=["Payments"])


class KlapUserModel(BaseModel):
    email: Optional[str] = None
    rut: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None


class KlapAmountDetailsModel(BaseModel):
    subtotal: Optional[float] = None
    fee: Optional[float] = None
    tax: Optional[float] = None


class KlapAmountModel(BaseModel):
    currency: str = "CLP"
    total: float
    details: Optional[KlapAmountDetailsModel] = None


class KlapItemModel(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    price: Optional[float] = None
    unit_price: Optional[float] = None
    quantity: Optional[float] = None


class KlapUrlModel(BaseModel):
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class KlapWebhookModel(BaseModel):
    webhook_validation: Optional[str] = None
    webhook_confirm: Optional[str] = None
    webhook_reject: Optional[str] = None


class KlapCreateOrderRequest(BaseModel):
    reference_id: str = Field(..., max_length=100)
    user: Optional[KlapUserModel] = None
    amount: KlapAmountModel
    methods: list[str]
    items: Optional[list[KlapItemModel]] = None
    description: str
    customs: Optional[list[dict[str, str]]] = None
    urls: Optional[KlapUrlModel] = None
    webhooks: Optional[KlapWebhookModel] = None


class KlapPaymentReturnRequest(BaseModel):
    reference_id: Optional[str] = Field(None, alias="referenceId")
    order_id: Optional[str] = Field(None, alias="orderId")

    model_config = {"populate_by_name": True}


class KlapRefundRequest(BaseModel):
    reference_id: Optional[str] = None
    amount: Optional[float] = None


@klap_payments.get("/return")
def klap_return_redirect(
    referenceId: Optional[str] = None,
    orderId: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Return URL alternativa en el backend: guarda y redirige al frontend público.
    """
    frontend_base = payments_env(
        "PAYMENTS_RETURN_FRONTEND_URL",
        "KLAP_RETURN_FRONTEND_URL",
        "https://intrajis.com/payments/success",
    ).rstrip("/")
    if referenceId and orderId:
        DtePaymentDataClass(db).record_payment_return(referenceId, orderId, source="return_redirect")
    from urllib.parse import urlencode

    qs = urlencode({"referenceId": referenceId or "", "orderId": orderId or ""})
    return RedirectResponse(url=f"{frontend_base}?{qs}", status_code=302)


@klap_payments.post("/payment-return")
def register_payment_return(body: KlapPaymentReturnRequest, db: Session = Depends(get_db)):
    """Registra retorno Klap (público, sin sesión)."""
    ref = body.reference_id
    oid = body.order_id
    if not ref or not oid:
        raise HTTPException(status_code=400, detail="referenceId y orderId son obligatorios")
    result = DtePaymentDataClass(db).record_payment_return(ref, oid, source="frontend_return")
    if result.get("status") != "success":
        raise HTTPException(status_code=502, detail=result.get("message") or "Error al registrar pago")
    return {"message": result}


@klap_payments.get("/payment-data/{order_id}")
def get_payment_data(order_id: str, db: Session = Depends(get_db)):
    """Consulta datos guardados de un pago Klap (público)."""
    data = DtePaymentDataClass(db).get_by_order_id(order_id)
    if not data:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return {"message": data}


@klap_payments.get("/pay/{order_id:path}")
def pay_redirect(order_id: str):
    """
    Redirección pública al checkout Klap.
    Plantilla WhatsApp envio_dte_v2: https://intrajisbackend.com/api/payments/pay/ + variable {{1}}
    ({{1}} = order_id de Klap; no debe quedar {{1}} literal en la URL final).
    """
    normalized = normalize_gateway_order_id(order_id)
    if not normalized:
        raise HTTPException(status_code=400, detail="order_id Klap inválido")
    redirect_url = KlapClass().redirect_url_for_order(normalized)
    if not redirect_url:
        raise HTTPException(
            status_code=404,
            detail="Orden Klap no encontrada o sin URL de pago",
        )
    return RedirectResponse(url=redirect_url, status_code=302)


@klap_payments.get("/dtes/{dte_id}/payment-url")
def dte_payment_url(dte_id: int, db: Session = Depends(get_db)):
    """Genera enlace de pago Klap para un DTE abonado v2 (copiar enlace)."""
    dte = db.query(DteModel).filter(DteModel.id == dte_id).first()
    if not dte:
        raise HTTPException(status_code=404, detail="DTE no encontrado")
    customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    result = KlapClass().payment_url_for_dte(dte, customer)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail=result.get("message") or "No se pudo crear orden Klap",
        )
    return {"message": result}


@klap_payments.post("/orders")
def create_order(body: KlapCreateOrderRequest):
    payload = body.model_dump(exclude_none=True)
    data = KlapClass().create_order(payload)
    return {"message": data}


@klap_payments.get("/orders/{order_id}")
def get_order(order_id: str):
    data = KlapClass().get_order(order_id)
    return {"message": data}


@klap_payments.post("/orders/{order_id}/refund")
def refund_order(order_id: str, body: Optional[KlapRefundRequest] = Body(default=None)):
    payload = body.model_dump(exclude_none=True) if body else {}
    data = KlapClass().refund_order(order_id, payload)
    return {"message": data}


@klap_payments.get("/transactions")
def list_transactions(
    reference_id: Optional[str] = None,
    order_id: Optional[str] = None,
    mc_code: Optional[str] = None,
):
    data = KlapClass().list_transactions(
        reference_id=reference_id,
        order_id=order_id,
        mc_code=mc_code,
    )
    return {"message": data}


@klap_payments.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    data = KlapClass().get_transaction(transaction_id)
    return {"message": data}


@klap_payments.post("/webhooks/validation")
async def webhook_validation(request: Request):
    payload = await _read_json(request)
    # TODO: validar firma / reglas de negocio antes de aprobar la orden
    return {"status": "ok", "payload": payload}


@klap_payments.post("/webhooks/confirm")
async def webhook_confirm(request: Request, db: Session = Depends(get_db)):
    payload = await _read_json(request)
    reference_id = (
        payload.get("reference_id")
        or payload.get("referenceId")
        or (payload.get("order") or {}).get("reference_id")
    )
    order_id = payload.get("order_id") or payload.get("orderId")
    if reference_id and order_id:
        DtePaymentDataClass(db).record_payment_return(
            str(reference_id),
            str(order_id),
            source="webhook_confirm",
        )
    return {"status": "ok", "payload": payload}


@klap_payments.post("/webhooks/reject")
async def webhook_reject(request: Request, db: Session = Depends(get_db)):
    payload = await _read_json(request)
    reference_id = payload.get("reference_id") or payload.get("referenceId")
    order_id = payload.get("order_id") or payload.get("orderId")
    if reference_id and order_id:
        DtePaymentDataClass(db).record_payment_return(
            str(reference_id),
            str(order_id),
            source="webhook_reject",
        )
    return {"status": "ok", "payload": payload}


async def _read_json(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}
