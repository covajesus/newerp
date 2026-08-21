"""Find a received inbox row that returns PDF from LibreDTE or SF."""
import requests
from app.backend.db.database import SessionLocal
from app.backend.db.models import ReceivedInboxModel
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.received_inbox_class import ReceivedInboxClass
from app.backend.classes.customer_ticket_class import (
    SIMPLEFACTURA_AMBIENTE,
    SIMPLEFACTURA_RUT_EMISOR,
    SIMPLEFACTURA_SUCURSAL,
)

TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
db = SessionLocal()
cls = ReceivedInboxClass(db)
rows = (
    db.query(ReceivedInboxModel)
    .filter(ReceivedInboxModel.folio < 10000000)
    .order_by(ReceivedInboxModel.id.desc())
    .limit(15)
    .all()
)
print("candidates", len(rows))
for row in rows:
    issuer = HelperClass().numeric_rut(row.rut)
    url = (
        f"https://libredte.cl/api/dte/dte_recibidos/pdf/{issuer}/"
        f"{int(row.dte_type_id)}/{int(row.folio)}/76063822"
        f"?papelContinuo=0&copias_tributarias=1&copias_cedibles=0&cedible=0&compress=0&base64=0"
    )
    r = requests.get(url, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=45)
    ok_ld = r.status_code == 200 and r.content.startswith(b"%PDF")
    print("LD", row.id, row.rut, row.folio, row.dte_type_id, r.status_code, ok_ld, (r.text or "")[:80])

    payload = {
        "credenciales": {
            "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
            "rutContribuyente": str(row.rut).strip(),
            "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
        },
        "ambiente": SIMPLEFACTURA_AMBIENTE,
        "folio": int(row.folio),
        "codigoTipoDte": int(row.dte_type_id),
    }
    try:
        pdf = cls._simplefactura_post_bytes(
            "https://api.simplefactura.cl/documentReceived/getPdf", payload
        )
        print("SF OK", row.id, len(pdf))
        break
    except Exception as exc:
        print("SF FAIL", row.id, str(exc)[:120])

db.close()
