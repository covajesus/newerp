"""
Crea tablas processes + logs (detalle día/hora) y siembra procesos base.
No altera tablas existentes.
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
from app.backend.classes.process_registry import build_seed_processes

DDL = [
    """
    CREATE TABLE IF NOT EXISTS processes (
      id INT NOT NULL AUTO_INCREMENT,
      code VARCHAR(64) NOT NULL,
      name VARCHAR(255) NOT NULL,
      description VARCHAR(512) DEFAULT NULL,
      status_id INT DEFAULT 1,
      added_date DATETIME DEFAULT NULL,
      updated_date DATETIME DEFAULT NULL,
      PRIMARY KEY (id),
      UNIQUE KEY uq_processes_code (code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
      id INT NOT NULL AUTO_INCREMENT,
      process_id INT NOT NULL,
      level VARCHAR(16) NOT NULL DEFAULT 'error',
      reference_type VARCHAR(64) DEFAULT NULL,
      reference_id INT DEFAULT NULL,
      user_rut VARCHAR(32) DEFAULT NULL,
      error_code VARCHAR(64) DEFAULT NULL,
      message TEXT NOT NULL,
      detail TEXT DEFAULT NULL,
      stack_trace TEXT DEFAULT NULL,
      log_datetime DATETIME NOT NULL,
      log_date DATE NOT NULL,
      log_time VARCHAR(8) NOT NULL,
      year INT NOT NULL,
      month INT NOT NULL,
      day INT NOT NULL,
      hour INT NOT NULL,
      minute INT NOT NULL,
      second INT NOT NULL,
      weekday INT DEFAULT NULL,
      added_date DATETIME DEFAULT NULL,
      PRIMARY KEY (id),
      KEY idx_logs_process_id (process_id),
      KEY idx_logs_log_date (log_date),
      KEY idx_logs_level (level),
      KEY idx_logs_reference (reference_type, reference_id),
      KEY idx_logs_datetime (log_datetime)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]

SEED_PROCESSES = build_seed_processes()


def main() -> None:
    db = SessionLocal()
    try:
        # Centralizar: quitar tablas legacy de logs por proceso
        for legacy in ("email_logs", "email_liogs", "process_error_logs"):
            db.execute(text(f"DROP TABLE IF EXISTS `{legacy}`"))
        db.commit()
        print("dropped legacy email_logs / process_error_logs (si existían)")

        for stmt in DDL:
            db.execute(text(stmt))
        db.commit()
        print("tables ok: processes, logs")

        # FK logs.process_id → processes.id
        fk = db.execute(
            text(
                """
                SELECT CONSTRAINT_NAME
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'logs'
                  AND CONSTRAINT_TYPE = 'FOREIGN KEY'
                  AND CONSTRAINT_NAME = 'fk_logs_process_id'
                """
            )
        ).fetchone()
        if not fk:
            db.execute(
                text(
                    """
                    ALTER TABLE logs
                      ADD CONSTRAINT fk_logs_process_id
                      FOREIGN KEY (process_id) REFERENCES processes(id)
                      ON UPDATE CASCADE ON DELETE RESTRICT
                    """
                )
            )
            db.commit()
            print("FK ok: logs.process_id -> processes.id")
        else:
            print("FK already exists: fk_logs_process_id")

        now = datetime.now()
        for code, name, description in SEED_PROCESSES:
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
            else:
                row.name = name
                row.description = description
                row.updated_date = now
        db.commit()
        total = db.query(ProcessModel).count()
        print(f"seeded processes={total}")
        for row in db.query(ProcessModel).order_by(ProcessModel.name).all():
            print(f"  [{row.id}] {row.code} = {row.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
