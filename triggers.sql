
-- WIMS TRIGGERS AND AUDIT LOGS
-- They must be run after the schema has already been run locally.


-- 1. AUDIT TABLE
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INTEGER,
    acted_by_user_id INTEGER,
    action_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB,
    CONSTRAINT fk_audit_user
        FOREIGN KEY (acted_by_user_id) REFERENCES users(user_id)
        ON DELETE SET NULL
);


-- 2. TRIGGER FUNCTION: PREVENT NEGATIVE STOCK

CREATE OR REPLACE FUNCTION prevent_negative_stock()
RETURNS TRIGGER AS $$
DECLARE
    current_stock INTEGER;
BEGIN
    SELECT quantity_in_stock INTO current_stock
    FROM item
    WHERE item_id = NEW.item_id;

    IF NEW.transaction_type = 'OUT' AND current_stock < NEW.quantity THEN
        RAISE EXCEPTION 'Cannot dispatch more than current stock for item_id %', NEW.item_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_negative_stock ON stock_transaction;

CREATE TRIGGER trg_prevent_negative_stock
BEFORE INSERT ON stock_transaction
FOR EACH ROW
EXECUTE FUNCTION prevent_negative_stock();


-- 3. TRIGGER FUNCTION: APPLY STOCK TRANSACTION

CREATE OR REPLACE FUNCTION apply_stock_transaction()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.transaction_type = 'IN' THEN
        UPDATE item
        SET quantity_in_stock = quantity_in_stock + NEW.quantity
        WHERE item_id = NEW.item_id;

    ELSIF NEW.transaction_type = 'OUT' THEN
        UPDATE item
        SET quantity_in_stock = quantity_in_stock - NEW.quantity
        WHERE item_id = NEW.item_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_apply_stock_transaction ON stock_transaction;

CREATE TRIGGER trg_apply_stock_transaction
AFTER INSERT ON stock_transaction
FOR EACH ROW
EXECUTE FUNCTION apply_stock_transaction();

-- 4. TRIGGER FUNCTION: AUDIT STOCK TRANSACTIONS
-- Since stock_transaction already has user_id, this one is easy

CREATE OR REPLACE FUNCTION audit_stock_transaction()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        operation,
        record_id,
        acted_by_user_id,
        old_data,
        new_data
    )
    VALUES (
        'stock_transaction',
        TG_OP,
        NEW.transaction_id,
        NEW.user_id,
        NULL,
        to_jsonb(NEW)
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_stock_transaction ON stock_transaction;

CREATE TRIGGER trg_audit_stock_transaction
AFTER INSERT ON stock_transaction
FOR EACH ROW
EXECUTE FUNCTION audit_stock_transaction();


-- 5. TRIGGER FUNCTION: AUDIT PURCHASE ORDERS
-- purchase_order already stores user_id too

CREATE OR REPLACE FUNCTION audit_purchase_order()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (
            table_name, operation, record_id, acted_by_user_id, old_data, new_data
        )
        VALUES (
            'purchase_order',
            TG_OP,
            NEW.po_id,
            NEW.user_id,
            NULL,
            to_jsonb(NEW)
        );
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (
            table_name, operation, record_id, acted_by_user_id, old_data, new_data
        )
        VALUES (
            'purchase_order',
            TG_OP,
            NEW.po_id,
            NEW.user_id,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (
            table_name, operation, record_id, acted_by_user_id, old_data, new_data
        )
        VALUES (
            'purchase_order',
            TG_OP,
            OLD.po_id,
            OLD.user_id,
            to_jsonb(OLD),
            NULL
        );
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_purchase_order ON purchase_order;

CREATE TRIGGER trg_audit_purchase_order
AFTER INSERT OR UPDATE OR DELETE ON purchase_order
FOR EACH ROW
EXECUTE FUNCTION audit_purchase_order();


-- 6. GENERIC AUDIT FUNCTION
-- This handles item, supplier, and users
-- It reads current Flask user from PostgreSQL session variable:
-- app.current_user_id

CREATE OR REPLACE FUNCTION generic_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    app_user_id INTEGER;
    target_record_id INTEGER;
BEGIN
    app_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;

    IF TG_OP = 'INSERT' THEN
        target_record_id := COALESCE(
            (to_jsonb(NEW)->>'item_id')::INTEGER,
            (to_jsonb(NEW)->>'supplier_id')::INTEGER,
            (to_jsonb(NEW)->>'user_id')::INTEGER,
            NULL
        );

        INSERT INTO audit_log(table_name, operation, record_id, acted_by_user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, target_record_id, app_user_id, NULL, to_jsonb(NEW));

        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        target_record_id := COALESCE(
            (to_jsonb(NEW)->>'item_id')::INTEGER,
            (to_jsonb(NEW)->>'supplier_id')::INTEGER,
            (to_jsonb(NEW)->>'user_id')::INTEGER,
            NULL
        );

        INSERT INTO audit_log(table_name, operation, record_id, acted_by_user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, target_record_id, app_user_id, to_jsonb(OLD), to_jsonb(NEW));

        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        target_record_id := COALESCE(
            (to_jsonb(OLD)->>'item_id')::INTEGER,
            (to_jsonb(OLD)->>'supplier_id')::INTEGER,
            (to_jsonb(OLD)->>'user_id')::INTEGER,
            NULL
        );

        INSERT INTO audit_log(table_name, operation, record_id, acted_by_user_id, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, target_record_id, app_user_id, to_jsonb(OLD), NULL);

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 7. APPLY GENERIC AUDIT TRIGGERS

DROP TRIGGER IF EXISTS trg_audit_item ON item;
CREATE TRIGGER trg_audit_item
AFTER INSERT OR UPDATE OR DELETE ON item
FOR EACH ROW
EXECUTE FUNCTION generic_audit_trigger();

DROP TRIGGER IF EXISTS trg_audit_supplier ON supplier;
CREATE TRIGGER trg_audit_supplier
AFTER INSERT OR UPDATE OR DELETE ON supplier
FOR EACH ROW
EXECUTE FUNCTION generic_audit_trigger();

DROP TRIGGER IF EXISTS trg_audit_users ON users;
CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW
EXECUTE FUNCTION generic_audit_trigger();