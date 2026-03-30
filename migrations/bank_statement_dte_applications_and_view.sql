-- Ejecutar en MySQL 8+ (una vez).
-- 1) Tabla: un movimiento de cartola (clave natural) solo puede aplicarse una vez.

CREATE TABLE IF NOT EXISTS bank_statement_dte_applications (
  id INT NOT NULL AUTO_INCREMENT,
  dte_id INT NOT NULL,
  folio INT NULL,
  deposit_number VARCHAR(255) NOT NULL,
  deposit_date VARCHAR(255) NOT NULL,
  amount INT NOT NULL,
  rut VARCHAR(255) NOT NULL,
  period VARCHAR(255) NOT NULL,
  applied_at DATETIME NULL,
  PRIMARY KEY (id),
  -- Índice con prefijos: VARCHAR(255)*5 en utf8mb4 supera 3072 bytes (error 1071).
  UNIQUE KEY uk_cartola_natural (
    deposit_number(80),
    deposit_date(24),
    amount,
    rut(24),
    period(48)
  ),
  KEY idx_dte_id (dte_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2) Vista: FIFO + monto igual + excluye movimientos ya aplicados (re-subida de cartola).

CREATE OR REPLACE VIEW comparation_pending_dtes_bank_statements AS
SELECT
  bs.id,
  bs.rut,
  c.customer,
  d.folio,
  bo.branch_office,
  d.total AS amount,
  bs.bank_statement_type_id,
  bs.period AS bank_statement_period,
  bs.amount AS bank_statement_amount,
  bs.rut AS bank_statement_rut,
  bs.deposit_number,
  bs.deposit_date
FROM (
  SELECT
    bs.id AS bs_id,
    d.id AS dte_id,
    ROW_NUMBER() OVER (
      PARTITION BY bs.id
      ORDER BY d.period ASC, d.added_date ASC, d.folio ASC
    ) AS rn
  FROM bank_statements bs
  INNER JOIN dtes d
    ON d.rut = bs.rut
   AND d.dte_type_id <> 61
   AND d.status_id = 4
   AND d.dte_version_id = 1
   AND bs.bank_statement_type_id = 2
   AND bs.rut <> '76063822-6'
   AND bs.amount = d.total
) ranked
INNER JOIN bank_statements bs ON bs.id = ranked.bs_id
INNER JOIN dtes d ON d.id = ranked.dte_id
LEFT JOIN customers c ON c.rut = d.rut
LEFT JOIN branch_offices bo ON bo.id = d.branch_office_id
WHERE ranked.rn = 1
  AND NOT EXISTS (
    SELECT 1
    FROM bank_statement_dte_applications a
    WHERE a.deposit_number = bs.deposit_number
      AND a.deposit_date = bs.deposit_date
      AND a.amount = bs.amount
      AND a.rut = bs.rut
      AND a.period = bs.period
  );
