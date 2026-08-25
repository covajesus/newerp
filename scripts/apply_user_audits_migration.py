"""Crea tabla user_audits para auditoría de actividad por usuario."""
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

DDL = """
CREATE TABLE IF NOT EXISTS user_audits (
  id INT NOT NULL AUTO_INCREMENT,
  user_rut VARCHAR(32) NOT NULL,
  user_full_name VARCHAR(255) DEFAULT NULL,
  rol_id INT DEFAULT NULL,
  session_id VARCHAR(64) DEFAULT NULL,
  process_id INT DEFAULT NULL,
  action_type VARCHAR(32) NOT NULL,
  path VARCHAR(512) DEFAULT NULL,
  route_name VARCHAR(128) DEFAULT NULL,
  method VARCHAR(16) DEFAULT NULL,
  element_tag VARCHAR(64) DEFAULT NULL,
  element_id VARCHAR(128) DEFAULT NULL,
  element_text VARCHAR(512) DEFAULT NULL,
  message VARCHAR(1024) DEFAULT NULL,
  detail TEXT DEFAULT NULL,
  meta_json TEXT DEFAULT NULL,
  duration_ms INT DEFAULT NULL,
  ip_address VARCHAR(64) DEFAULT NULL,
  user_agent VARCHAR(512) DEFAULT NULL,
  audit_datetime DATETIME NOT NULL,
  audit_date DATE NOT NULL,
  audit_time VARCHAR(8) NOT NULL,
  year INT NOT NULL,
  month INT NOT NULL,
  day INT NOT NULL,
  hour INT NOT NULL,
  minute INT NOT NULL,
  second INT NOT NULL,
  weekday INT DEFAULT NULL,
  added_date DATETIME DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_ua_user_rut (user_rut),
  KEY idx_ua_session (session_id),
  KEY idx_ua_action (action_type),
  KEY idx_ua_datetime (audit_datetime),
  KEY idx_ua_date (audit_date),
  KEY idx_ua_process (process_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""

SEED = [
    ("user_audit", "Auditoría de usuarios", "Registro de actividad UI/API por usuario"),
]


def main() -> None:
    db = SessionLocal()
    try:
        db.execute(text(DDL))
        db.commit()
        print("table ok: user_audits")

        fk = db.execute(
            text(
                """
                SELECT CONSTRAINT_NAME
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'user_audits'
                  AND CONSTRAINT_TYPE = 'FOREIGN KEY'
                  AND CONSTRAINT_NAME = 'fk_user_audits_process_id'
                """
            )
        ).fetchone()
        if not fk:
            try:
                db.execute(
                    text(
                        """
                        ALTER TABLE user_audits
                          ADD CONSTRAINT fk_user_audits_process_id
                          FOREIGN KEY (process_id) REFERENCES processes(id)
                          ON UPDATE CASCADE ON DELETE SET NULL
                        """
                    )
                )
                db.commit()
                print("FK ok: user_audits.process_id -> processes.id")
            except Exception as e:
                db.rollback()
                print(f"FK skip/warn: {e}")
        else:
            print("FK already exists")

        now = datetime.now()
        for code, name, description in SEED:
            row = db.query(ProcessModel).filter(ProcessModel.code == code).first()
            if not row:
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
        print("seed process user_audit ok")
        count = db.execute(text("SELECT COUNT(*) FROM user_audits")).scalar()
        print(f"user_audits rows: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
