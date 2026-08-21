"""Try alternate SimpleFactura payloads for received PDF."""
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

URL = "https://api.simplefactura.cl/documentReceived/getPdf"
db = SessionLocal()
row = db.query(ReceivedInboxModel).filter(ReceivedInboxModel.id == 645).first()
print("row", row.id, row.rut, row.folio, row.dte_type_id)

cls = ReceivedInboxClass(db)
token, _ = cls._simplefactura_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

payloads = [
    {
        "name": "current",
        "body": {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "rutContribuyente": str(row.rut).strip(),
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": SIMPLEFACTURA_AMBIENTE,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        },
    },
    {
        "name": "contrib=jis emis=supplier",
        "body": {
            "credenciales": {
                "rutEmisor": str(row.rut).strip(),
                "rutContribuyente": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": SIMPLEFACTURA_AMBIENTE,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        },
    },
    {
        "name": "both jis ambi0",
        "body": {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "rutContribuyente": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": 0,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        },
    },
    {
        "name": "both jis ambi1",
        "body": {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "rutContribuyente": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": 1,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        },
    },
    {
        "name": "pascal",
        "body": {
            "Credenciales": {
                "RutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "RutContribuyente": str(row.rut).strip(),
                "NombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "Ambiente": SIMPLEFACTURA_AMBIENTE,
            "Folio": int(row.folio),
            "CodigoTipoDte": int(row.dte_type_id),
        },
    },
    {
        "name": "xml endpoint both jis",
        "url": "https://api.simplefactura.cl/documentReceived/xml",
        "body": {
            "credenciales": {
                "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
                "rutContribuyente": SIMPLEFACTURA_RUT_EMISOR,
                "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
            },
            "ambiente": 1,
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
        },
    },
]

for p in payloads:
    url = p.get("url") or URL
    try:
        r = requests.post(url, json=p["body"], headers=headers, timeout=45)
        magic = r.content[:8] if r.content else b""
        print(p["name"], r.status_code, magic, (r.text or "")[:180].replace("\n", " "))
    except Exception as exc:
        print(p["name"], "ERR", exc)

db.close()
