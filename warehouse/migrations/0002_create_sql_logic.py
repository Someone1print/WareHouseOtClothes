from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                -- 1. Stored Procedure: Check Budget
                CREATE OR ALTER PROCEDURE sp_check_budget
                    @p_amount decimal(18,2),
                    @result int OUTPUT
                AS
                BEGIN
                    DECLARE @v_budget decimal(18,2);
                    
                    SELECT TOP 1 @v_budget = amount FROM warehouse_budget ORDER BY id ASC;
                    
                    IF @v_budget IS NULL
                        SET @result = 1;
                    ELSE IF @v_budget >= @p_amount
                        SET @result = 0;
                    ELSE
                        SET @result = 1;
                END;
                """,
                """
                -- 2. Stored Procedure: Create Purchase
                CREATE OR ALTER PROCEDURE sp_create_purchase
                    @p_raw_id int, 
                    @p_qty float, 
                    @p_amount float, 
                    @p_date datetime2, 
                    @p_employee_id int, 
                    @result int OUTPUT
                AS
                BEGIN
                    DECLARE @v_check int;

                    EXEC sp_check_budget @p_amount, @v_check OUTPUT;
                    
                    IF @v_check = 0
                    BEGIN
                        INSERT INTO warehouse_rawpurchase (raw_material_id, quantity, amount, date, employee_id)
                        VALUES (@p_raw_id, @p_qty, @p_amount, @p_date, @p_employee_id);
                        SET @result = 0;
                    END
                    ELSE
                    BEGIN
                        SET @result = 1;
                    END
                END;
                """,
                """
                -- 3 & 4. Trigger Function: Update Budget and Stock
                CREATE OR ALTER TRIGGER trg_after_purchase
                ON warehouse_rawpurchase
                AFTER INSERT
                AS
                BEGIN
                    -- Deduct from Budget (assuming 1 row insert for simplicity, typical in Django ORM unless bulk_create)
                    UPDATE warehouse_budget
                    SET amount = amount - i.total_amount
                    FROM warehouse_budget
                    CROSS JOIN (SELECT SUM(amount) as total_amount FROM inserted) i
                    WHERE id = (SELECT TOP 1 id FROM warehouse_budget ORDER BY id ASC);
                    
                    -- Update RawMaterial stock
                    UPDATE r
                    SET quantity = r.quantity + i.total_qty,
                        amount = r.amount + i.total_amount
                    FROM warehouse_rawmaterial r
                    JOIN (
                        SELECT raw_material_id, SUM(quantity) as total_qty, SUM(amount) as total_amount 
                        FROM inserted 
                        GROUP BY raw_material_id
                    ) i ON r.id = i.raw_material_id;
                END;
                """,
                """
                -- 5. View: Raw Material Stock
                CREATE OR ALTER VIEW v_raw_material_stock AS
                SELECT 
                    r.id as raw_id,
                    r.name as raw_name,
                    u.name as unit_name,
                    r.quantity,
                    r.amount
                FROM warehouse_rawmaterial r
                JOIN warehouse_unit u ON r.unit_id = u.id;
                """,
                """
                -- 6. View: Finished Product Stock
                CREATE OR ALTER VIEW v_finished_product_stock AS
                SELECT 
                    p.id as product_id,
                    p.name as product_name,
                    u.name as unit_name,
                    p.quantity,
                    p.amount
                FROM warehouse_finishedproduct p
                JOIN warehouse_unit u ON p.unit_id = u.id;
                """,
                """
                -- 7. View: Materials Needed for Production
                CREATE OR ALTER VIEW v_materials_needed_for_production AS
                SELECT 
                    p.id as product_id,
                    p.name as product_name,
                    r.id as raw_id,
                    r.name as raw_name,
                    i.quantity as ingredient_qty
                FROM warehouse_ingredient i
                JOIN warehouse_finishedproduct p ON i.product_id = p.id
                JOIN warehouse_rawmaterial r ON i.raw_material_id = r.id;
                """
            ],
            reverse_sql=[
                "DROP VIEW IF EXISTS v_materials_needed_for_production;",
                "DROP VIEW IF EXISTS v_finished_product_stock;",
                "DROP VIEW IF EXISTS v_raw_material_stock;",
                "DROP TRIGGER IF EXISTS trg_after_purchase;",
                "DROP PROCEDURE IF EXISTS sp_create_purchase;",
                "DROP PROCEDURE IF EXISTS sp_check_budget;"
            ]
        )
    ]
