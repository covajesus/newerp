CREATE TABLE IF NOT EXISTS `dte_line_item_names` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `item_name` VARCHAR(255) NOT NULL,
  `added_date` DATETIME NULL DEFAULT NULL,
  `updated_date` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dte_line_item_names_item_name` (`item_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
