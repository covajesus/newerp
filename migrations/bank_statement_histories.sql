-- Historial de cartolas: copia de bank_statements antes de cada DELETE masivo.
-- added_date = cuándo se guardó la fila en el historial (antes archived_at).
-- Índice único evita duplicar el mismo movimiento en el mismo período (mes YYYY-MM).
-- Ejecutar en MySQL 8+ (una vez).

CREATE TABLE IF NOT EXISTS bank_statement_histories (
  id INT NOT NULL AUTO_INCREMENT,
  bank_statement_type_id INT NULL,
  rut VARCHAR(255) NULL,
  deposit_number VARCHAR(255) NULL,
  amount INT NULL,
  period VARCHAR(255) NULL,
  deposit_date VARCHAR(255) NULL,
  added_date DATETIME NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_bank_statement_histories_natural (
    period(48),
    bank_statement_type_id,
    deposit_number(80),
    deposit_date(24),
    amount,
    rut(32)
  ),
  KEY idx_bank_statement_histories_period (period(24)),
  KEY idx_bank_statement_histories_added_date (added_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Si ya creaste la tabla con archived_at:
-- ALTER TABLE bank_statement_histories CHANGE COLUMN archived_at added_date DATETIME NULL;
-- ALTER TABLE bank_statement_histories RENAME INDEX idx_bank_statement_histories_archived TO idx_bank_statement_histories_added_date;
