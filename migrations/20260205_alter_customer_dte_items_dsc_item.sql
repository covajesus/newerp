-- Texto para nodo SII DscItem (detalle adicional de la línea). Opcional.
-- `description` sigue guardando el texto combinado para listados/impresos internos.

ALTER TABLE `customer_dte_items`
  ADD COLUMN `dsc_item` VARCHAR(500) NULL DEFAULT NULL COMMENT 'DscItem LibreDTE' AFTER `description`;
