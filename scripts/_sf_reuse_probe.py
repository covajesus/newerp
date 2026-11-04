"""Probar payload de /folios/reutilizar (sin asumir éxito)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.db.database import SessionLocal

URL = "https://api.simplefactura.cl/folios/reutilizar"
RUT = "76063822-6"


def main() -> None:
    db = SessionLocal()
    try:
        token = CustomerTicketClass(db).get_token().get("accessToken")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # Solo diagnóstico de payload inválido primero (folio inexistente alto)
        # para no liberar un folio real por accidente.
        payload = {
            "credenciales": {
                "rutEmisor": RUT,
                "nombreSucursal": "Casa Matriz",
            },
            "codigoTipoDte": 61,
            "folio": 999999,
            "ambiente": 1,
        }
        r = requests.post(URL, json=payload, headers=headers, timeout=90)
        print("probe fake folio HTTP", r.status_code)
        print((r.text or "")[:500])

        # Estado actual de un rechazado real (solo lectura)
        r2 = requests.post(
            "https://api.simplefactura.cl/documentIssued",
            json={
                "credenciales": {
                    "rutEmisor": RUT,
                    "nombreSucursal": "Casa Matriz",
                },
                "dteReferenciadoExterno": {
                    "folio": 6915,
                    "codigoTipoDte": 61,
                    "ambiente": 1,
                },
            },
            headers=headers,
            timeout=60,
        )
        body = r2.json() if r2.text else {}
        data = body.get("data") or {}
        print(
            "6915 estado=",
            data.get("estadoSII"),
            "folioReutilizado=",
            data.get("folioReutilizado"),
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
