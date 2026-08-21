-- WhatsApp template for subscriber quotations (Meta name: quotation)
-- Same pattern as id=1 (envio_dte), id=8 (envio_dte_v3), etc.
-- Header: document PDF | Body: {{1}}..{{6}} (n°, fecha, monto, contacto, teléfono, email)
INSERT INTO whatsapp_templates (id, title, template)
VALUES (9, 'quotation', 'quotation')
ON DUPLICATE KEY UPDATE title = VALUES(title), template = VALUES(template);
