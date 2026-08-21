-- SII tax password for BTE emission (English column names)
-- Migrates legacy Spanish column if present.
ALTER TABLE settings
  ADD COLUMN IF NOT EXISTS sii_login_rut VARCHAR(32) NULL;

-- Prefer rename when old column exists; otherwise add new column.
-- MySQL 8 may not support IF NOT EXISTS on CHANGE; run carefully.
-- Manual fallback:
--   ALTER TABLE settings CHANGE COLUMN sii_clave_tributaria sii_tax_password TEXT NULL;
--   ALTER TABLE settings ADD COLUMN sii_tax_password TEXT NULL;
