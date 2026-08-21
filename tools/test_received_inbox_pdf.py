"""Test received_inbox PDF download via SimpleFactura."""
from app.backend.db.database import SessionLocal
from app.backend.classes.received_inbox_class import ReceivedInboxClass

db = SessionLocal()
try:
    result = ReceivedInboxClass(db).download_pdf(644)
    status = result.get("status")
    print("status", status)
    if status == "success":
        print("file_name", result.get("file_name"))
        data = result.get("file_data") or ""
        print("b64_len", len(data))
        import base64
        raw = base64.b64decode(data)
        print("pdf_magic", raw[:8])
    else:
        print("message", (result.get("message") or "")[:800])
finally:
    db.close()
