INSERT INTO category (category_name, description) VALUES
('Electronics', 'Electronic components and devices'),
('Office Supplies', 'Stationery and office consumables'),
('Industrial Tools', 'Mechanical and hand tools'),
('Perishables', 'Items with a limited shelf life'),
('Packaging', 'Boxes, wrapping, and sealing materials');

INSERT INTO warehouse (warehouse_name, address, manager_name) VALUES
('Main Warehouse', '14 Industrial Avenue, Tema', 'Kwame Asante'),
('North Storage Facility', '3 Ring Road, Accra', 'Abena Mensah');

INSERT INTO location (aisle, shelf, bin, warehouse_id) VALUES
('A','1','01',1), ('A','1','02',1), ('A','2','01',1),
('B','1','01',1), ('B','2','03',2), ('C','1','01',2);



INSERT INTO supplier (supplier_name, contact_person, phone, email, address) VALUES
('TechSource Ltd', 'James Osei', '024-111-2233', 'james@techsource.com', 'Accra, Ghana'),
('OfficeWorld Ghana', 'Adwoa Frimpong', '055-444-5566', 'adwoa@officeworld.com', 'Kumasi, Ghana'),
('IndustroParts Co', 'Yaw Mensah', '020-777-8899', 'yaw@industro.com', 'Takoradi, Ghana');

INSERT INTO item (item_name, description, quantity_in_stock, reorder_level, unit_price, category_id, location_id) VALUES
('USB-C Cable 2m', 'High-speed USB-C charging cable', 150, 20, 12.50, 1, 1),
('A4 Paper Ream', '500 sheets per ream, 80gsm', 300, 50, 8.00, 2, 2),
('Cordless Drill', '18V cordless drill with battery', 40, 5, 120.00, 3, 3),
('Bubble Wrap Roll', '50m roll of bubble wrap', 80, 15, 25.00, 5, 4),
('AA Batteries Pack', 'Pack of 10 AA alkaline batteries', 200, 30, 6.00, 1, 5),
('Ballpoint Pens Box', 'Box of 50 blue ballpoint pens', 120, 25, 4.50, 2, 6);

INSERT INTO item_supplier (item_id, supplier_id, supply_price) VALUES
(1,1,9.00),(2,2,5.50),(3,3,90.00),(4,3,18.00),(5,1,4.00),(6,2,3.00),(3,1,95.00);

INSERT INTO purchase_order (order_date, expected_delivery, status, supplier_id, user_id) VALUES
('2026-03-01','2026-03-07','Delivered',1,3),
('2026-03-05','2026-03-12','Pending',2,3),
('2026-03-08','2026-03-15','Pending',3,3);

INSERT INTO purchase_order_item (quantity_ordered, unit_price, po_id, item_id) VALUES
(100,9.00,1,1),(50,4.00,1,5),(200,5.50,2,2),(100,3.00,2,6),(20,90.00,3,3),(30,18.00,3,4);

INSERT INTO stock_transaction (transaction_type, quantity, transaction_date, notes, item_id, user_id) VALUES
('IN', 100,'2026-03-07 09:00:00','Received from PO #1 - TechSource',1,2),
('IN', 50,'2026-03-07 09:30:00','Received from PO #1 - TechSource',5,2),
('OUT', 30,'2026-03-08 11:00:00','Dispatched to dispatch bay 3',1,2),
('OUT', 10,'2026-03-09 14:00:00','Internal use - admin department',2,2),
('IN', 60,'2026-03-09 15:00:00','Emergency restock from supplier',3,2);
