-- Crear tabla products basada en la estructura de la base de datos existente
CREATE TABLE `products` (
  `product_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `cost` int(11) NOT NULL,
  `price` int(11) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `category_id` int(11) DEFAULT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `brand` varchar(255) DEFAULT NULL,
  `model` varchar(255) DEFAULT NULL,
  `barcode` varchar(255) DEFAULT NULL,
  `status_id` int(11) DEFAULT 1,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`product_id`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `idx_category_id` (`category_id`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_status_id` (`status_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Crear tabla movements basada en la estructura de la base de datos existente
CREATE TABLE `movements` (
  `movement_id` int(11) NOT NULL AUTO_INCREMENT,
  `movement_type` varchar(50) NOT NULL COMMENT 'IN para entrada, OUT para salida',
  `reference_number` varchar(255) DEFAULT NULL,
  `description` text,
  `total_amount` int(11) NOT NULL DEFAULT 0,
  `branch_office_id` int(11) DEFAULT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `user_rut` varchar(255) NOT NULL,
  `status_id` int(11) DEFAULT 1,
  `movement_date` datetime NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`movement_id`),
  KEY `idx_movement_type` (`movement_type`),
  KEY `idx_branch_office_id` (`branch_office_id`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_user_rut` (`user_rut`),
  KEY `idx_status_id` (`status_id`),
  KEY `idx_movement_date` (`movement_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Actualizar tabla movements_products para que coincida con la estructura SQL proporcionada
ALTER TABLE `movements_products` 
ADD COLUMN `product_id` int(11) NOT NULL AFTER `movement_product_id`,
ADD COLUMN `movement_id` int(11) NOT NULL AFTER `product_id`,
ADD COLUMN `cost` int(11) NOT NULL AFTER `movement_id`,
ADD COLUMN `qty` int(11) NOT NULL AFTER `cost`,
ADD COLUMN `created_at` datetime DEFAULT CURRENT_TIMESTAMP AFTER `qty`;

-- Si la tabla movements_products no existe, créala con la estructura correcta
-- (Esta sección se puede usar si la tabla no existe)
/*
CREATE TABLE `movements_products` (
  `movement_product_id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `movement_id` int(11) NOT NULL,
  `cost` int(11) NOT NULL,
  `qty` int(11) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`movement_product_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_movement_id` (`movement_id`),
  FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE,
  FOREIGN KEY (`movement_id`) REFERENCES `movements` (`movement_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
*/

-- Insertar algunos datos de ejemplo para products
INSERT INTO `products` (`name`, `description`, `cost`, `price`, `stock`, `category_id`, `supplier_id`, `brand`, `model`, `barcode`, `status_id`) VALUES
('Producto Ejemplo 1', 'Descripción del producto ejemplo 1', 1000, 1500, 100, 1, 1, 'Marca A', 'Modelo X', '1234567890123', 1),
('Producto Ejemplo 2', 'Descripción del producto ejemplo 2', 2000, 3000, 50, 2, 2, 'Marca B', 'Modelo Y', '1234567890124', 1),
('Producto Ejemplo 3', 'Descripción del producto ejemplo 3', 500, 800, 200, 1, 1, 'Marca A', 'Modelo Z', '1234567890125', 1);

-- Insertar algunos datos de ejemplo para movements
INSERT INTO `movements` (`movement_type`, `reference_number`, `description`, `total_amount`, `branch_office_id`, `supplier_id`, `user_rut`, `status_id`, `movement_date`) VALUES
('IN', 'MOV-001', 'Entrada inicial de productos', 350000, 1, 1, '12345678-9', 1, NOW()),
('OUT', 'MOV-002', 'Salida de productos para venta', 45000, 1, NULL, '12345678-9', 1, NOW());

-- Insertar algunos datos de ejemplo para movements_products
INSERT INTO `movements_products` (`product_id`, `movement_id`, `cost`, `qty`) VALUES
(1, 1, 1000, 100),
(2, 1, 2000, 50),
(3, 1, 500, 200),
(1, 2, 1000, -30),
(3, 2, 500, -30);
