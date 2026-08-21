from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
try:
    cols = db.execute(text("SHOW COLUMNS FROM quotations LIKE 'payment_term_id'")).fetchall()
    print("before", cols)
    if cols:
        db.execute(text("ALTER TABLE quotations DROP COLUMN payment_term_id"))
        db.commit()
        print("dropped payment_term_id")
    print("after", db.execute(text("SHOW COLUMNS FROM quotations LIKE 'payment_term_id'")).fetchall())
finally:
    db.close()
