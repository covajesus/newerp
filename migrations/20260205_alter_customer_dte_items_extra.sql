-- Columnas adicionales por ítem (código, nombre, unidad, descuento en pesos).
-- Ejecutar si ya creaste `customer_dte_items` sin estos campos.

ALTER TABLE `customer_dte_items`
  ADD COLUMN `item_code` VARCHAR(64) NULL DEFAULT NULL AFTER `description`,
  ADD COLUMN `item_name` VARCHAR(255) NULL DEFAULT NULL AFTER `item_code`,
  ADD COLUMN `unit_measure` VARCHAR(32) NULL DEFAULT NULL AFTER `item_name`,
  ADD COLUMN `discount_amount` INT NOT NULL DEFAULT 0 AFTER `unit_measure`;
