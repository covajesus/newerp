-- Ejecutar una vez en MySQL/MariaDB (tabla para cola pull-based de sincronización de cajas)
CREATE TABLE IF NOT EXISTS cashier_sync_commands (
  id INT AUTO_INCREMENT PRIMARY KEY,
  branch_office_id INT NOT NULL,
  cashier_id INT NOT NULL,
  batch_id VARCHAR(36) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pendiente',
  requester_wa_id VARCHAR(32) NOT NULL,
  action VARCHAR(50) NOT NULL DEFAULT 'sync_sales',
  created_at DATETIME NULL,
  started_at DATETIME NULL,
  completed_at DATETIME NULL,
  result_text TEXT NULL,
  error_text TEXT NULL,
  duration_ms INT NULL,
  INDEX idx_cashier_status (cashier_id, status),
  INDEX idx_batch (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
