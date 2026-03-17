from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)

    items = db.relationship('Item', back_populates='category', lazy=True)


class Warehouse(db.Model):
    __tablename__ = 'warehouse'
    warehouse_id = db.Column(db.Integer, primary_key=True)
    warehouse_name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.Text)
    manager_name = db.Column(db.String(150))

    locations = db.relationship('Location', back_populates='warehouse', lazy=True)


class Location(db.Model):
    __tablename__ = 'location'
    location_id = db.Column(db.Integer, primary_key=True)
    aisle = db.Column(db.String(10), nullable=False)
    shelf = db.Column(db.String(10), nullable=False)
    bin = db.Column(db.String(10), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.warehouse_id', ondelete='RESTRICT'), nullable=False)

    warehouse = db.relationship('Warehouse', back_populates='locations')
    items = db.relationship('Item', back_populates='location', lazy=True)

    @property
    def code(self):
        return f"{self.aisle}-{self.shelf}-{self.bin}"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    transactions = db.relationship('StockTransaction', back_populates='user', lazy=True)
    purchase_orders = db.relationship('PurchaseOrder', back_populates='user', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Supplier(db.Model):
    __tablename__ = 'supplier'
    supplier_id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    address = db.Column(db.Text)

    purchase_orders = db.relationship('PurchaseOrder', back_populates='supplier', lazy=True)
    supplied_items = db.relationship('ItemSupplier', back_populates='supplier', cascade='all, delete-orphan', lazy=True)


class Item(db.Model):
    __tablename__ = 'item'
    item_id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id', ondelete='RESTRICT'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.location_id', ondelete='RESTRICT'), nullable=False)

    category = db.relationship('Category', back_populates='items')
    location = db.relationship('Location', back_populates='items')
    transactions = db.relationship('StockTransaction', back_populates='item', lazy=True)
    suppliers = db.relationship('ItemSupplier', back_populates='item', cascade='all, delete-orphan', lazy=True)
    purchase_order_items = db.relationship('PurchaseOrderItem', back_populates='item', lazy=True)


class ItemSupplier(db.Model):
    __tablename__ = 'item_supplier'
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id', ondelete='CASCADE'), primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id', ondelete='CASCADE'), primary_key=True)
    supply_price = db.Column(db.Numeric(10, 2), nullable=False)

    item = db.relationship('Item', back_populates='suppliers')
    supplier = db.relationship('Supplier', back_populates='supplied_items')


class StockTransaction(db.Model):
    __tablename__ = 'stock_transaction'
    transaction_id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(3), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id', ondelete='RESTRICT'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)

    item = db.relationship('Item', back_populates='transactions')
    user = db.relationship('User', back_populates='transactions')


class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_order'
    po_id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.Date, default=date.today, nullable=False)
    expected_delivery = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id', ondelete='RESTRICT'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)

    supplier = db.relationship('Supplier', back_populates='purchase_orders')
    user = db.relationship('User', back_populates='purchase_orders')
    items = db.relationship('PurchaseOrderItem', back_populates='purchase_order', cascade='all, delete-orphan', lazy=True)


class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_item'
    po_item_id = db.Column(db.Integer, primary_key=True)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    po_id = db.Column(db.Integer, db.ForeignKey('purchase_order.po_id', ondelete='CASCADE'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id', ondelete='RESTRICT'), nullable=False)

    purchase_order = db.relationship('PurchaseOrder', back_populates='items')
    item = db.relationship('Item', back_populates='purchase_order_items')
