"""
HTTP client for the e-commerce payment gateway (Multicaja pasarela).

Docs: https://api.pasarela.multicaja.cl/docs/ecommerce_api_payments
Auth: header `apikey`.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, urlencode

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.backend.classes.payments_env import payments_env
from app.backend.db.models import CustomerModel, DteModel, DtePaymentDataModel

_GATEWAY_ORDER_ID_RE = re.compile(r"^[0-9][0-9A-Za-z]{20,}$")
_UNIQUE_ONLY_METHODS = frozenset({"*", "tarjetas_api"})
_DEFAULT_METHOD_EXPIRATION_METHODS = ("tarjetas", "sodexo", "edenred")
_RETRY_ORDER_STATUSES = frozenset(
    {"canceled", "cancelled", "rejected", "expired", "failed", "refunded", "refund"}
)


def normalize_payment_methods(raw: str | None) -> list[str]:
    """
    Parse PAYMENTS_METHODS env value for gateway POST /orders.

    Gateway error 400006: methods marked (U) such as * or tarjetas_api must be alone.
    Duplicate entries in the list also trigger 400006.
    """
    ordered: list[str] = []
    seen: set[str] = set()
    for part in (raw or "tarjetas").replace(";", ",").split(","):
        method = part.strip().lower()
        if not method or method in seen:
            continue
        seen.add(method)
        ordered.append(method)

    if not ordered:
        return ["tarjetas"]

    unique_hits = [m for m in ordered if m in _UNIQUE_ONLY_METHODS]
    if unique_hits:
        return [unique_hits[0]]

    return ordered


def _methods_for_expiration_customs(methods: list[str]) -> list[str]:
    """Gateway expects tarjetas_expiration_minutes etc., not *_expiration_minutes."""
    if methods == ["*"]:
        return list(_DEFAULT_METHOD_EXPIRATION_METHODS)
    return methods


def normalize_gateway_order_id(raw: str) -> str:
    """
    Clean order_id received at /payments/pay/{order_id}.
    Meta sometimes leaves {{1}} literal in the URL when the template is misconfigured.
    """
    cleaned = unquote((raw or "").strip())
    for junk in ("{{1}}", "{{ 1 }}", "%7B%7B1%7D%7D", "{1}"):
        cleaned = cleaned.replace(junk, "")
    cleaned = cleaned.strip().strip("/")
    if cleaned and _GATEWAY_ORDER_ID_RE.match(cleaned):
        return cleaned
    match = re.search(r"([0-9][0-9A-Za-z]{20,})", cleaned)
    return match.group(1) if match else cleaned


class PaymentGatewayClass:
    def __init__(self):
        self.api_key = payments_env("PAYMENTS_API_KEY")
        self.base_url = payments_env(
            "PAYMENTS_API_BASE_URL",
            default="https://api.pasarela.multicaja.cl",
        ).rstrip("/")
        self.return_url = payments_env(
            "PAYMENTS_RETURN_URL",
            default="https://intrajisbackend.com/api/payments/return",
        )
        self.cancel_url = payments_env(
            "PAYMENTS_CANCEL_URL",
            default="https://intrajisbackend.com/api/payments/cancel",
        )
        self.webhook_confirm_url = payments_env(
            "PAYMENTS_WEBHOOK_CONFIRM_URL",
            default="https://intrajisbackend.com/api/payments/webhooks/confirm",
        )
        self.webhook_reject_url = payments_env(
            "PAYMENTS_WEBHOOK_REJECT_URL",
            default="https://intrajisbackend.com/api/payments/webhooks/reject",
        )
        self.webhook_validation_url = payments_env(
            "PAYMENTS_WEBHOOK_VALIDATION_URL",
            default="https://intrajisbackend.com/api/payments/webhooks/validation",
        )

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="PAYMENTS_API_KEY is not configured on the server.",
            )
        return {
            "apikey": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                json=json_body,
                params=params,
                timeout=60,
            )
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Payment gateway connection error: {exc}",
            ) from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                payload = response.json()
                detail = payload.get("message") or payload
            except ValueError:
                pass
            raise HTTPException(status_code=response.status_code, detail=detail)

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def _with_defaults(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = dict(payload)
        urls = dict(body.get("urls") or {})
        if self.return_url and not urls.get("return_url"):
            urls["return_url"] = self.return_url
        if self.cancel_url and not urls.get("cancel_url"):
            urls["cancel_url"] = self.cancel_url
        if urls:
            body["urls"] = urls

        webhooks = dict(body.get("webhooks") or {})
        if self.webhook_confirm_url and not webhooks.get("webhook_confirm"):
            webhooks["webhook_confirm"] = self.webhook_confirm_url
        if self.webhook_reject_url and not webhooks.get("webhook_reject"):
            webhooks["webhook_reject"] = self.webhook_reject_url
        if self.webhook_validation_url and not webhooks.get("webhook_validation"):
            webhooks["webhook_validation"] = self.webhook_validation_url
        if webhooks:
            body["webhooks"] = webhooks

        customs = list(body.get("customs") or [])
        customs_keys = {str(c.get("key")) for c in customs if isinstance(c, dict)}
        methods = list(body.get("methods") or [])
        for method in _methods_for_expiration_customs(methods):
            exp_key = f"{method}_expiration_minutes"
            if exp_key not in customs_keys:
                customs.append({"key": exp_key, "value": "-1"})
                customs_keys.add(exp_key)
        if customs:
            body["customs"] = customs

        return body

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /payment-gateway/v1/orders"""
        return self._request(
            "POST",
            "/payment-gateway/v1/orders",
            json_body=self._with_defaults(payload),
        )

    def _create_order_safe(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "message": "PAYMENTS_API_KEY is not configured on the server."}
        try:
            body = self.create_order(payload)
        except HTTPException as exc:
            print(f"[payments] create_order failed: {exc.detail}", flush=True)
            return {"status": "error", "message": str(exc.detail)}
        except Exception as exc:
            print(f"[payments] create_order failed: {exc}", flush=True)
            return {"status": "error", "message": str(exc)}

        redirect_url = body.get("redirect_url")
        if not redirect_url:
            return {
                "status": "error",
                "message": "Payment gateway did not return redirect_url",
                "response": body,
            }
        return {
            "status": "success",
            "redirect_url": redirect_url,
            "order_id": body.get("order_id"),
            "response": body,
        }

    def create_subscriber_dte_order(
        self,
        dte,
        customer,
        *,
        reference_id: str | None = None,
    ) -> dict[str, Any]:
        """Payment order for v2 subscriber ticket/invoice."""
        dte_type_id = int(getattr(dte, "dte_type_id", 39) or 39)
        document_folio = int(getattr(dte, "folio", 0) or 0)
        document_type_label = "Ticket" if dte_type_id == 39 else "Invoice"
        total = int(getattr(dte, "total", 0) or 0)
        if document_folio <= 0:
            return {"status": "error", "message": "Invalid document folio for payment order"}
        if total <= 0:
            return {"status": "error", "message": "Invalid DTE total for payment order"}

        reference_id = (reference_id or str(document_folio))[:100]
        methods_raw = payments_env("PAYMENTS_METHODS", default="tarjetas")
        methods = normalize_payment_methods(methods_raw)
        print(f"[payments] create_subscriber_dte_order folio={document_folio} methods={methods}", flush=True)

        user: dict[str, str] = {}
        email = getattr(customer, "email", None)
        if email and str(email).strip():
            user["email"] = str(email).strip()
        rut = getattr(customer, "rut", None)
        if rut and str(rut).strip():
            user["rut"] = str(rut).strip()
        phone = getattr(customer, "phone", None)
        if phone and str(phone).strip():
            user["phone"] = str(phone).strip().lstrip("+")
        customer_name = getattr(customer, "customer", None)
        if customer_name and str(customer_name).strip():
            parts = str(customer_name).strip().split(None, 1)
            user["first_name"] = parts[0]
            user["last_name"] = parts[1] if len(parts) > 1 else "Customer"
        else:
            user["first_name"] = "Customer"
            user["last_name"] = "Jisparking"

        payload: dict[str, Any] = {
            "reference_id": reference_id,
            "description": f"{document_type_label} folio {document_folio}",
            "methods": methods,
            "amount": {"currency": "CLP", "total": total},
            "items": [
                {
                    "name": f"{document_type_label} folio {document_folio}",
                    "code": str(document_folio),
                    "price": total,
                    "quantity": 1,
                }
            ],
            "user": user,
        }
        result = self._create_order_safe(payload)
        if result.get("status") != "success" and methods != ["*"]:
            msg = str(result.get("message", "")).lower()
            if "400006" in msg or "payment method list invalid" in msg or "must be unique" in msg:
                print(
                    f"[payments] retry folio={document_folio} with methods=['*'] "
                    f"after: {result.get('message')}",
                    flush=True,
                )
                payload["methods"] = ["*"]
                result = self._create_order_safe(payload)
        return result

    def payment_url_for_dte(self, dte, customer, db: Session) -> dict[str, Any]:
        """Ensure gateway order matches current DTE total; return stable folio pay link."""
        folio = int(getattr(dte, "folio", 0) or 0)
        if folio <= 0:
            return {"status": "error", "message": "Invalid document folio for payment link"}

        redirect_url = self.checkout_url_for_folio(folio, db)
        latest = (
            db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.folio == folio)
            .order_by(DtePaymentDataModel.id.desc())
            .first()
        )
        order_id = str(latest.order_id) if latest and latest.order_id else None
        proxy_base = payments_env(
            "PAYMENTS_WHATSAPP_PROXY_PUBLIC_BASE",
            default="https://intrajisbackend.com/api/payments/pay",
        ).rstrip("/")
        mode = payments_env("PAYMENTS_WHATSAPP_URL_MODE", default="proxy").strip().lower()
        if mode == "direct" and redirect_url:
            base = payments_env(
                "PAYMENTS_WHATSAPP_URL_BASE",
                default="https://pagos-pasarela.multicaja.cl/",
            ).rstrip("/") + "/"
            whatsapp_url_data = (
                redirect_url[len(base):]
                if redirect_url.startswith(base)
                else redirect_url
            )
        else:
            whatsapp_url_data = str(folio)
        return {
            "status": "success",
            "order_id": order_id,
            "redirect_url": redirect_url,
            "payment_link": f"{proxy_base}/{whatsapp_url_data}",
            "whatsapp_url_data": whatsapp_url_data,
            "amount": self._expected_dte_total(dte),
        }

    def _frontend_success_url(self, reference_id: str, order_id: str) -> str:
        base = payments_env(
            "PAYMENTS_RETURN_FRONTEND_URL",
            default="https://intrajis.com/payments/success",
        ).rstrip("/")
        qs = urlencode({"referenceId": reference_id, "orderId": order_id})
        return f"{base}?{qs}"

    def _frontend_already_paid_url(self, folio: int) -> str:
        base = payments_env(
            "PAYMENTS_ALREADY_PAID_FRONTEND_URL",
            default="https://intrajis.com/payments/already-paid",
        ).rstrip("/")
        qs = urlencode({"folio": folio})
        return f"{base}?{qs}"

    @staticmethod
    def _paid_document_redirect(folio: int, db: Session) -> str | None:
        dte = (
            db.query(DteModel)
            .filter(DteModel.folio == folio)
            .order_by(DteModel.id.desc())
            .first()
        )
        if dte and int(getattr(dte, "status_id", 0) or 0) == 5:
            return PaymentGatewayClass()._frontend_already_paid_url(int(folio))
        return None

    def _next_reference_id(self, folio: int, db: Session) -> str:
        """Unique gateway reference_id per payment attempt (folio, folio-r2, …)."""
        folio_s = str(folio)
        refs = (
            db.query(DtePaymentDataModel.reference_id)
            .filter(DtePaymentDataModel.folio == folio)
            .all()
        )
        max_attempt = 0
        for (ref,) in refs:
            if not ref:
                continue
            ref_s = str(ref).strip()
            if ref_s == folio_s:
                max_attempt = max(max_attempt, 1)
                continue
            match = re.match(rf"^{re.escape(folio_s)}-r(\d+)$", ref_s)
            if match:
                max_attempt = max(max_attempt, int(match.group(1)))
        if max_attempt == 0:
            return folio_s
        return f"{folio_s}-r{max_attempt + 1}"

    def checkout_url_for_pay_link(self, pay_id: str, db: Session) -> str:
        """Resolve /payments/pay/{id} — folio (stable) or legacy gateway order_id."""
        cleaned = unquote((pay_id or "").strip()).strip("/")
        for junk in ("{{1}}", "{{ 1 }}", "%7B%7B1%7D%7D", "{1}"):
            cleaned = cleaned.replace(junk, "")
        if cleaned.isdigit():
            return self.checkout_url_for_folio(int(cleaned), db)
        normalized = normalize_gateway_order_id(cleaned)
        if normalized and _GATEWAY_ORDER_ID_RE.match(normalized):
            return self.checkout_url_for_order_id(normalized, db)
        raise HTTPException(status_code=400, detail="Invalid payment link")

    def _order_checkout_url(self, gateway_order: dict[str, Any]) -> str | None:
        status = str(gateway_order.get("status") or "").lower()
        redirect_url = gateway_order.get("redirect_url")
        if status == "pending" and redirect_url:
            return str(redirect_url)
        return None

    @staticmethod
    def _expected_dte_total(dte) -> int:
        return int(getattr(dte, "total", 0) or 0)

    @staticmethod
    def _gateway_order_total(gateway_order: dict[str, Any]) -> int | None:
        amount_block = gateway_order.get("amount") or {}
        if isinstance(amount_block, dict) and amount_block.get("total") is not None:
            try:
                return int(float(amount_block["total"]))
            except (TypeError, ValueError):
                return None
        return None

    def _pending_order_matches_dte(
        self,
        gateway_order: dict[str, Any],
        dte,
        payment_row: DtePaymentDataModel | None = None,
    ) -> bool:
        """True only if the gateway pending order amount matches the current DTE total."""
        expected = self._expected_dte_total(dte)
        if expected <= 0:
            return False
        gateway_total = self._gateway_order_total(gateway_order)
        if gateway_total is not None:
            return gateway_total == expected
        if payment_row is not None and payment_row.amount is not None:
            return int(payment_row.amount) == expected
        return False

    def _create_and_record_checkout_order(
        self,
        folio: int,
        dte,
        customer,
        db: Session,
    ) -> str:
        ref_id = self._next_reference_id(folio, db)
        print(f"[payments] pay folio={folio} new gateway order reference_id={ref_id}", flush=True)
        result = self.create_subscriber_dte_order(dte, customer, reference_id=ref_id)
        if result.get("status") != "success":
            raise HTTPException(
                status_code=502,
                detail=result.get("message") or "Failed to create payment order",
            )
        redirect_url = result.get("redirect_url")
        if not redirect_url:
            raise HTTPException(status_code=502, detail="Payment gateway missing redirect_url")
        from app.backend.classes.dte_payment_data_class import DtePaymentDataClass

        DtePaymentDataClass(db).record_order_created(
            dte=dte,
            customer=customer,
            order_id=str(result.get("order_id") or ""),
            reference_id=ref_id,
            gateway_response=result.get("response"),
        )
        return str(redirect_url)

    def checkout_url_for_folio(self, folio: int, db: Session) -> str:
        """Stable pay link by document folio — creates a new gateway order if the last one expired."""
        dte = (
            db.query(DteModel)
            .filter(DteModel.folio == folio)
            .order_by(DteModel.id.desc())
            .first()
        )
        if not dte:
            pay_row = (
                db.query(DtePaymentDataModel)
                .filter(DtePaymentDataModel.folio == folio)
                .order_by(DtePaymentDataModel.id.desc())
                .first()
            )
            if pay_row and pay_row.dte_id:
                dte = db.query(DteModel).filter(DteModel.id == pay_row.dte_id).first()
        if not dte:
            raise HTTPException(status_code=404, detail="Document not found for payment")

        paid_redirect = self._paid_document_redirect(folio, db)
        if paid_redirect:
            print(f"[payments] pay folio={folio} already paid → frontend", flush=True)
            return paid_redirect

        customer = (
            db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
            if dte.rut
            else None
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found for payment")

        latest = (
            db.query(DtePaymentDataModel)
            .filter(DtePaymentDataModel.folio == folio)
            .order_by(DtePaymentDataModel.id.desc())
            .first()
        )
        if latest and latest.order_id:
            try:
                gateway_order = self.get_order(str(latest.order_id))
                checkout = self._order_checkout_url(gateway_order)
                if checkout and self._pending_order_matches_dte(gateway_order, dte, latest):
                    print(
                        f"[payments] pay folio={folio} reusing pending order={latest.order_id} "
                        f"amount={self._expected_dte_total(dte)}",
                        flush=True,
                    )
                    return checkout
                if checkout:
                    gateway_total = self._gateway_order_total(gateway_order)
                    print(
                        f"[payments] pay folio={folio} pending order={latest.order_id} "
                        f"amount mismatch (gateway={gateway_total}, dte={self._expected_dte_total(dte)}) "
                        f"→ new order",
                        flush=True,
                    )
                status = str(gateway_order.get("status") or "").lower()
                if status == "completed":
                    return self._frontend_success_url(
                        str(gateway_order.get("reference_id") or folio),
                        str(latest.order_id),
                    )
            except HTTPException:
                pass

        return self._create_and_record_checkout_order(folio, dte, customer, db)

    def checkout_url_for_order_id(self, order_id: str, db: Session) -> str:
        """Legacy WhatsApp links by order_id — recreates checkout if gateway order was rejected."""
        normalized = normalize_gateway_order_id(order_id)
        if not normalized:
            raise HTTPException(status_code=400, detail="Invalid payment order_id")

        try:
            gateway_order = self.get_order(normalized)
        except HTTPException:
            row = (
                db.query(DtePaymentDataModel)
                .filter(DtePaymentDataModel.order_id == normalized)
                .first()
            )
            if row and row.folio:
                return self.checkout_url_for_folio(int(row.folio), db)
            raise

        from app.backend.classes.dte_payment_data_class import document_folio_from_reference_id

        folio_hint = document_folio_from_reference_id(gateway_order.get("reference_id"))
        if folio_hint is None:
            row_hint = (
                db.query(DtePaymentDataModel)
                .filter(DtePaymentDataModel.order_id == normalized)
                .first()
            )
            if row_hint and row_hint.folio:
                folio_hint = int(row_hint.folio)
        if folio_hint is not None:
            paid_redirect = self._paid_document_redirect(folio_hint, db)
            if paid_redirect:
                print(
                    f"[payments] pay order={normalized} folio={folio_hint} already paid → frontend",
                    flush=True,
                )
                return paid_redirect

        checkout = self._order_checkout_url(gateway_order)
        if checkout and folio_hint is not None:
            dte = (
                db.query(DteModel)
                .filter(DteModel.folio == folio_hint)
                .order_by(DteModel.id.desc())
                .first()
            )
            row_hint = (
                db.query(DtePaymentDataModel)
                .filter(DtePaymentDataModel.order_id == normalized)
                .first()
            )
            if dte and self._pending_order_matches_dte(gateway_order, dte, row_hint):
                return checkout
            if dte:
                return self.checkout_url_for_folio(int(folio_hint), db)
        if checkout:
            return checkout

        status = str(gateway_order.get("status") or "").lower()
        if status == "completed":
            return self._frontend_success_url(
                str(gateway_order.get("reference_id") or ""),
                normalized,
            )

        if status in _RETRY_ORDER_STATUSES or not gateway_order.get("redirect_url"):
            folio = folio_hint
            if folio is None:
                row = (
                    db.query(DtePaymentDataModel)
                    .filter(DtePaymentDataModel.order_id == normalized)
                    .first()
                )
                if row and row.folio:
                    folio = int(row.folio)
            if folio is not None:
                print(
                    f"[payments] pay order={normalized} status={status} → new order for folio={folio}",
                    flush=True,
                )
                return self.checkout_url_for_folio(folio, db)

        redirect_url = gateway_order.get("redirect_url")
        if redirect_url:
            return str(redirect_url)
        raise HTTPException(status_code=404, detail="Payment order not available for checkout")

    def redirect_url_for_order(self, order_id: str) -> str | None:
        """Deprecated: use checkout_url_for_order_id with db session."""
        if not self.api_key:
            return None
        normalized = normalize_gateway_order_id(order_id)
        if not normalized:
            return None
        try:
            body = self.get_order(normalized)
        except HTTPException:
            return None
        return body.get("redirect_url") if isinstance(body, dict) else None

    def get_order(self, order_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payment-gateway/v1/orders/{order_id}")

    def refund_order(
        self,
        order_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/payment-gateway/v1/orders/{order_id}/refund",
            json_body=payload or {},
        )

    def list_transactions(
        self,
        *,
        reference_id: str | None = None,
        order_id: str | None = None,
        mc_code: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {}
        if reference_id:
            params["reference_id"] = reference_id
        if order_id:
            params["order_id"] = order_id
        if mc_code:
            params["mc_code"] = mc_code
        return self._request(
            "GET",
            "/payment-gateway/v1/transactions",
            params=params or None,
        )

    def get_transaction(self, transaction_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/payment-gateway/v1/transactions/{transaction_id}",
        )
