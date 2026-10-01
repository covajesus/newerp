"""Crea consentimientos y el catalogo de origen (Pago de DTE, Web)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime

from sqlalchemy import text

from app.backend.db.database import SessionLocal
from app.backend.db.models import PersonalDataConsentTypeModel

TYPES_DDL = """
CREATE TABLE IF NOT EXISTS personal_data_consent_types (
  id INT NOT NULL AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description VARCHAR(512) DEFAULT NULL,
  added_date DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_pdct_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

TYPE_SEED = (
    ("dte_payment", "Pago de DTE", "Aceptacion antes de ir a la pasarela de un documento."),
    ("web", "Web", "Aceptacion desde el sitio web publico, sin documento asociado."),
)

DDL = """
CREATE TABLE IF NOT EXISTS personal_data_consents (
  id INT NOT NULL AUTO_INCREMENT,
  consent_type_id INT DEFAULT NULL,
  accepted INT NOT NULL DEFAULT 1,
  rut VARCHAR(32) DEFAULT NULL,
  customer_name VARCHAR(255) DEFAULT NULL,
  email VARCHAR(255) DEFAULT NULL,
  phone VARCHAR(64) DEFAULT NULL,
  customer_id INT DEFAULT NULL,
  dte_id INT DEFAULT NULL,
  folio INT DEFAULT NULL,
  dte_type_id INT DEFAULT NULL,
  document_type VARCHAR(64) DEFAULT NULL,
  branch_office_id INT DEFAULT NULL,
  branch_office_name VARCHAR(255) DEFAULT NULL,
  amount INT DEFAULT NULL,
  pay_id VARCHAR(128) DEFAULT NULL,
  case_description TEXT DEFAULT NULL,
  event_place VARCHAR(255) DEFAULT NULL,
  document_datetime DATETIME DEFAULT NULL,
  attachments_note VARCHAR(255) DEFAULT NULL,
  consent_title VARCHAR(255) DEFAULT NULL,
  consent_body TEXT DEFAULT NULL,
  consent_statement TEXT DEFAULT NULL,
  legal_basis VARCHAR(255) DEFAULT NULL,
  form_json TEXT DEFAULT NULL,
  ip_address VARCHAR(64) DEFAULT NULL,
  user_agent VARCHAR(512) DEFAULT NULL,
  accepted_datetime DATETIME NOT NULL,
  accepted_date DATE NOT NULL,
  accepted_time VARCHAR(8) NOT NULL,
  year INT NOT NULL,
  month INT NOT NULL,
  day INT NOT NULL,
  hour INT NOT NULL,
  minute INT NOT NULL,
  second INT NOT NULL,
  weekday INT DEFAULT NULL,
  weekday_name VARCHAR(16) DEFAULT NULL,
  added_date DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_pdc_consent_type (consent_type_id),
  KEY idx_pdc_rut (rut),
  KEY idx_pdc_folio (folio),
  KEY idx_pdc_pay_id (pay_id),
  KEY idx_pdc_accepted_datetime (accepted_datetime),
  KEY idx_pdc_accepted_date (accepted_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

CHALLENGE_DDL = """
CREATE TABLE IF NOT EXISTS payment_consent_challenges (
  id INT NOT NULL AUTO_INCREMENT,
  token VARCHAR(80) NOT NULL,
  pay_id VARCHAR(128) NOT NULL,
  expires_at DATETIME NOT NULL,
  used_at DATETIME DEFAULT NULL,
  added_date DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_pcc_token (token),
  KEY idx_pcc_pay_id (pay_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _column_exists(db, table: str, column: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table
              AND COLUMN_NAME = :column
            """
        ),
        {"table": table, "column": column},
    ).fetchone()
    return row is not None


def main() -> None:
    db = SessionLocal()
    try:
        db.execute(text(TYPES_DDL))
        db.execute(text(DDL))
        db.execute(text(CHALLENGE_DDL))
        db.commit()

        now = datetime.now()
        for code, name, description in TYPE_SEED:
            row = (
                db.query(PersonalDataConsentTypeModel)
                .filter(PersonalDataConsentTypeModel.code == code)
                .first()
            )
            if not row:
                db.add(
                    PersonalDataConsentTypeModel(
                        code=code,
                        name=name,
                        description=description,
                        added_date=now,
                    )
                )
        db.commit()

        if not _column_exists(db, "personal_data_consents", "consent_type_id"):
            db.execute(
                text(
                    """
                    ALTER TABLE personal_data_consents
                      ADD COLUMN consent_type_id INT DEFAULT NULL AFTER id,
                      ADD KEY idx_pdc_consent_type (consent_type_id)
                    """
                )
            )
            db.commit()
            print("column ok: personal_data_consents.consent_type_id")
        else:
            print("column already exists: consent_type_id")

        fk = db.execute(
            text(
                """
                SELECT CONSTRAINT_NAME
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'personal_data_consents'
                  AND CONSTRAINT_TYPE = 'FOREIGN KEY'
                  AND CONSTRAINT_NAME = 'fk_pdc_consent_type_id'
                """
            )
        ).fetchone()
        if not fk:
            db.execute(
                text(
                    """
                    ALTER TABLE personal_data_consents
                      ADD CONSTRAINT fk_pdc_consent_type_id
                        FOREIGN KEY (consent_type_id)
                        REFERENCES personal_data_consent_types (id)
                    """
                )
            )
            db.commit()
            print("FK ok: consent_type_id")
        else:
            print("FK already exists: consent_type_id")

        types = db.execute(
            text("SELECT id, code, name FROM personal_data_consent_types ORDER BY id")
        ).fetchall()
        count = db.execute(text("SELECT COUNT(*) FROM personal_data_consents")).scalar()
        print(f"table ok: personal_data_consents rows={count}")
        print("table ok: payment_consent_challenges")
        print("types:", [(row[0], row[1], row[2]) for row in types])
    finally:
        db.close()


if __name__ == "__main__":
    main()
