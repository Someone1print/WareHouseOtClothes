from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- 1. Stored Procedure: Check Budget
            CREATE OR REPLACE FUNCTION sp_check_budget(p_amount numeric, OUT result int)
            RETURNS int AS $$
            DECLARE
                v_budget numeric;
            BEGIN
                -- Find the singleton budget (or the one with min ID)
                SELECT amount INTO v_budget FROM warehouse_budget ORDER BY id ASC LIMIT 1;
                
                IF v_budget IS NULL THEN
                    result := 1; -- No budget record
                ELSIF v_budget >= p_amount THEN
                    result := 0; -- Enough budget
                ELSE
                    result := 1; -- Not enough
                END IF;
            END;
            $$ LANGUAGE plpgsql;

            -- 2. Stored Procedure: Create Purchase
            CREATE OR REPLACE FUNCTION sp_create_purchase(
                p_raw_id int, 
                p_qty numeric, 
                p_amount numeric, 
                p_date timestamp, 
                p_employee_id int, 
                OUT result int
            )
            RETURNS int AS $$
            DECLARE
                v_check int;
            BEGIN
                -- Check budget first
                SELECT * INTO v_check FROM sp_check_budget(p_amount);
                
                IF v_check = 0 THEN
                    -- Insert into RawPurchase
                    INSERT INTO warehouse_rawpurchase (raw_material_id, quantity, amount, date, employee_id)
                    VALUES (p_raw_id, p_qty, p_amount, p_date, p_employee_id);
                    result := 0; -- Success
                ELSE
                    result := 1; -- Failed (insufficient budget)
                END IF;
            END;
            $$ LANGUAGE plpgsql;

            -- 3. Trigger Function: Update Budget and Stock
            CREATE OR REPLACE FUNCTION trg_func_after_purchase()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Deduct from Budget
                UPDATE warehouse_budget
                SET amount = amount - NEW.amount
                WHERE id = (SELECT id FROM warehouse_budget ORDER BY id ASC LIMIT 1);
                
                -- Update RawMaterial stock
                UPDATE warehouse_rawmaterial
                SET quantity = quantity + NEW.quantity,
                    amount = amount + NEW.amount
                WHERE id = NEW.raw_material_id;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            -- 4. Trigger Definition
            DROP TRIGGER IF EXISTS trg_after_purchase ON warehouse_rawpurchase;
            CREATE TRIGGER trg_after_purchase
            AFTER INSERT ON warehouse_rawpurchase
            FOR EACH ROW
            EXECUTE FUNCTION trg_func_after_purchase();

            -- 5. View: Raw Material Stock
            CREATE OR REPLACE VIEW v_raw_material_stock AS
            SELECT 
                r.id as raw_id,
                r.name as raw_name,
                u.name as unit_name,
                r.quantity,
                r.amount
            FROM warehouse_rawmaterial r
            JOIN warehouse_unit u ON r.unit_id = u.id;

            -- 6. View: Finished Product Stock
            CREATE OR REPLACE VIEW v_finished_product_stock AS
            SELECT 
                p.id as product_id,
                p.name as product_name,
                u.name as unit_name,
                p.quantity,
                p.amount
            FROM warehouse_finishedproduct p
            JOIN warehouse_unit u ON p.unit_id = u.id;

            -- 7. View: Materials Needed for Production
            CREATE OR REPLACE VIEW v_materials_needed_for_production AS
            SELECT 
                p.id as product_id,
                p.name as product_name,
                r.id as raw_id,
                r.name as raw_name,
                i.quantity as ingredient_qty
            FROM warehouse_ingredient i
            JOIN warehouse_finishedproduct p ON i.product_id = p.id
            JOIN warehouse_rawmaterial r ON i.raw_material_id = r.id;
            """,
            reverse_sql="""
            DROP VIEW IF EXISTS v_materials_needed_for_production;
            DROP VIEW IF EXISTS v_finished_product_stock;
            DROP VIEW IF EXISTS v_raw_material_stock;
            DROP TRIGGER IF EXISTS trg_after_purchase ON warehouse_rawpurchase;
            DROP FUNCTION IF EXISTS trg_func_after_purchase;
            DROP FUNCTION IF EXISTS sp_create_purchase;
            DROP FUNCTION IF EXISTS sp_check_budget;
            """
        )
    ]
