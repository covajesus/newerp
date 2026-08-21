from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
try:
    cols = db.execute(text("SHOW COLUMNS FROM settings LIKE 'accounting_backend'")).fetchall()
    print("accounting_backend", bool(cols))
    for t in [
        "accounting_accounts",
        "accounting_entries",
        "accounting_entry_lines",
        "accounting_entry_documents",
    ]:
        n = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(t, n)
finally:
    db.close()
