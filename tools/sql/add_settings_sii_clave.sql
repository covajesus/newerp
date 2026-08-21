-- Clave Tributaria SII (BTE / boletas de honorarios de terceros)
ALTER TABLE settings
  ADD COLUMN IF NOT EXISTS sii_login_rut VARCHAR(32) NULL,
  ADD COLUMN IF NOT EXISTS sii_clave_tributaria TEXT NULL;
