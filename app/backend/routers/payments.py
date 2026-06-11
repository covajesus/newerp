"""
Payment gateway proxy and webhooks (Boleta2 / Factura2).

Docs: https://api.pasarela.multicaja.cl/docs/ecommerce_api_payments
"""
from typing import Any, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backend.classes.dte_payment_data_class import DtePaymentDataClass
from app.backend.classes.payment_gateway_class import (
    PaymentGatewayClass,
    normalize_gateway_order_id,
)
from app.backend.classes.payment_webhook_class import (
    certification_debug_response,
    extract_payment_ids,
    incoming_api_key,
    require_webhook_api_key,
    validate_order_webhook_payload,
    verify_webhook_api_key_if_present,
    webhook_ok_response,
)
from app.backend.classes.payments_env import payments_env
from app.backend.db.database import get_db
from app.backend.db.models import CustomerModel, DteModel

payments = APIRouter(prefix="/payments", tags=["Payments"])


class PaymentUserModel(BaseModel):
    email: Optional[str] = None
    rut: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address_line: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None


class PaymentAmountDetailsModel(BaseModel):
    subtotal: Optional[float] = None
    fee: Optional[float] = None
    tax: Optional[float] = None


class PaymentAmountModel(BaseModel):
    currency: str = "CLP"
    total: float
    details: Optional[PaymentAmountDetailsModel] = None


class PaymentItemModel(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    price: Optional[float] = None
    unit_price: Optional[float] = None
    quantity: Optional[float] = None


class PaymentUrlModel(BaseModel):
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentWebhookModel(BaseModel):
    webhook_validation: Optional[str] = None
    webhook_confirm: Optional[str] = None
    webhook_reject: Optional[str] = None


class PaymentCreateOrderRequest(BaseModel):
    reference_id: str = Field(..., max_length=100)
    user: Optional[PaymentUserModel] = None
    amount: PaymentAmountModel
    methods: list[str]
    items: Optional[list[PaymentItemModel]] = None
    description: str
    customs: Optional[list[dict[str, str]]] = None
    urls: Optional[PaymentUrlModel] = None
    webhooks: Optional[PaymentWebhookModel] = None


class PaymentReturnRequest(BaseModel):
    reference_id: Optional[str] = Field(None, alias="referenceId")
    order_id: Optional[str] = Field(None, alias="orderId")

    model_config = {"populate_by_name": True}


class PaymentRefundRequest(BaseModel):
    reference_id: Optional[str] = None
    amount: Optional[float] = None


@payments.get("/return")
def payment_return_redirect(
    referenceId: Optional[str] = None,
    orderId: Optional[str] = None,
    db: Session = Depends(get_db),
):
    frontend_base = payments_env(
        "PAYMENTS_RETURN_FRONTEND_URL",
        default="https://intrajis.com/payments/success",
    ).rstrip("/")
    if referenceId and orderId:
        DtePaymentDataClass(db).record_payment_return(
            referenceId, orderId, source="return_redirect"
        )
    qs = urlencode({"referenceId": referenceId or "", "orderId": orderId or ""})
    return RedirectResponse(url=f"{frontend_base}?{qs}", status_code=302)


@payments.get("/cancel")
def payment_cancel_redirect(
    referenceId: Optional[str] = None,
    orderId: Optional[str] = None,
    db: Session = Depends(get_db),
):
    frontend_base = payments_env(
        "PAYMENTS_CANCEL_FRONTEND_URL",
        default="https://intrajis.com/payments/rejected",
    ).rstrip("/")
    if referenceId and orderId:
        DtePaymentDataClass(db).record_payment_return(
            referenceId, orderId, source="cancel_redirect"
        )
    qs = urlencode({"referenceId": referenceId or "", "orderId": orderId or ""})
    return RedirectResponse(url=f"{frontend_base}?{qs}", status_code=302)


@payments.post("/payment-return")
def register_payment_return(body: PaymentReturnRequest, db: Session = Depends(get_db)):
    ref = body.reference_id
    oid = body.order_id
    if not ref or not oid:
        raise HTTPException(status_code=400, detail="referenceId and orderId are required")
    result = DtePaymentDataClass(db).record_payment_return(ref, oid, source="frontend_return")
    if result.get("status") != "success":
        raise HTTPException(status_code=502, detail=result.get("message") or "Failed to register payment")
    return {"message": result}


@payments.get("/payment-data/{order_id}")
def get_payment_data(order_id: str, db: Session = Depends(get_db)):
    data = DtePaymentDataClass(db).get_by_order_id(order_id)
    if not data:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"message": data}


@payments.get("/pay/{order_id:path}")
def pay_redirect(order_id: str):
    return _pay_redirect_to_gateway(order_id)


def _pay_redirect_to_gateway(order_id: str):
    """
    Public redirect to payment gateway checkout.
    WhatsApp template envio_dte_v3: https://intrajisbackend.com/api/payments/pay/{{1}}
    """
    normalized = normalize_gateway_order_id(order_id)
    if not normalized:
        raise HTTPException(status_code=400, detail="Invalid payment order_id")
    redirect_url = PaymentGatewayClass().redirect_url_for_order(normalized)
    if not redirect_url:
        raise HTTPException(
            status_code=404,
            detail="Payment order not found or missing checkout URL",
        )
    return RedirectResponse(url=redirect_url, status_code=302)


@payments.get("/dtes/{dte_id}/payment-url")
def dte_payment_url(dte_id: int, db: Session = Depends(get_db)):
    dte = db.query(DteModel).filter(DteModel.id == dte_id).first()
    if not dte:
        raise HTTPException(status_code=404, detail="DTE not found")
    customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    result = PaymentGatewayClass().payment_url_for_dte(dte, customer)
    if result.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail=result.get("message") or "Failed to create payment order",
        )
    return {"message": result}


@payments.post("/orders")
def create_order(body: PaymentCreateOrderRequest):
    payload = body.model_dump(exclude_none=True)
    data = PaymentGatewayClass().create_order(payload)
    return {"message": data}


@payments.get("/orders/{order_id}")
def get_order(order_id: str):
    data = PaymentGatewayClass().get_order(order_id)
    return {"message": data}


@payments.post("/orders/{order_id}/refund")
def refund_order(order_id: str, body: Optional[PaymentRefundRequest] = Body(default=None)):
    payload = body.model_dump(exclude_none=True) if body else {}
    data = PaymentGatewayClass().refund_order(order_id, payload)
    return {"message": data}


@payments.get("/transactions")
def list_transactions(
    reference_id: Optional[str] = None,
    order_id: Optional[str] = None,
    mc_code: Optional[str] = None,
):
    data = PaymentGatewayClass().list_transactions(
        reference_id=reference_id,
        order_id=order_id,
        mc_code=mc_code,
    )
    return {"message": data}


@payments.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    data = PaymentGatewayClass().get_transaction(transaction_id)
    return {"message": data}


@payments.post("/webhooks/validation")
async def webhook_validation(request: Request):
    """
    Called by Klap when an order is created (before checkout).
    Validates the order payload; apikey header is checked when present.
    """
    payload = await _read_json(request)
    apikey_verified = verify_webhook_api_key_if_present(request)
    reference_id = payload.get("reference_id") or payload.get("referenceId")
    print(
        f"[payments] webhook_validation ref={reference_id} "
        f"apikey_header={'yes' if incoming_api_key(request) else 'no'} "
        f"verified={apikey_verified}",
        flush=True,
    )
    validate_order_webhook_payload(payload)

    response = webhook_ok_response(
        source="webhook_validation",
        apikey_verified=apikey_verified,
        reference_id=reference_id,
    )
    if _webhook_debug_enabled():
        response.update(certification_debug_response(request))
    return response


@payments.post("/webhooks/confirm")
async def webhook_confirm(request: Request, db: Session = Depends(get_db)):
    """Mandatory Klap webhook: payment completed."""
    require_webhook_api_key(request)
    payload = await _read_json(request)
    reference_id, order_id = _resolve_payment_ids(payload)
    dte_updated = False
    if reference_id and order_id:
        result = DtePaymentDataClass(db).record_payment_return(
            reference_id,
            order_id,
            source="webhook_confirm",
        )
        dte_updated = bool(result.get("dte_updated"))
        print(
            f"[payments] webhook_confirm ref={reference_id} order={order_id} "
            f"dte_updated={dte_updated}",
            flush=True,
        )
    else:
        print(f"[payments] webhook_confirm missing ids payload={payload}", flush=True)

    response = webhook_ok_response(
        source="webhook_confirm",
        apikey_verified=True,
        dte_updated=dte_updated,
    )
    if _webhook_debug_enabled():
        response.update(certification_debug_response(request))
    return response


@payments.post("/webhooks/reject")
async def webhook_reject(request: Request, db: Session = Depends(get_db)):
    """Klap webhook: payment failed, canceled or expired."""
    require_webhook_api_key(request)
    payload = await _read_json(request)
    reference_id, order_id = _resolve_payment_ids(payload)
    if reference_id and order_id:
        DtePaymentDataClass(db).record_payment_return(
            reference_id,
            order_id,
            source="webhook_reject",
        )
        print(
            f"[payments] webhook_reject ref={reference_id} order={order_id}",
            flush=True,
        )
    else:
        print(f"[payments] webhook_reject missing ids payload={payload}", flush=True)

    response = webhook_ok_response(
        source="webhook_reject",
        apikey_verified=True,
    )
    if _webhook_debug_enabled():
        response.update(certification_debug_response(request))
    return response


def _webhook_debug_enabled() -> bool:
    return payments_env("PAYMENTS_WEBHOOK_DEBUG", default="false").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _resolve_payment_ids(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    reference_id, order_id = extract_payment_ids(payload)
    if order_id and not reference_id:
        try:
            order = PaymentGatewayClass().get_order(order_id)
            if isinstance(order, dict):
                reference_id = order.get("reference_id") or order.get("referenceId")
                if reference_id:
                    reference_id = str(reference_id).strip()
        except HTTPException:
            pass
    return reference_id, order_id


async def _read_json(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}
