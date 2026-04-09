-- Tabla para datos de remitente/destino en etiquetas de envío (sucursales / supervisores).
--
-- Por defecto SIN claves foráneas: evita el error 1822 cuando `regions` (o `communes`)
-- no es InnoDB o `id` no tiene índice PK/UNIQUE. La app (SQLAlchemy) sigue usando las
-- relaciones a nivel de modelo.
--
-- Para tener FK en MySQL después de arreglar las tablas padre, ejecute el bloque al final.

CREATE TABLE IF NOT EXISTS delivery_address_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT NOT NULL,
    commune_id INT NOT NULL,
    branch_office VARCHAR(512) NOT NULL,
    address VARCHAR(1024) NOT NULL,
    supervisor_rut VARCHAR(32) NOT NULL,
    supervisor VARCHAR(512) NOT NULL,
    phone VARCHAR(64) NULL,
    company_name VARCHAR(512) NOT NULL,
    company_rut VARCHAR(64) NOT NULL,
    company_phone VARCHAR(64) NOT NULL,
    company_address VARCHAR(1024) NOT NULL,
    added_date DATETIME NULL,
    updated_date DATETIME NULL,
    INDEX idx_delivery_address_tags_region (region_id),
    INDEX idx_delivery_address_tags_commune (commune_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Si obtuvo 1822 antes: diagnóstico en `regions`
--
--   SHOW CREATE TABLE regions\G
--   SHOW INDEX FROM regions;
--
-- Suele bastar:
--   ALTER TABLE regions ENGINE=InnoDB;
--   ALTER TABLE communes ENGINE=InnoDB;
--
-- Si `id` no es PRIMARY KEY ni UNIQUE, hay que alinear el esquema (no forzar PK duplicada).
--
-- Luego puede añadir FK (falle si ya existen constraints con el mismo nombre):
--
-- ALTER TABLE delivery_address_tags
--     ADD CONSTRAINT fk_delivery_address_tags_region
--         FOREIGN KEY (region_id) REFERENCES regions (id),
--     ADD CONSTRAINT fk_delivery_address_tags_commune
--         FOREIGN KEY (commune_id) REFERENCES communes (id);
--
-- ---------------------------------------------------------------------------
-- Alternativa: CREATE con FK desde cero (solo si regions/communes ya cumplen requisitos):
--
-- CREATE TABLE IF NOT EXISTS delivery_address_tags (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     region_id INT NOT NULL,
--     commune_id INT NOT NULL,
--     branch_office VARCHAR(512) NOT NULL,
--     address VARCHAR(1024) NOT NULL,
--     supervisor_rut VARCHAR(32) NOT NULL,
--     supervisor VARCHAR(512) NOT NULL,
--     phone VARCHAR(64) NULL,
--     company_name VARCHAR(512) NOT NULL,
--     company_rut VARCHAR(64) NOT NULL,
--     company_phone VARCHAR(64) NOT NULL,
--     company_address VARCHAR(1024) NOT NULL,
--     added_date DATETIME NULL,
--     updated_date DATETIME NULL,
--     CONSTRAINT fk_delivery_address_tags_region
--         FOREIGN KEY (region_id) REFERENCES regions(id),
--     CONSTRAINT fk_delivery_address_tags_commune
--         FOREIGN KEY (commune_id) REFERENCES communes(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Datos de ejemplo (ajuste region_id y commune_id a filas reales):
--
--   SELECT id, region FROM regions ORDER BY id;
--   SELECT id, commune, region_id FROM communes ORDER BY region_id, id;

INSERT INTO delivery_address_tags (
    region_id,
    commune_id,
    branch_office,
    address,
    supervisor_rut,
    supervisor,
    phone,
    company_name,
    company_rut,
    company_phone,
    company_address,
    added_date,
    updated_date
) VALUES
(
    1,
    1,
    'Sucursal Centro',
    'Av. Principal 123, Local 4',
    '12.345.678-9',
    'Juan Pérez González',
    '+56912345678',
    'Empresa Ejemplo SpA',
    '76.543.210-K',
    '+56221234567',
    'Av. Matriz 456, Oficina 701',
    NOW(),
    NOW()
);
