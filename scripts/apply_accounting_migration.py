from sqlalchemy import text
from app.backend.db.database import SessionLocal
from app.backend.classes.accounting_entry_class import AccountingEntryClass

db = SessionLocal()
try:
    cols = db.execute(text("SHOW COLUMNS FROM settings LIKE 'accounting_backend'")).fetchall()
    if not cols:
        db.execute(
            text(
                "ALTER TABLE settings ADD COLUMN accounting_backend "
                "TINYINT NOT NULL DEFAULT 1 AFTER apigetaway_token"
            )
        )
        db.commit()
        print("added accounting_backend")
    else:
        print("accounting_backend exists")

    ddl = [
        """
        CREATE TABLE IF NOT EXISTS accounting_accounts (
          id INT NOT NULL AUTO_INCREMENT,
          code VARCHAR(32) NOT NULL,
          name VARCHAR(255) NOT NULL,
          status_id INT NOT NULL DEFAULT 1,
          added_date DATETIME DEFAULT NULL,
          updated_date DATETIME DEFAULT NULL,
          PRIMARY KEY (id),
          UNIQUE KEY uq_accounting_accounts_code (code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS accounting_entries (
          id INT NOT NULL AUTO_INCREMENT,
          number INT NOT NULL,
          period VARCHAR(7) DEFAULT NULL,
          entry_date DATE NOT NULL,
          glosa VARCHAR(512) NOT NULL,
          operation VARCHAR(8) DEFAULT NULL,
          annulled TINYINT NOT NULL DEFAULT 0,
          user_id INT DEFAULT NULL,
          source VARCHAR(32) NOT NULL DEFAULT 'system',
          external_ref VARCHAR(128) DEFAULT NULL,
          added_date DATETIME DEFAULT NULL,
          updated_date DATETIME DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_accounting_entries_period (period),
          KEY idx_accounting_entries_number (number),
          KEY idx_accounting_entries_date (entry_date),
          KEY idx_accounting_entries_annulled (annulled)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS accounting_entry_lines (
          id INT NOT NULL AUTO_INCREMENT,
          accounting_entry_id INT NOT NULL,
          account_code VARCHAR(32) NOT NULL,
          debit INT NOT NULL DEFAULT 0,
          credit INT NOT NULL DEFAULT 0,
          concept VARCHAR(255) DEFAULT NULL,
          sort_order INT NOT NULL DEFAULT 0,
          PRIMARY KEY (id),
          KEY idx_ael_entry (accounting_entry_id),
          CONSTRAINT fk_ael_entry FOREIGN KEY (accounting_entry_id)
            REFERENCES accounting_entries (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS accounting_entry_documents (
          id INT NOT NULL AUTO_INCREMENT,
          accounting_entry_id INT NOT NULL,
          doc_type VARCHAR(16) NOT NULL,
          issuer_rut VARCHAR(16) DEFAULT NULL,
          dte_type_id INT DEFAULT NULL,
          folio INT DEFAULT NULL,
          period VARCHAR(7) DEFAULT NULL,
          PRIMARY KEY (id),
          KEY idx_aed_entry (accounting_entry_id),
          CONSTRAINT fk_aed_entry FOREIGN KEY (accounting_entry_id)
            REFERENCES accounting_entries (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """,
    ]
    for stmt in ddl:
        db.execute(text(stmt))
        db.commit()

    seed = [
        ("111000101", "Caja / Banco 101"),
        ("111000102", "Caja / Banco 102"),
        ("111000122", "IVA Credito Fiscal"),
        ("221000226", "IVA Debito Fiscal"),
        ("221000223", "Retencion Honorarios"),
        ("441000102", "Gasto / Costo 441000102"),
        ("443000344", "Honorarios 443000344"),
    ]
    for code, name in seed:
        db.execute(
            text(
                "INSERT IGNORE INTO accounting_accounts "
                "(code, name, status_id, added_date, updated_date) "
                "VALUES (:code, :name, 1, NOW(), NOW())"
            ),
            {"code": code, "name": name},
        )
    db.commit()
    print("accounts", db.execute(text("SELECT COUNT(*) FROM accounting_accounts")).scalar())
    print("backend", AccountingEntryClass(db).get_backend())
finally:
    db.close()
