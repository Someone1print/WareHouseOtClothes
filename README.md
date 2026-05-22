# 🏭 Clothes Factory Warehouse

Django project for the DBMS term project: a web application for managing
a garment-factory warehouse — raw materials, production, sales, budget,
salaries, loans and role-based access.

## 📋 Features

- **Reference data**: units of measurement, positions, employees, accounts.
- **Stock**: raw materials, finished products, recipes (ingredients).
- **Operations**: raw-material purchases, production, sales, salary payouts,
  business loans (with a 3-loan limit), production requests with a
  multi-stage workflow.
- **DB logic (MSSQL)**:
    - stored procedures `sp_check_budget`, `sp_create_purchase`;
    - trigger `trg_after_purchase` updating raw-material stock and budget;
    - views `v_raw_material_stock`, `v_finished_product_stock`,
      `v_materials_needed_for_production`.
- **RBAC**: director / accountant / warehouse / production / sales roles
  (`role_required`, `director_required` decorators).
- **Analytics dashboard**: top-sold products, revenue vs expenses, drill-down
  tables.
- **UI**: Bootstrap 5 with custom palette.

## 🚀 How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the database** (Microsoft SQL Server):
    - Make sure SQL Server is running and ODBC Driver 17 for SQL Server is installed.
    - Copy `.env` template and fill `DB_NAME`, `DB_HOST`, `DB_PORT`.
    - The connection uses Windows Authentication (`Trusted_Connection=yes`).

3. **Apply migrations** (creates 14 domain tables, 2 stored procedures,
   1 trigger and 3 views, then seeds workwear demo data):
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser** (the first director):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the dev server**:
   ```bash
   python manage.py runserver 8080
   ```

6. **Open the browser**:
   - <http://127.0.0.1:8080>

## 📂 Project Structure

- `warehouse/models.py` — database models.
- `warehouse/migrations/0002_create_sql_logic.py` — stored procedures,
  trigger and SQL views.
- `warehouse/views.py` — controllers (purchase, production, sale, salary,
  loan, analytics, production-request workflow).
- `warehouse/auth_views.py` — login / logout, account management.
- `warehouse/permissions.py` — RBAC decorators.
- `warehouse/templates/` — HTML templates (Bootstrap 5).
- `screenshots/` — UI and DB screenshots used by the term-project report.
- `build_term_project_report.py` — generates the term-project DOCX.
- `generate_report.py` — captures UI screenshots through Playwright.

## 📄 Term-project report

The compiled DOCX is committed to the root:
`DBMS_TermProject_Klyuchevsky_WarehouseOfClothes.docx`.
