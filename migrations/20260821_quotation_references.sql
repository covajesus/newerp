-- Referencias de cotizaciones (mismo shape que dte_references)
CREATE TABLE IF NOT EXISTS `quotation_references` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `quotation_id` INT NOT NULL,
  `reference_type_id` VARCHAR(16) DEFAULT NULL,
  `reference_date_id` VARCHAR(255) DEFAULT NULL,
  `reference_code` VARCHAR(64) DEFAULT NULL,
  `reference_description` VARCHAR(512) DEFAULT NULL,
  `added_date` DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_quotation_references_quotation` (`quotation_id`),
  CONSTRAINT `fk_quotation_references_quotation`
    FOREIGN KEY (`quotation_id`) REFERENCES `quotations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
