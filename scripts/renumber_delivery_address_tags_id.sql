-- =============================================================================
-- Renumera `id` de 1 a N en `delivery_address_tags` (mismo número de filas,
-- conservando el orden lógico por el `id` actual).
--
-- HAZ COPIA DE SEGURIDAD ANTES (mysqldump o export).
-- Si otra tabla tiene FK a delivery_address_tags.id, NO ejecutes esto o
-- actualiza/elimina esas referencias primero.
-- =============================================================================

SET @OLD_SQL_SAFE_UPDATES = @@SQL_SAFE_UPDATES;
SET SQL_SAFE_UPDATES = 0;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `delivery_address_tags__renum` LIKE `delivery_address_tags`;

INSERT INTO `delivery_address_tags__renum` (
  region_id,
  commune_id,
  branch_office,
  address,
  supervisor_rut,
  supervisor,
  phone,
  company_name,
  company_rut,
  company_phone,
  company_address,
  added_date,
  updated_date
)
SELECT
  region_id,
  commune_id,
  branch_office,
  address,
  supervisor_rut,
  supervisor,
  phone,
  company_name,
  company_rut,
  company_phone,
  company_address,
  added_date,
  updated_date
FROM `delivery_address_tags`
ORDER BY `id` ASC;

-- Comprueba: mismos conteos
-- SELECT COUNT(*) FROM delivery_address_tags; SELECT COUNT(*) FROM delivery_address_tags__renum;

DROP TABLE `delivery_address_tags`;

RENAME TABLE `delivery_address_tags__renum` TO `delivery_address_tags`;

SET @next := (SELECT IFNULL(MAX(id), 0) + 1 FROM `delivery_address_tags`);
SET @q := CONCAT('ALTER TABLE `delivery_address_tags` AUTO_INCREMENT = ', @next);
PREPARE stmt FROM @q;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET FOREIGN_KEY_CHECKS = 1;
SET SQL_SAFE_UPDATES = @OLD_SQL_SAFE_UPDATES;

-- Verificación: 1, 2, 3, ...
-- SELECT id, branch_office FROM delivery_address_tags ORDER BY id;
