# 🏭 Clothes Factory Warehouse

Django Project for Laboratory Work "Warehouse of Clothes on Production".

## 📋 Features
- **Entities**: Units, Positions, Employees, Raw Materials, Finished Products, Ingredients (Composition).
- **Transactions**: Raw Material Purchase, Product Sale, Production.
- **Logic**:
    - **Budget Control**: Stored Procedure checks budget before purchase.
    - **Stock Updates**: Trigger updates raw material stock and budget after purchase.
- **Reporting**: SQL Views for stock and material requirements.
- **UI**: Bootstrap 5 interface.

## 🚀 How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**:
   - Ensure PostgreSQL is running.
   - Create a database named `postgres` (or update `.env`).
   - Allow user `postgres` with password `123`.

3. **Apply Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Seed Data** (Optional but recommended):
   ```bash
   python manage.py populate_data
   ```

5. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run Server**:
   ```bash
   python manage.py runserver
   ```

7. **Open Browser**:
   - Go to [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 📂 Project Structure
- `warehouse/models.py`: Database models.
- `warehouse/migrations/0002_create_sql_logic.py`: **SQL Logic (Functions, Triggers, Views)**.
- `warehouse/views.py`: Logic for views, including Raw SQL calls.
- `warehouse/templates/`: HTML templates.
