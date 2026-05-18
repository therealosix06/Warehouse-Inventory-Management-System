# WIMS — Warehouse Inventory Management System

WIMS is a Flask-based warehouse inventory management system designed to help organizations manage inventory, stock levels, suppliers, procurement workflows, and warehouse operations efficiently.

The system supports multiple warehouse roles and provides database-backed inventory management using PostgreSQL.

---

# Features

- User authentication and login system
- Role-based access control
- Product inventory management
- Stock quantity tracking
- Supplier management
- Procurement request handling
- Warehouse activity organization
- PostgreSQL database integration
- Responsive UI with Bootstrap
- Deployed production-ready configuration

---

# User Roles

WIMS supports multiple warehouse-related user roles, including:

- Manager
- Clerk
- Procurement Officer
- Auditor

Different users have access to different warehouse operations based on their role.

---

# Tech Stack

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

---

# Project Structure

```txt
WIMS/
├── app/
├── templates/
├── static/
├── models/
├── forms/
├── routes/
├── requirements.txt
└── run.py
```

---

# Setup Instructions

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd WIMS
```

---

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

### Windows

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root or configure these variables in your deployment platform:

```env
DATABASE_URL=your_postgresql_database_url
SECRET_KEY=your_secret_key
```

---

## 5. Initialize the Database

This project uses the Flask application factory pattern and initializes the database using `db.create_all()`.

Example:

```python
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
```

Depending on your project structure, this may already be handled automatically during setup.

---

## 6. Seed Demo Data

Visit:

```txt
/setup-demo
```

to create:
- demo users
- warehouse roles
- sample inventory data

---

## 7. Run the Application

```bash
python run.py
```

or depending on your project structure:

```bash
python app.py
```

---

## 8. Open in Browser

```txt
http://127.0.0.1:5000/
```

---

# Deployment

The application was deployed using:

- Render
- PostgreSQL production database
- Environment variable configuration

---

# Current Functionality

WIMS currently supports:

- Authentication system
- Inventory management
- Database-backed stock tracking
- Warehouse role management
- Supplier/procurement workflows
- Production deployment setup

---

# Future Improvements

- Inventory analytics dashboard
- Low-stock alerts
- Export reports to CSV/PDF
- REST API integration
- Barcode/QR scanning support
- Improved warehouse activity logs
- Advanced permissions system
- Audit trail tracking

---

# Project Goal

WIMS was built to solve real warehouse inventory challenges by providing a centralized system for managing products, users, procurement activities, and stock operations efficiently.
