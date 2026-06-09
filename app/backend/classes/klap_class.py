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

        return body

    def create_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /payment-gateway/v1/orders"""
        return self._request(
            "POST",
            "/payment-gateway/v1/orders",
            json_body=self._with_defaults(payload),
        )

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
