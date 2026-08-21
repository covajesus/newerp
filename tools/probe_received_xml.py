"""Fetch received XML with working creds; inspect options for PDF."""
import base64
import json
import requests
from app.backend.db.database import SessionLocal
from app.backend.classes.received_inbox_class import ReceivedInboxClass
from app.backend.classes.customer_ticket_class import (
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
    SIMPLEFACTURA_AMBIENTE,
)
from app.backend.db.models import ReceivedInboxModel

db = SessionLocal()
row = db.query(ReceivedInboxModel).filter(ReceivedInboxModel.id == 645).first()
cls = ReceivedInboxClass(db)
token, _ = cls._simplefactura_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

body = {
    "credenciales": {
        "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
        "rutContribuyente": str(row.rut).strip(),
        "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
    },
    "ambiente": SIMPLEFACTURA_AMBIENTE,
    "folio": int(row.folio),
    "codigoTipoDte": int(row.dte_type_id),
}

for path in (
    "https://api.simplefactura.cl/documentReceived/xml",
    "https://api.simplefactura.cl/documentReceived/getPdf",
    "https://api.simplefactura.cl/proveedores/pdf",
    "https://api.simplefactura.cl/documentsReceived/pdf",
):
    r = requests.post(path, json=body, headers=headers, timeout=45)
    print(path.split(".cl")[-1], r.status_code, r.headers.get("content-type"), r.content[:60])

# Also try without nombreSucursal
body2 = {
    "credenciales": {
        "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
        "rutContribuyente": str(row.rut).strip(),
    },
    "ambiente": SIMPLEFACTURA_AMBIENTE,
    "folio": int(row.folio),
    "codigoTipoDte": int(row.dte_type_id),
}
r = requests.post("https://api.simplefactura.cl/documentReceived/xml", json=body2, headers=headers, timeout=45)
print("xml no sucursal", r.status_code, r.content[:80])
if r.status_code == 200:
    try:
        j = r.json()
        print("json keys", list(j.keys()) if isinstance(j, dict) else type(j))
        data = j.get("data") if isinstance(j, dict) else None
        if isinstance(data, str) and data:
            print("data prefix", data[:80])
            # maybe base64 xml
            try:
                raw = base64.b64decode(data)
                print("decoded", raw[:80])
            except Exception:
                pass
        elif isinstance(data, dict):
            print("data dict keys", data.keys())
    except Exception as e:
        print("not json", e)

db.close()
