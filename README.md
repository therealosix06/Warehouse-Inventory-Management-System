# WIMS Flask + PostgreSQL App

This is a complete mini app for the Warehouse Inventory Management System project. It is designed so your group can **demo the software** and also **explain the database design cleanly**.

## What the app covers

- Inventory items, categories, warehouses, locations, suppliers, purchase orders, users, and stock transactions
- Many-to-many relationship between `Item` and `Supplier` through `item_supplier`
- One-to-many relationships such as:
  - `Category -> Item`
  - `Warehouse -> Location`
  - `Location -> Item`
  - `PurchaseOrder -> PurchaseOrderItem`
  - `User -> StockTransaction`
- Role-based login for Manager, Clerk, Procurement, and Auditor
- Low-stock report, stock value report, and purchase order history
- PostgreSQL schema with PKs, FKs, `CHECK`, `UNIQUE`, indexes, and a PL/pgSQL function

## Suggested demo flow

1. Login as Manager or Clerk
2. Show dashboard metrics and low-stock alerts
3. Add a new item
4. Record a stock IN or OUT transaction and show stock changing
5. Create a purchase order with multiple line items
6. Open reports and explain the joins
7. Open `docs/ERD.md` and your SQL schema while presenting the relationships

## Project structure

- `app/models.py` → ORM models matching the relational schema
- `app/routes.py` → business logic and screens
- `schema.sql` → PostgreSQL schema + stored function
- `seed.sql` → project sample data
- `docs/ERD.md` → Mermaid ERD for quick diagram generation

## Setup

### 1. Create the database

```sql
CREATE DATABASE wims;
```

### 2. Create a virtual environment and install packages

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Set environment variables

Copy `.env.example` and adjust the PostgreSQL connection string.

Example:

```bash
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/wims
set SECRET_KEY=change-this
```

On PowerShell:

```powershell
$env:DATABASE_URL="postgresql://postgres:postgres@localhost:5432/wims"
$env:SECRET_KEY="change-this"
```

### 4. Create tables

You have two valid paths:

#### Path A: use the raw PostgreSQL SQL
Run `schema.sql`, then `seed.sql`.

#### Path B: use Flask ORM for quick demo data

```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> app.app_context().push()
>>> db.create_all()
>>> exit()
python run.py
```

Then visit `/setup-demo` once.

## Demo login

After running `/setup-demo`:

- `kwame@wims.com / password123` → Manager
- `ama@wims.com / password123` → Clerk
- `kofi@wims.com / password123` → Procurement
- `efua@wims.com / password123` → Auditor

## What to explain for marks

### 1NF
No repeating groups. Supplier links are not crammed into the item table.

### 2NF
`item_supplier` has a composite key, and `supply_price` depends on both `item_id` and `supplier_id`.

### 3NF
Category, supplier, warehouse, and location details are separated into their own tables to avoid transitive dependencies.

### Integrity
- PKs uniquely identify rows
- FKs enforce valid references
- `CHECK` constraints stop nonsense like negative stock or invalid roles
- `UNIQUE` on user email and category name prevents duplicates

## Hard truth

Do not just submit the code and pray to the gods of partial credit. You and your group need to understand:
- why each table exists
- why `item_supplier` is a junction table
- why transaction history is stored separately
- how the reports are built from joins
- why PostgreSQL constraints matter

That is the difference between “we built an app” and “we actually understand database design.”
