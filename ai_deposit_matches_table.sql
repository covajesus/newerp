-- =====================================================
-- Tabla para almacenar matches de depósitos con IA
-- =====================================================

CREATE TABLE IF NOT EXISTS `ai_deposit_matches` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `bank_statement_id` INT(11) DEFAULT NULL COMMENT 'ID del registro en bank_statements',
  `transbank_statement_id` INT(11) DEFAULT NULL COMMENT 'ID del registro en transbank_statements',
  `deposit_id` INT(11) DEFAULT NULL COMMENT 'ID del depósito encontrado (FK a deposits)',
  
  -- Datos del Excel (Bank Statement)
  `excel_deposit_number` VARCHAR(255) DEFAULT NULL COMMENT 'Número de depósito del Excel',
  `excel_branch_office` VARCHAR(255) DEFAULT NULL COMMENT 'Sucursal del Excel (texto)',
  `excel_amount` INT(11) DEFAULT NULL COMMENT 'Monto del Excel',
  `excel_date` VARCHAR(255) DEFAULT NULL COMMENT 'Fecha del Excel',
  
  -- Datos del Depósito en BD
  `db_deposit_id` INT(11) DEFAULT NULL COMMENT 'ID del depósito en BD',
  `db_branch_office_id` INT(11) DEFAULT NULL COMMENT 'ID de sucursal en BD',
  `db_branch_office_name` VARCHAR(255) DEFAULT NULL COMMENT 'Nombre de sucursal en BD',
  `db_payment_number` INT(11) DEFAULT NULL COMMENT 'Número de pago en BD',
  `db_collection_amount` INT(11) DEFAULT NULL COMMENT 'Monto de cobro en BD',
  `db_deposited_amount` INT(11) DEFAULT NULL COMMENT 'Monto depositado en BD',
  `db_collection_date` VARCHAR(255) DEFAULT NULL COMMENT 'Fecha de cobro en BD',
  
  -- Información del matching
  `match_confidence` DECIMAL(5,2) DEFAULT NULL COMMENT 'Confianza del match (0-100)',
  `match_reason` TEXT DEFAULT NULL COMMENT 'Razón del match explicada por IA',
  `match_type` ENUM('exact', 'ai_suggested', 'manual') DEFAULT 'ai_suggested' COMMENT 'Tipo de match',
  `is_confirmed` TINYINT(1) DEFAULT 0 COMMENT 'Si el match fue confirmado manualmente',
  `is_rejected` TINYINT(1) DEFAULT 0 COMMENT 'Si el match fue rechazado',
  
  -- Metadata
  `ai_model_used` VARCHAR(100) DEFAULT NULL COMMENT 'Modelo de IA usado (ej: gpt-4, gpt-3.5-turbo)',
  `ai_prompt_tokens` INT(11) DEFAULT NULL COMMENT 'Tokens usados en el prompt',
  `ai_completion_tokens` INT(11) DEFAULT NULL COMMENT 'Tokens usados en la respuesta',
  `processing_time_ms` INT(11) DEFAULT NULL COMMENT 'Tiempo de procesamiento en milisegundos',
  
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by_user_id` INT(11) DEFAULT NULL COMMENT 'ID del usuario que creó el match',
  `confirmed_by_user_id` INT(11) DEFAULT NULL COMMENT 'ID del usuario que confirmó el match',
  
  PRIMARY KEY (`id`),
  KEY `idx_bank_statement_id` (`bank_statement_id`),
  KEY `idx_transbank_statement_id` (`transbank_statement_id`),
  KEY `idx_deposit_id` (`deposit_id`),
  KEY `idx_excel_deposit_number` (`excel_deposit_number`),
  KEY `idx_db_deposit_id` (`db_deposit_id`),
  KEY `idx_match_confidence` (`match_confidence`),
  KEY `idx_is_confirmed` (`is_confirmed`),
  KEY `idx_is_rejected` (`is_rejected`),
  KEY `idx_created_at` (`created_at`),
  
  CONSTRAINT `fk_ai_match_bank_statement` 
    FOREIGN KEY (`bank_statement_id`) 
    REFERENCES `bank_statements` (`id`) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE,
    
  CONSTRAINT `fk_ai_match_deposit` 
    FOREIGN KEY (`deposit_id`) 
    REFERENCES `deposits` (`id`) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE,
    
  CONSTRAINT `fk_ai_match_transbank_statement` 
    FOREIGN KEY (`transbank_statement_id`) 
    REFERENCES `transbank_statements` (`id`) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices adicionales para optimización
CREATE INDEX `idx_match_type_confirmed` ON `ai_deposit_matches` (`match_type`, `is_confirmed`);
CREATE INDEX `idx_excel_db_deposit_number` ON `ai_deposit_matches` (`excel_deposit_number`, `db_payment_number`);
