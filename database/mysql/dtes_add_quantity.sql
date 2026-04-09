-- Boleta por cantidad (category_id = 3): unidades vendidas.
ALTER TABLE `dtes`
  ADD COLUMN `quantity` INT NULL DEFAULT NULL AFTER `category_id`;
