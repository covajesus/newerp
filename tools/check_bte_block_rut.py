from app.backend.classes.honorary_class import HonoraryClass
from app.backend.db.database import SessionLocal
from sqlalchemy import text

print("blocked hyphen", HonoraryClass.is_bte_sii_blocked_rut("27141399-8"))
print("blocked digits", HonoraryClass.is_bte_sii_blocked_rut("271413998"))
print("blocked dots", HonoraryClass.is_bte_sii_blocked_rut("27.141.399-8"))
print("other rut", HonoraryClass.is_bte_sii_blocked_rut("11111111-1"))

db = SessionLocal()
try:
    rows = db.execute(
        text(
            """
            SELECT id, status_id, bte_emitted, bte_folio, foreigner_id
            FROM honoraries
            WHERE REPLACE(REPLACE(CAST(replacement_employee_rut AS CHAR), '.', ''), '-', '') LIKE '%27141399%'
            ORDER BY id DESC
            LIMIT 15
            """
        )
    ).mappings().all()
    emitted = [dict(r) for r in rows if int(r.get("bte_emitted") or 0) == 1 or r.get("bte_folio")]
    print("honoraries_found", len(rows))
    print("any_bte_emitted", len(emitted))
    for r in rows[:5]:
        print(dict(r))
finally:
    db.close()
