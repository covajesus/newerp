-- Facturas cliente (dtes tipo 33): categoría y múltiples líneas de referencia SII.
-- Ejecutar en la misma base que usa newerp (tabla `dtes`).

-- Categoría del documento: 1 = sin referencias, 2 = con referencias (según front).
-- Columnas resumen en dtes: ver migrate_dtes_reference_summary_columns.sql si vienes de shopping_order_*.
ALTER TABLE `dtes`
  ADD COLUMN `category_id` INT NULL DEFAULT NULL;

CREATE TABLE IF NOT EXISTS `dte_references` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `dte_id` INT NOT NULL,
  `reference_type_id` VARCHAR(16) NULL DEFAULT NULL COMMENT 'Código SII ej. 33, 34, 801',
  `reference_date_id` VARCHAR(255) NULL DEFAULT NULL COMMENT 'Folio o N° doc. ref.',
  `reference_code` VARCHAR(64) NULL DEFAULT NULL COMMENT 'Fecha referencia (YYYY-MM-DD)',
  `reference_description` VARCHAR(512) NULL DEFAULT NULL COMMENT 'Razón referencia',
  `added_date` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_dte_references_dte_id` (`dte_id`),
  CONSTRAINT `fk_dte_references_dte`
    FOREIGN KEY (`dte_id`) REFERENCES `dtes` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Si la columna se llamaba referenced_type_id, renombrar:
-- ALTER TABLE `dte_references` CHANGE COLUMN `referenced_type_id` `reference_type_id` VARCHAR(16) NULL DEFAULT NULL COMMENT 'Código SII ej. 33, 34, 801';

-- Si ya tenías la versión anterior con sort_order y nombres viejos, migrar a mano o recrear la tabla.

-- Datos viejos: alinear category_id con facturas que tenían referencias (ajustar según tu negocio):
-- UPDATE dtes SET category_id = 2 WHERE category_id IS NULL AND EXISTS (SELECT 1 FROM dte_references r WHERE r.dte_id = dtes.id);
-- UPDATE dtes d INNER JOIN dte_references r ON r.dte_id = d.id SET d.category_id = 2 WHERE d.category_id IS NULL;
