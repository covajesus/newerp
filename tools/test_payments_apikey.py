"""Compare PAYMENTS_API_KEY against Multicaja POST /orders (no DB)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BASE = os.getenv("PAYMENTS_API_BASE_URL", "https://api.pasarela.multicaja.cl").rstrip("/")
URL = f"{BASE}/payment-gateway/v1/orders"

PAYLOAD = {
    "reference_id": "intrajis-apikey-diagnostic",
    "description": "Diagnostic order (do not pay)",
    "methods": ["tarjetas"],
    "amount": {"currency": "CLP", "total": 1000},
    "items": [
        {
            "name": "Diagnostic",
            "code": "diag",
            "price": 1000,
            "quantity": 1,
        }
    ],
    "user": {
        "email": "diagnostic@intrajis.com",
        "first_name": "Diagnostic",
        "last_name": "Intrajis",
        "rut": "11111111-1",
        "phone": "56999999999",
    },
    "urls": {
        "return_url": os.getenv(
            "PAYMENTS_RETURN_URL",
            "https://intrajisbackend.com/api/payments/return",
        ),
        "cancel_url": os.getenv(
            "PAYMENTS_CANCEL_URL",
            "https://intrajisbackend.com/api/payments/cancel",
        ),
    },
}


def probe(label: str, api_key: str) -> dict:
    masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else "(empty)"
    try:
        response = requests.post(
            URL,
            headers={
                "apikey": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=PAYLOAD,
            timeout=60,
        )
        body: object
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
    except requests.RequestException as exc:
        return {
            "label": label,
            "apikey_masked": masked,
            "http_status": None,
            "body": str(exc),
            "ok": False,
        }


def main() -> int:
    env_key = (os.getenv("PAYMENTS_API_KEY") or "").strip()
    klap_key = (sys.argv[1] if len(sys.argv) > 1 else "").strip()

    results = [probe("PAYMENTS_API_KEY (.env)", env_key)]
    if klap_key and klap_key != env_key:
        results.append(probe("Klap key (argument)", klap_key))

    print(json.dumps({"url": URL, "results": results}, ensure_ascii=False, indent=2))
    return 0 if any(r["ok"] for r in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
