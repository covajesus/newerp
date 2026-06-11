-- Payment return / webhook data for v2 DTEs
CREATE TABLE IF NOT EXISTS dtes_payment_data (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dte_id INT NULL,
  customer_id INT NULL,
  payment_type_id INT NULL,
  branch_office_id INT NULL,
  folio INT NULL,
  reference_id VARCHAR(100) NOT NULL,
  order_id VARCHAR(128) NOT NULL,
  payment_status VARCHAR(32) NULL,
  amount INT NULL,
  rut VARCHAR(32) NULL,
  raw_payload TEXT NULL,
  added_date DATETIME NULL,
  updated_date DATETIME NULL,
  UNIQUE KEY uq_dtes_payment_data_order_id (order_id),
  KEY idx_dtes_payment_data_folio (folio),
  KEY idx_dtes_payment_data_reference_id (reference_id),
  KEY idx_dtes_payment_data_dte_id (dte_id),
  KEY idx_dtes_payment_data_customer_id (customer_id),
  KEY idx_dtes_payment_data_branch_office_id (branch_office_id)
);
