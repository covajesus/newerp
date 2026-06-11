-- WhatsApp template for v2 DTE emission with online payment (envio_dte_v3)
-- Same pattern as id=1 (envio_dte), id=2 (payment notify), id=7 (folio alerts), etc.
INSERT INTO whatsapp_templates (id, title, template)
VALUES (8, 'envio_dte_v3', 'envio_dte_v3')
ON DUPLICATE KEY UPDATE title = VALUES(title), template = VALUES(template);
