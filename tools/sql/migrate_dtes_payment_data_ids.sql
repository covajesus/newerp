-- Migrate dtes_payment_data to id-based columns (run once on existing table)
ALTER TABLE dtes_payment_data
  ADD COLUMN customer_id INT NULL AFTER dte_id,
  ADD COLUMN payment_type_id INT NULL AFTER customer_id,
  ADD COLUMN branch_office_id INT NULL AFTER payment_type_id;

-- Optional: backfill ids from related tables before dropping string columns
UPDATE dtes_payment_data dp
LEFT JOIN customers c ON c.rut = dp.rut
SET dp.customer_id = c.id
WHERE dp.customer_id IS NULL AND c.id IS NOT NULL;

UPDATE dtes_payment_data dp
LEFT JOIN dtes d ON d.id = dp.dte_id
SET
  dp.branch_office_id = COALESCE(dp.branch_office_id, d.branch_office_id),
  dp.customer_id = COALESCE(dp.customer_id, (
    SELECT c.id FROM customers c WHERE c.rut = d.rut LIMIT 1
  ))
WHERE dp.dte_id IS NOT NULL;

UPDATE dtes_payment_data
SET payment_type_id = 2
WHERE payment_type_id IS NULL
  AND payment_status = 'completed';

ALTER TABLE dtes_payment_data
  DROP COLUMN IF EXISTS customer_name,
  DROP COLUMN IF EXISTS branch_office,
  DROP COLUMN IF EXISTS payment_method;

ALTER TABLE dtes_payment_data
  DROP COLUMN IF EXISTS klap_status;

-- If payment_status column is missing but klap_status exists:
-- ALTER TABLE dtes_payment_data CHANGE COLUMN klap_status payment_status VARCHAR(32) NULL;
