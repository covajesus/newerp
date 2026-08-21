"""Try SimpleFactura PDF payload variants + LibreDTE fallback."""
import base64
import requests
from app.backend.db.database import SessionLocal
from app.backend.db.models import ReceivedInboxModel
from app.backend.classes.received_inbox_class import ReceivedInboxClass
from app.backend.classes.customer_ticket_class import (
    SIMPLEFACTURA_AMBIENTE,
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
)
from app.backend.classes.helper_class import HelperClass

db = SessionLocal()
row = db.query(ReceivedInboxModel).order_by(ReceivedInboxModel.id.desc()).first()
print("row", row.id, row.rut, row.folio, row.dte_type_id)
cls = ReceivedInboxClass(db)

payloads = [
    ("flat+contrib", {
        "credenciales": {
            "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
            "rutContribuyente": str(row.rut).strip(),
            "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
        },
        "ambiente": SIMPLEFACTURA_AMBIENTE,
        "folio": int(row.folio),
        "codigoTipoDte": int(row.dte_type_id),
    }),
    ("ref-externo", {
        "credenciales": {
            "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
            "rutContribuyente": str(row.rut).strip(),
            "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
        },
        "dteReferenciadoExterno": {
            "folio": int(row.folio),
            "codigoTipoDte": int(row.dte_type_id),
            "ambiente": SIMPLEFACTURA_AMBIENTE,
        },
    }),
    ("flat-no-contrib", {
        "credenciales": {
            "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
            "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
        },
        "ambiente": SIMPLEFACTURA_AMBIENTE,
        "folio": int(row.folio),
        "codigoTipoDte": int(row.dte_type_id),
    }),
]

for name, payload in payloads:
    try:
        pdf = cls._simplefactura_post_bytes(
            "https://api.simplefactura.cl/documentReceived/getPdf", payload
        )
        print(name, "OK", len(pdf), pdf[:5])
    except Exception as exc:
        print(name, "FAIL", str(exc)[:200])

# LibreDTE
issuer = HelperClass().numeric_rut(row.rut)
url = (
    f"https://libredte.cl/api/dte/dte_recibidos/pdf/{issuer}/"
    f"{int(row.dte_type_id)}/{int(row.folio)}/76063822"
    f"?papelContinuo=0&copias_tributarias=1&copias_cedibles=0&cedible=0&compress=0&base64=0"
)
TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=60)
print("libredte", r.status_code, r.headers.get("content-type"), len(r.content), r.content[:8])
db.close()
