-- Crear tabla tags
CREATE TABLE IF NOT EXISTS `tags` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `branch_office_id` INT NULL,
  `tag` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `color` VARCHAR(50) NULL,
  `visibility_id` INT NOT NULL DEFAULT 1,
  `added_date` DATETIME NULL,
  `updated_date` DATETIME NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_branch_office_id` (`branch_office_id` ASC),
  INDEX `idx_visibility_id` (`visibility_id` ASC),
  CONSTRAINT `fk_tags_branch_office`
    FOREIGN KEY (`branch_office_id`)
    REFERENCES `branch_offices` (`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
