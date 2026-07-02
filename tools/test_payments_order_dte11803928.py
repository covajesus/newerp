"""Create payment order like generate_v2 would for DTE 11803928 / folio 32130061."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from app.backend.classes.payment_gateway_class import PaymentGatewayClass, normalize_payment_methods

KLAP_KEY = "12f99b04d0a145f78f20afad2c85a09b"
FOLIO = 32130061
TOTAL = 1000


def build_payload() -> dict:
    pg = PaymentGatewayClass()
    methods = normalize_payment_methods(os.getenv("PAYMENTS_METHODS", "tarjetas"))
    payload = {
        "reference_id": str(FOLIO),
        "description": f"Ticket folio {FOLIO}",
        "methods": methods,
        "amount": {"currency": "CLP", "total": TOTAL},
        "items": [
            {
                "name": f"Ticket folio {FOLIO}",
                "code": str(FOLIO),
                "price": TOTAL,
                "quantity": 1,
            }
        ],
        "user": {
            "email": "jesusrafaelcovahuerta@gmail.com",
            "first_name": "JESUS",
            "last_name": "COVA",
            "rut": "27141399-8",
            "phone": "976357193",
        },
    }
    return pg._with_defaults(payload), pg.base_url


def post_order(base_url: str, api_key: str, payload: dict, label: str) -> dict:
    masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else "(empty)"
    response = requests.post(
        f"{base_url.rstrip('/')}/payment-gateway/v1/orders",
        headers={
            "apikey": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=payload,
        timeout=60,
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text[:500]
    return {
        "label": label,
        "apikey_masked": masked,
        "http_status": response.status_code,
        "body": body,
        "ok": 200 <= response.status_code < 300,
    }


def main() -> int:
    payload, base_url = build_payload()
    env_key = (os.getenv("PAYMENTS_API_KEY") or "").strip()
    results = [
        post_order(base_url, env_key, payload, "PAYMENTS_API_KEY (.env / producción probable)"),
        post_order(base_url, KLAP_KEY, payload, "Klap key (nueva)"),
    ]
    print(
        json.dumps(
            {
                "dte_id": 11803928,
                "folio": FOLIO,
                "url": f"{base_url}/payment-gateway/v1/orders",
                "payload": payload,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if any(r["ok"] for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
