from app import create_app, db
from app.models import (
    User, Category, Warehouse, Location, Supplier,
    Item, ItemSupplier, StockTransaction,
    PurchaseOrder, PurchaseOrderItem
)

app = create_app()

with app.app_context():
    print("DATABASE URI:", app.config["SQLALCHEMY_DATABASE_URI"])
    db.create_all()
    print("Tables known to SQLAlchemy:")
    for table in db.metadata.tables:
        print("-", table)
    print("Tables created successfully.")