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