"""
Incoming webhook handlers for the Klap / Multicaja payment gateway.

Docs: https://developers.klap.cl/webhooks
OpenAPI: https://api.pasarela.multicaja.cl/docs/swagger/ecommerce_api_payments.yml
"""
from __future__ import annotations

import secrets
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.backend.classes.payments_env import payments_env


def expected_webhook_api_key() -> str:
    return payments_env("PAYMENTS_API_KEY", legacy_name="KLAP_API_KEY").strip()


def incoming_api_key(request: Request) -> str | None:
    for header_name in ("apikey", "x-api-key"):
        value = request.headers.get(header_name)
        if value and str(value).strip():
            return str(value).strip()
    return None


def api_keys_match(provided: str | None, expected: str) -> bool:
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided.strip(), expected.strip())


def require_webhook_api_key(request: Request) -> None:
    """
    Klap sends header `apikey` on confirm/reject notifications.
    Invalid key -> 403001 (required for production certification).
    """
    expected = expected_webhook_api_key()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="PAYMENTS_API_KEY is not configured on the server.",
        )

    provided = incoming_api_key(request)
    if not api_keys_match(provided, expected):
        raise HTTPException(
            status_code=403,
            detail={"code": "403001", "message": "The apikey is not valid"},
        )


def log_webhook_apikey_status(request: Request) -> dict[str, str | bool]:
    """Log-only apikey check for webhook_validation (must not block order creation)."""
    expected = expected_webhook_api_key()
    provided = incoming_api_key(request) or ""
    return {
        "apikey_header_present": bool(provided),
        "apikey_match": api_keys_match(provided, expected) if provided and expected else False,
    }


def webhook_ok_response(*, source: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"status": "ok", "source": source}
    body.update(extra)
    return body


def extract_payment_ids(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    if not isinstance(payload, dict):
        return None, None

    order = payload.get("order")
    if isinstance(order, dict):
        ref = order.get("reference_id") or order.get("referenceId")
        oid = order.get("order_id") or order.get("orderId")
        if ref and oid:
            return str(ref).strip(), str(oid).strip()

    data = payload.get("data")
    if isinstance(data, dict):
        ref = data.get("reference_id") or data.get("referenceId")
        oid = data.get("order_id") or data.get("orderId")
        if ref and oid:
            return str(ref).strip(), str(oid).strip()

    ref = payload.get("reference_id") or payload.get("referenceId")
    oid = payload.get("order_id") or payload.get("orderId")
    if ref and oid:
        return str(ref).strip(), str(oid).strip()
    return None, None


def validate_order_webhook_payload(payload: dict[str, Any]) -> None:
    """
    webhook_validation runs when Klap creates an order.
    Reject invalid orders before checkout is offered to the payer.
    """
    reference_id = payload.get("reference_id") or payload.get("referenceId")
    if not reference_id or not str(reference_id).strip():
        raise HTTPException(
            status_code=400,
            detail={"code": "400003", "message": "reference_id is required"},
        )

    amount = payload.get("amount")
    if not isinstance(amount, dict):
        raise HTTPException(
            status_code=400,
            detail={"code": "400011", "message": "amount is required"},
        )

    total = amount.get("total")
    try:
        total_value = float(total)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail={"code": "400010", "message": "amount.total is invalid"},
        ) from None

    if total_value < 50:
        raise HTTPException(
            status_code=400,
            detail={"code": "400010", "message": "amount.total must be at least 50"},
        )

    methods = payload.get("methods")
    if not isinstance(methods, list) or not methods:
        raise HTTPException(
            status_code=400,
            detail={"code": "400007", "message": "Payment methods list is invalid"},
        )

    currency = str(amount.get("currency") or "").upper()
    if currency and currency != "CLP":
        raise HTTPException(
            status_code=400,
            detail={"code": "400010", "message": "amount.currency must be CLP"},
        )


def certification_debug_response(request: Request) -> dict[str, str]:
    """
    Fields useful when Klap asks for evidence that header apikey matches
    the key configured on the merchant side (production certification).
    """
    expected = expected_webhook_api_key()
    provided = incoming_api_key(request) or ""
    return {
        "header_apikey_received": provided,
        "merchant_apikey_expected": expected,
        "apikey_match": str(api_keys_match(provided, expected)).lower(),
    }
