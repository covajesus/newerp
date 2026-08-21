from sqlalchemy import text
from app.backend.db.database import SessionLocal

db = SessionLocal()
try:
    for col, ddl in [
        (
            "send_email",
            "ALTER TABLE quotations ADD COLUMN send_email TINYINT NOT NULL DEFAULT 1 AFTER renew_mode",
        ),
        (
            "send_whatsapp",
            "ALTER TABLE quotations ADD COLUMN send_whatsapp TINYINT NOT NULL DEFAULT 0 AFTER send_email",
        ),
    ]:
        exists = db.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'quotations' "
                "AND COLUMN_NAME = :col"
            ),
            {"col": col},
        ).scalar()
        if not exists:
            db.execute(text(ddl))
            db.commit()
            print("added", col)
        else:
            print("exists", col)
finally:
    db.close()
