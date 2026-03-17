CREATE DATABASE wims;



CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE warehouse (
    warehouse_id SERIAL PRIMARY KEY,
    warehouse_name VARCHAR(150) NOT NULL,
    address TEXT,
    manager_name VARCHAR(150)
);

CREATE TABLE location (
    location_id SERIAL PRIMARY KEY,
    aisle VARCHAR(10) NOT NULL,
    shelf VARCHAR(10) NOT NULL,
    bin VARCHAR(10) NOT NULL,
    warehouse_id INTEGER NOT NULL,
    CONSTRAINT fk_location_warehouse
        FOREIGN KEY (warehouse_id) REFERENCES warehouse(warehouse_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_location_slot UNIQUE (aisle, shelf, bin, warehouse_id)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('Manager','Clerk','Procurement','Auditor')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE supplier (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    contact_person VARCHAR(150),
    phone VARCHAR(20),
    email VARCHAR(150),
    address TEXT
);

CREATE TABLE item (
    item_id SERIAL PRIMARY KEY,
    item_name VARCHAR(150) NOT NULL,
    description TEXT,
    quantity_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (quantity_in_stock >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    category_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    CONSTRAINT fk_item_category FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_item_location FOREIGN KEY (location_id) REFERENCES location(location_id) ON DELETE RESTRICT
);

CREATE TABLE item_supplier (
    item_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    supply_price NUMERIC(10,2) NOT NULL CHECK (supply_price >= 0),
    PRIMARY KEY (item_id, supplier_id),
    CONSTRAINT fk_is_item FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE CASCADE,
    CONSTRAINT fk_is_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id) ON DELETE CASCADE
);

CREATE TABLE stock_transaction (
    transaction_id SERIAL PRIMARY KEY,
    transaction_type VARCHAR(3) NOT NULL CHECK (transaction_type IN ('IN','OUT')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    CONSTRAINT fk_txn_item FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE RESTRICT,
    CONSTRAINT fk_txn_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE purchase_order (
    po_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_delivery DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Delivered','Cancelled')),
    supplier_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id) ON DELETE RESTRICT,
    CONSTRAINT fk_po_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE purchase_order_item (
    po_item_id SERIAL PRIMARY KEY,
    quantity_ordered INTEGER NOT NULL CHECK (quantity_ordered > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    po_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    CONSTRAINT fk_poi_po FOREIGN KEY (po_id) REFERENCES purchase_order(po_id) ON DELETE CASCADE,
    CONSTRAINT fk_poi_item FOREIGN KEY (item_id) REFERENCES item(item_id) ON DELETE RESTRICT
);

CREATE INDEX idx_item_category ON item(category_id);
CREATE INDEX idx_item_location ON item(location_id);
CREATE INDEX idx_txn_item ON stock_transaction(item_id);
CREATE INDEX idx_txn_user ON stock_transaction(user_id);
CREATE INDEX idx_po_supplier ON purchase_order(supplier_id);
CREATE INDEX idx_po_user ON purchase_order(user_id);
CREATE INDEX idx_poi_po ON purchase_order_item(po_id);
CREATE INDEX idx_poi_item ON purchase_order_item(item_id);

CREATE OR REPLACE FUNCTION record_transaction(
    p_type VARCHAR,
    p_quantity INTEGER,
    p_item_id INTEGER,
    p_user_id INTEGER,
    p_notes TEXT DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    current_stock INTEGER;
BEGIN
    SELECT quantity_in_stock INTO current_stock FROM item WHERE item_id = p_item_id FOR UPDATE;

    IF p_type = 'OUT' AND current_stock < p_quantity THEN
        RAISE EXCEPTION 'Insufficient stock for item %', p_item_id;
    END IF;

    INSERT INTO stock_transaction (transaction_type, quantity, item_id, user_id, notes)
    VALUES (p_type, p_quantity, p_item_id, p_user_id, p_notes);

    IF p_type = 'IN' THEN
        UPDATE item SET quantity_in_stock = quantity_in_stock + p_quantity WHERE item_id = p_item_id;
    ELSIF p_type = 'OUT' THEN
        UPDATE item SET quantity_in_stock = quantity_in_stock - p_quantity WHERE item_id = p_item_id;
    ELSE
        RAISE EXCEPTION 'Invalid transaction type: %', p_type;
    END IF;
END;
$$ LANGUAGE plpgsql;
