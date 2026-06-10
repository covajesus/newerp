"""
Cliente HTTP para Klap Order API (Multicaja pasarela e-commerce).

Documentación OpenAPI:
https://api.pasarela.multicaja.cl/docs/ecommerce_api_payments
Spec: https://api.pasarela.multicaja.cl/docs/swagger/ecommerce_api_payments.yml

Autenticación: header `apikey`.
"""
from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import HTTPException


class KlapClass:
    def __init__(self):
        self.api_key = os.getenv("KLAP_API_KEY", "")
        self.base_url = os.getenv(
            "KLAP_API_BASE_URL",
            "https://api.pasarela.multicaja.cl",
        ).rstrip("/")
        self.return_url = os.getenv("KLAP_RETURN_URL", "")
        self.cancel_url = os.getenv("KLAP_CANCEL_URL", "")
        self.webhook_confirm_url = os.getenv(
            "KLAP_WEBHOOK_CONFIRM_URL",
            "https://intrajisbackend.com/api/klap/webhooks/confirm",
        )
        self.webhook_reject_url = os.getenv(
            "KLAP_WEBHOOK_REJECT_URL",
            "https://intrajisbackend.com/api/klap/webhooks/reject",
        )
        self.webhook_validation_url = os.getenv("KLAP_WEBHOOK_VALIDATION_URL", "")

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="KLAP_API_KEY no configurada en el servidor.",
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
                detail=f"Error de conexión con Klap: {exc}",
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
        for method in body.get("methods") or []:
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
        """Crea orden Klap sin lanzar HTTPException (uso interno WhatsApp v2)."""
        if not self.api_key:
            return {"status": "error", "message": "KLAP_API_KEY no configurada en el servidor."}
        try:
            body = self.create_order(payload)
        except HTTPException as exc:
            return {"status": "error", "message": str(exc.detail)}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        redirect_url = body.get("redirect_url")
        if not redirect_url:
            return {
                "status": "error",
                "message": "Klap no devolvió redirect_url",
                "response": body,
            }
        return {
            "status": "success",
            "redirect_url": redirect_url,
            "order_id": body.get("order_id"),
            "response": body,
        }

    def create_subscriber_dte_order(self, dte, customer) -> dict[str, Any]:
        """
        Orden de pago Klap para boleta/factura abonados v2.
        Docs: https://api.pasarela.multicaja.cl/docs/ecommerce_api_payments
        """
        dte_type_id = int(getattr(dte, "dte_type_id", 39) or 39)
        folio = int(getattr(dte, "folio", 0) or 0)
        dte_id = getattr(dte, "id", None)
        label = "Boleta" if dte_type_id == 39 else "Factura"
        total = int(getattr(dte, "total", 0) or 0)
        if total <= 0:
            return {"status": "error", "message": "Total del DTE inválido para orden Klap"}

        reference_id = f"intrajis-dte-{dte_id}-{folio}"[:100]
        methods_raw = os.getenv("KLAP_PAYMENT_METHODS", "tarjetas")
        methods = [m.strip() for m in methods_raw.split(",") if m.strip()]

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
            user["last_name"] = parts[1] if len(parts) > 1 else "Cliente"
        else:
            user["first_name"] = "Cliente"
            user["last_name"] = "Jisparking"

        payload: dict[str, Any] = {
            "reference_id": reference_id,
            "description": f"{label} folio {folio}",
            "methods": methods or ["tarjetas"],
            "amount": {"currency": "CLP", "total": total},
            "items": [
                {
                    "name": f"{label} folio {folio}",
                    "code": str(folio),
                    "price": total,
                    "quantity": 1,
                }
            ],
            "user": user,
        }
        return self._create_order_safe(payload)

    def payment_url_for_dte(self, dte, customer) -> dict[str, Any]:
        """Crea orden Klap y devuelve redirect_url + link proxy para WhatsApp/copiar."""
        result = self.create_subscriber_dte_order(dte, customer)
        if result.get("status") != "success":
            return result
        order_id = result.get("order_id")
        redirect_url = result.get("redirect_url")
        proxy_base = os.getenv(
            "KLAP_WHATSAPP_PROXY_PUBLIC_BASE",
            "https://intrajisbackend.com/api/klap/pay",
        ).rstrip("/")
        mode = (os.getenv("KLAP_WHATSAPP_URL_MODE") or "proxy").strip().lower()
        if mode == "direct" and redirect_url:
            base = os.getenv(
                "KLAP_WHATSAPP_URL_BASE",
                "https://pagos-pasarela.multicaja.cl/",
            ).rstrip("/") + "/"
            whatsapp_url_data = (
                redirect_url[len(base):]
                if redirect_url.startswith(base)
                else redirect_url
            )
        else:
            whatsapp_url_data = order_id
        return {
            "status": "success",
            "order_id": order_id,
            "redirect_url": redirect_url,
            "payment_link": f"{proxy_base}/{order_id}",
            "whatsapp_url_data": whatsapp_url_data,
            "response": result.get("response"),
        }

    def redirect_url_for_order(self, order_id: str) -> str | None:
        """Obtiene redirect_url de Klap para redirigir al cliente."""
        if not self.api_key:
            return None
        try:
            body = self.get_order(order_id)
        except HTTPException:
            return None
        return body.get("redirect_url") if isinstance(body, dict) else None

    def get_order(self, order_id: str) -> dict[str, Any]:
        """GET /payment-gateway/v1/orders/{order_id}"""
        return self._request("GET", f"/payment-gateway/v1/orders/{order_id}")

    def refund_order(
        self,
        order_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST /payment-gateway/v1/orders/{order_id}/refund"""
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
        """GET /payment-gateway/v1/transactions"""
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
        """GET /payment-gateway/v1/transactions/{transaction_id}"""
        return self._request(
            "GET",
            f"/payment-gateway/v1/transactions/{transaction_id}",
        )
