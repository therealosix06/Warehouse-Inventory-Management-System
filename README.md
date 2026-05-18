# WIMS — Warehouse Inventory Management System

WIMS is a Flask-based warehouse inventory management system built to help manage products, stock levels, suppliers, purchase requests, and warehouse operations.

## Features

- User authentication and login system
- Role-based access for warehouse users
- Product inventory management
- Stock level tracking
- Supplier management
- Purchase/procurement request handling
- Admin/manager dashboard
- PostgreSQL database integration
- Deployed web application

## Tech Stack

- Python
- Flask
- PostgreSQL
- SQLAlchemy
- Flask-Login
- Flask-WTF
- HTML
- CSS
- Bootstrap
- Render

## User Roles

The system supports multiple warehouse-related roles, such as:

- Manager
- Clerk
- Procurement Officer
- Auditor

## Project Purpose

This project was built to solve a real warehouse problem: keeping inventory organized, tracking stock movement, and supporting different user responsibilities inside a warehouse system.

## Setup

```bash
git clone <your-repo-url>
cd stockr
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
