-- Quotation email open tracking (1 = read, 0 = not read)
ALTER TABLE quotations
  ADD COLUMN email_read TINYINT NOT NULL DEFAULT 0 AFTER last_sent_channel,
  ADD COLUMN email_read_token VARCHAR(64) NULL DEFAULT NULL AFTER email_read,
  ADD COLUMN email_read_at DATETIME NULL DEFAULT NULL AFTER email_read_token;

CREATE UNIQUE INDEX uq_quotations_email_read_token ON quotations (email_read_token);
