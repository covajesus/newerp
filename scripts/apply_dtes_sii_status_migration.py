"""Agrega columnas SII en dtes (SimpleFactura status sync).

sii_status_id: 1=Pendiente, 2=Aceptado, 3=Rechazado
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.backend.db.database import SessionLocal
from app.backend.db.models import ProcessModel

COLUMNS = [
    ("sii_status_id", "TINYINT NULL DEFAULT NULL AFTER folio"),
    ("sii_track_id", "BIGINT NULL DEFAULT NULL AFTER sii_status_id"),
    ("sii_rejection_reason", "TEXT NULL AFTER sii_track_id"),
    ("sii_status_checked_at", "DATETIME NULL AFTER sii_rejection_reason"),
    ("sii_status_alerted_at", "DATETIME NULL AFTER sii_status_checked_at"),
]

SEED = [
    ("dte_sii_rejected", "DTE - Rechazado SII", "DTE emitido rechazado por el SII (SimpleFactura)"),
]


def column_exists(db, table: str, column: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            LIMIT 1
            """
        ),
        {"table": table, "column": column},
    ).first()
    return bool(row)


def index_exists(db, table: str, index_name: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND INDEX_NAME = :index_name
            LIMIT 1
            """
        ),
        {"table": table, "index_name": index_name},
    ).first()
    return bool(row)


def main() -> None:
    db = SessionLocal()
    try:
        for name, ddl in COLUMNS:
            if column_exists(db, "dtes", name):
                print(f"skip column (exists): dtes.{name}")
                continue
            db.execute(text(f"ALTER TABLE dtes ADD COLUMN {name} {ddl}"))
            db.commit()
            print(f"added column: dtes.{name}")

        if index_exists(db, "dtes", "idx_dtes_sii_status_id"):
            print("skip index (exists): idx_dtes_sii_status_id")
        else:
            db.execute(text("CREATE INDEX idx_dtes_sii_status_id ON dtes (sii_status_id)"))
            db.commit()
            print("added index: idx_dtes_sii_status_id")

        now = datetime.now()
        for code, name, description in SEED:
            row = db.query(ProcessModel).filter(ProcessModel.code == code).first()
            if row:
                print(f"skip process (exists): {code}")
                continue
            db.add(
                ProcessModel(
                    code=code,
                    name=name,
                    description=description,
                    status_id=1,
                    added_date=now,
                    updated_date=now,
                )
            )
            db.commit()
            print(f"seeded process: {code}")

        print("migration ok: dtes sii status columns")
    except Exception as exc:
        db.rollback()
        print(f"migration failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
