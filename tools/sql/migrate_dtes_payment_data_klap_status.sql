-- Run once if dtes_payment_data was created with klap_status column
ALTER TABLE dtes_payment_data
  CHANGE COLUMN klap_status payment_status VARCHAR(32) NULL;
