-- Parche: en algunos servidores la vista quedó SIN el NOT EXISTS a bank_statement_dte_applications,
-- por eso siguen apareciendo filas ya conciliadas. Ejecutar en MySQL 8+.

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
    WHERE a.amount = bs.amount
      AND TRIM(a.rut) = TRIM(bs.rut)
      AND TRIM(a.period) = TRIM(bs.period)
      AND LEFT(TRIM(a.deposit_date), 10) = LEFT(TRIM(bs.deposit_date), 10)
      AND (
        TRIM(a.deposit_number) = TRIM(bs.deposit_number)
        OR (
          TRIM(a.deposit_number) REGEXP '^[0-9]+$'
          AND TRIM(bs.deposit_number) REGEXP '^[0-9]+$'
          AND CAST(TRIM(a.deposit_number) AS UNSIGNED) = CAST(TRIM(bs.deposit_number) AS UNSIGNED)
        )
      )
  );
