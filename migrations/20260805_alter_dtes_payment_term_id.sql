-- Condición de pago de factura (SII FmaPago): 1 Contado, 2 Crédito.
-- Default Contado para filas existentes.

ALTER TABLE `dtes`
  ADD COLUMN `payment_term_id` TINYINT NOT NULL DEFAULT 1 AFTER `payment_type_id`;
