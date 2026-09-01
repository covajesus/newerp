-- Estados SII de DTE emitidos (solo SimpleFactura).
-- sii_status_id: 1=Pendiente, 2=Aceptado, 3=Rechazado

ALTER TABLE dtes
  ADD COLUMN sii_status_id TINYINT NULL DEFAULT NULL AFTER folio,
  ADD COLUMN sii_track_id BIGINT NULL DEFAULT NULL AFTER sii_status_id,
  ADD COLUMN sii_rejection_reason TEXT NULL AFTER sii_track_id,
  ADD COLUMN sii_status_checked_at DATETIME NULL AFTER sii_rejection_reason,
  ADD COLUMN sii_status_alerted_at DATETIME NULL AFTER sii_status_checked_at;

CREATE INDEX idx_dtes_sii_status_id ON dtes (sii_status_id);
