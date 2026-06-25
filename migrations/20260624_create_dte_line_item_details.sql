CREATE TABLE IF NOT EXISTS `dte_line_item_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_detail` varchar(255) NOT NULL,
  `added_date` datetime DEFAULT NULL,
  `updated_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_dte_line_item_details_item_detail` (`item_detail`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
