-- Rename Spanish columns on received_inbox to English.
-- Safe to re-run: only renames if old names still exist.

SET @db := DATABASE();

SET @sql := (
  SELECT IF(
    COUNT(*) > 0,
    'ALTER TABLE `received_inbox` CHANGE COLUMN `ambiente` `environment` varchar(32) DEFAULT NULL',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'received_inbox' AND COLUMN_NAME = 'ambiente'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) > 0,
    'ALTER TABLE `received_inbox` CHANGE COLUMN `estado` `document_status` varchar(64) DEFAULT NULL',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'received_inbox' AND COLUMN_NAME = 'estado'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) > 0,
    'ALTER TABLE `received_inbox` CHANGE COLUMN `estado_sii` `sii_status` varchar(64) DEFAULT NULL',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'received_inbox' AND COLUMN_NAME = 'estado_sii'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(
    COUNT(*) > 0,
    'ALTER TABLE `received_inbox` CHANGE COLUMN `estado_acuse` `acknowledgment_status` varchar(64) DEFAULT NULL',
    'SELECT 1'
  )
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @db AND TABLE_NAME = 'received_inbox' AND COLUMN_NAME = 'estado_acuse'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
