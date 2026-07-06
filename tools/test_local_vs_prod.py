"""Diagnóstico local vs producción: pagos Klap, WhatsApp Meta, PDF, API backend."""
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

PROD_BASE = "https://intrajisbackend.com/api"
DTE_ID = int(os.getenv("TEST_DTE_ID", "11804034"))
FOLIO = int(os.getenv("TEST_FOLIO", "32130918"))
RUT = os.getenv("TEST_RUT", "27141399-8")


def mask(s: str | None) -> str:
    s = (s or "").strip()
    if not s:
        return "(vacío)"
    if len(s) < 8:
        return "***"
    return f"{s[:4]}…{s[-4:]}"


def local_payments() -> dict:
    from app.backend.classes.payment_gateway_class import PaymentGatewayClass
    from app.backend.db.database import SessionLocal
    from app.backend.db.models import CustomerModel, DteModel

    db = SessionLocal()
    try:
        dte = db.query(DteModel).filter(DteModel.id == DTE_ID).first()
        if not dte:
            return {"ok": False, "error": f"DTE {DTE_ID} no encontrado en BD local"}
        customer = db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()
        pg = PaymentGatewayClass()
        ref = f"{dte.folio or FOLIO}-diag-local"
        result = pg.create_subscriber_dte_order(dte, customer, reference_id=ref)
        return {
            "ok": result.get("status") == "success",
            "api_key": mask(pg.api_key),
            "folio": dte.folio,
            "reference_id": ref,
            "order_id": result.get("order_id"),
            "message": result.get("message"),
        }
    finally:
        db.close()


def local_whatsapp_token() -> dict:
    from app.backend.classes.whatsapp_class import (
        validate_whatsapp_access_token,
        whatsapp_access_token,
    )

    token = whatsapp_access_token()
    source = "WHATSAPP_ACCESS_TOKEN" if os.getenv("WHATSAPP_ACCESS_TOKEN") else "LIBREDTE_TOKEN"
    err = validate_whatsapp_access_token()
    return {
        "ok": err is None,
        "token_source": source,
        "token": mask(token),
        "error": err,
    }


def local_smtp() -> dict:
    pwd = (os.getenv("DTE_EMAIL_SMTP_PASSWORD") or os.getenv("SMTP_PASSWORD") or "").strip()
    return {
        "ok": bool(pwd),
        "user": os.getenv("DTE_EMAIL_SMTP_USER") or "contacto@jisparking.com",
        "password_set": bool(pwd),
    }


def prod_http_get(path: str, timeout: int = 30) -> dict:
    url = f"{PROD_BASE}{path}"
    try:
        r = requests.get(url, timeout=timeout)
        body: object
        try:
            body = r.json()
        except ValueError:
            body = (r.text or "")[:500]
        return {"ok": r.status_code < 400, "url": url, "http": r.status_code, "body": body}
    except requests.RequestException as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def prod_pdf_folio() -> dict:
    url = f"https://intrajisbackend.com/files/{FOLIO}.pdf"
    try:
        r = requests.head(url, timeout=20, allow_redirects=True)
        return {"ok": r.status_code == 200, "url": url, "http": r.status_code}
    except requests.RequestException as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def main() -> int:
    report = {
        "target": {"dte_id": DTE_ID, "folio": FOLIO, "rut": RUT},
        "local": {
            "env": {
                "PAYMENTS_API_KEY": mask(os.getenv("PAYMENTS_API_KEY")),
                "PAYMENTS_API_BASE_URL": os.getenv("PAYMENTS_API_BASE_URL"),
                "KLAP_API_KEY_present": bool(os.getenv("KLAP_API_KEY")),
            },
            "klap_create_order": local_payments(),
            "whatsapp_meta_token": local_whatsapp_token(),
            "smtp": local_smtp(),
        },
        "produccion": {
            "api_alive": prod_http_get(f"/dtes/massive_resend_whatsapp/pending?period=2026-07"),
            "pdf_publico": prod_pdf_folio(),
            "resend_endpoint_sin_wa": prod_http_get(f"/dtes/resend/{DTE_ID}/0/null"),
        },
        "notas": [
            "Klap: Multicaja usa la misma PAYMENTS_API_KEY en local y prod si copiaste el .env.",
            "WhatsApp prod: el reenvío exitoso confirma LIBREDTE_TOKEN vigente en el servidor.",
            "Local WA falla si LIBREDTE_TOKEN local está vencido (Meta 190).",
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    local_ok = (
        report["local"]["klap_create_order"].get("ok")
        and report["local"]["smtp"].get("ok")
    )
    prod_ok = report["produccion"]["api_alive"].get("ok") and report["produccion"]["pdf_publico"].get("ok")
    return 0 if local_ok and prod_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
