from decimal import Decimal
from functools import wraps
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func,text

from . import db
from .models import (
    Category,
    Item,
    ItemSupplier,
    Location,
    PurchaseOrder,
    PurchaseOrderItem,
    StockTransaction,
    Supplier,
    User,
    Warehouse,
)


ROLE_ACCESS = {
    'Manager': {'Manager'},
    'Clerk': {'Manager', 'Clerk'},
    'Procurement': {'Manager', 'Procurement'},
    'Auditor': {'Manager', 'Auditor'},
}


def role_required(required_role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))

            allowed_roles = ROLE_ACCESS.get(required_role, set())

            if current_user.role not in allowed_roles:
                flash('You do not have permission for that action.', 'danger')
                return redirect(url_for('dashboard'))

            return view(*args, **kwargs)
        return wrapped
    return decorator

def set_db_user_context():
    if current_user.is_authenticated:
        db.session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(current_user.user_id)}
        )

def register_routes(app):
    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('home.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            user = User.query.filter(func.lower(User.email) == email).first()

            if user and user.check_password(password):
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))

            flash('Invalid email or password.', 'danger')

        return render_template('login.html')
    @app.route('/audit-logs')
    @role_required('Auditor')
    def audit_logs():
        logs = db.session.execute(text("""
            SELECT
                al.log_id,
                al.table_name,
                al.operation,
                al.record_id,
                al.action_time,
                u.full_name AS acted_by,
                al.old_data,
                al.new_data
            FROM audit_log al
            LEFT JOIN users u ON al.acted_by_user_id = u.user_id
            ORDER BY al.action_time DESC
        """)).fetchall()

        return render_template('audit_logs.html', logs=logs)
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        total_items = Item.query.count()
        total_suppliers = Supplier.query.count()
        total_purchase_orders = PurchaseOrder.query.count()
        total_transactions = StockTransaction.query.count()

        low_stock_items = Item.query.filter(
            Item.quantity_in_stock <= Item.reorder_level
        ).all()

        stock_value = db.session.query(
            func.coalesce(func.sum(Item.quantity_in_stock * Item.unit_price), 0)
        ).scalar()

        recent_transactions = StockTransaction.query.order_by(
            StockTransaction.transaction_date.desc()
        ).limit(6).all()

        return render_template(
            'dashboard.html',
            total_items=total_items,
            total_suppliers=total_suppliers,
            total_purchase_orders=total_purchase_orders,
            total_transactions=total_transactions,
            low_stock_items=low_stock_items,
            stock_value=stock_value,
            recent_transactions=recent_transactions,
        )

    @app.route('/items', methods=['GET', 'POST'])
    @role_required('Clerk')
    def items():
        if request.method == 'POST':
            item = Item(
                item_name=request.form['item_name'],
                description=request.form.get('description'),
                quantity_in_stock=int(request.form['quantity_in_stock']),
                reorder_level=int(request.form['reorder_level']),
                unit_price=Decimal(request.form['unit_price']),
                category_id=int(request.form['category_id']),
                location_id=int(request.form['location_id']),
            )
            set_db_user_context()
            db.session.add(item)
            db.session.commit()
            flash('Item added successfully.', 'success')
            return redirect(url_for('items'))

        items_list = Item.query.order_by(Item.item_name).all()
        categories = Category.query.order_by(Category.category_name).all()
        locations = Location.query.order_by(Location.aisle, Location.shelf, Location.bin).all()

        return render_template(
            'items.html',
            items=items_list,
            categories=categories,
            locations=locations
        )
    @app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
    @role_required('Clerk')
    def edit_item(item_id):
        item = Item.query.get_or_404(item_id)
        categories = Category.query.order_by(Category.category_name).all()
        locations = Location.query.order_by(Location.aisle, Location.shelf, Location.bin).all()

        if request.method == 'POST':
            item.item_name = request.form['item_name']
            item.description = request.form.get('description')
            item.quantity_in_stock = int(request.form['quantity_in_stock'])
            item.reorder_level = int(request.form['reorder_level'])
            item.unit_price = Decimal(request.form['unit_price'])
            item.category_id = int(request.form['category_id'])
            item.location_id = int(request.form['location_id'])
            
            set_db_user_context()
            db.session.commit()
            flash('Item updated successfully.', 'success')
            return redirect(url_for('items'))

        return render_template(
            'edit_item.html',
            item=item,
            categories=categories,
            locations=locations
        )

    @app.route('/items/<int:item_id>/delete', methods=['POST'])
    @role_required('Clerk')
    def delete_item(item_id):
        item = Item.query.get_or_404(item_id)

        if item.transactions:
            flash('Cannot delete an item that already has stock transactions.', 'danger')
            return redirect(url_for('items'))

        if item.purchase_order_items:
            flash('Cannot delete an item that is already linked to purchase orders.', 'danger')
            return redirect(url_for('items'))
        
        set_db_user_context()
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully.', 'success')
        return redirect(url_for('items'))
    @app.route('/suppliers', methods=['GET', 'POST'])
    @role_required('Procurement')
    def suppliers():
        if request.method == 'POST':
            supplier = Supplier(
                supplier_name=request.form['supplier_name'],
                contact_person=request.form.get('contact_person'),
                phone=request.form.get('phone'),
                email=request.form.get('email'),
                address=request.form.get('address'),
            )
            set_db_user_context()
            db.session.add(supplier)
            db.session.commit()
            flash('Supplier created.', 'success')
            return redirect(url_for('suppliers'))

        suppliers_list = Supplier.query.order_by(Supplier.supplier_name).all()
        items_list = Item.query.order_by(Item.item_name).all()

        return render_template(
            'suppliers.html',
            suppliers=suppliers_list,
            items=items_list
        )

    @app.route('/item-suppliers/add', methods=['POST'])
    @role_required('Procurement')
    def add_item_supplier():
        record = ItemSupplier(
            item_id=int(request.form['item_id']),
            supplier_id=int(request.form['supplier_id']),
            supply_price=Decimal(request.form['supply_price'])
        )
        db.session.merge(record)
        db.session.commit()
        flash('Item-supplier relationship saved.', 'success')
        return redirect(url_for('suppliers'))
    
    @app.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
    @role_required('Procurement')
    def edit_supplier(supplier_id):
        supplier = Supplier.query.get_or_404(supplier_id)

        if request.method == 'POST':
            supplier.supplier_name = request.form['supplier_name']
            supplier.contact_person = request.form.get('contact_person')
            supplier.phone = request.form.get('phone')
            supplier.email = request.form.get('email')
            supplier.address = request.form.get('address')
            
            set_db_user_context()
            db.session.commit()
            flash('Supplier updated successfully.', 'success')
            return redirect(url_for('suppliers'))

        return render_template('edit_supplier.html', supplier=supplier)

    @app.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
    @role_required('Procurement')
    def delete_supplier(supplier_id):
        supplier = Supplier.query.get_or_404(supplier_id)

        if supplier.purchase_orders:
            flash('Cannot delete a supplier that is already linked to purchase orders.', 'danger')
            return redirect(url_for('suppliers'))

        if supplier.supplied_items:
            flash('Cannot delete a supplier that is already linked to items.', 'danger')
            return redirect(url_for('suppliers'))
        
        set_db_user_context()
        db.session.delete(supplier)
        db.session.commit()
        flash('Supplier deleted successfully.', 'success')
        return redirect(url_for('suppliers'))

    @app.route('/transactions', methods=['GET', 'POST'])
    @role_required('Clerk')
    def transactions():
        if request.method == 'POST':
            txn_type = request.form['transaction_type']
            quantity = int(request.form['quantity'])
            item = Item.query.get_or_404(int(request.form['item_id']))

            set_db_user_context()

            transaction = StockTransaction(
                transaction_type=txn_type,
                quantity=quantity,
                notes=request.form.get('notes'),
                item_id=item.item_id,
                user_id=current_user.user_id,
            )

            db.session.add(transaction)

            try:
                db.session.commit()
                flash('Transaction recorded and stock updated.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Could not record transaction: {str(e)}', 'danger')

            return redirect(url_for('transactions'))

        transactions_list = StockTransaction.query.order_by(
            StockTransaction.transaction_date.desc()
        ).all()
        items_list = Item.query.order_by(Item.item_name).all()

        return render_template(
            'transactions.html',
            transactions=transactions_list,
            items=items_list
        )

    @app.route('/purchase-orders', methods=['GET', 'POST'])
    @role_required('Procurement')
    def purchase_orders():
        suppliers = Supplier.query.order_by(Supplier.supplier_name).all()
        items_list = Item.query.order_by(Item.item_name).all()

        if request.method == 'POST':
            po = PurchaseOrder(
                expected_delivery=datetime.strptime(
                    request.form['expected_delivery'], '%Y-%m-%d'
                ).date() if request.form.get('expected_delivery') else None,
                status=request.form['status'],
                supplier_id=int(request.form['supplier_id']),
                user_id=current_user.user_id,
            )
            db.session.add(po)
            db.session.flush()

            item_ids = request.form.getlist('item_id')
            quantities = request.form.getlist('quantity_ordered')
            prices = request.form.getlist('unit_price')

            for item_id, qty, price in zip(item_ids, quantities, prices):
                if item_id and qty and price:
                    db.session.add(
                        PurchaseOrderItem(
                            po_id=po.po_id,
                            item_id=int(item_id),
                            quantity_ordered=int(qty),
                            unit_price=Decimal(price),
                        )
                    )

            db.session.commit()
            flash('Purchase order created.', 'success')
            return redirect(url_for('purchase_orders'))

        orders = PurchaseOrder.query.order_by(
            PurchaseOrder.order_date.desc(),
            PurchaseOrder.po_id.desc()
        ).all()

        return render_template(
            'purchase_orders.html',
            orders=orders,
            suppliers=suppliers,
            items=items_list
        )
    
    @app.route('/purchase-orders/<int:po_id>')
    @role_required('Procurement')
    def purchase_order_detail(po_id):
        order = PurchaseOrder.query.get_or_404(po_id)
        return render_template('purchase_order_detail.html', order=order)

    @app.route('/reports')
    @role_required('Auditor')
    def reports():
        low_stock = (
            db.session.query(Item, Supplier)
            .join(ItemSupplier, Item.item_id == ItemSupplier.item_id)
            .join(Supplier, Supplier.supplier_id == ItemSupplier.supplier_id)
            .filter(Item.quantity_in_stock <= Item.reorder_level)
            .order_by((Item.reorder_level - Item.quantity_in_stock).desc())
            .all()
        )

        category_totals = (
            db.session.query(
                Category.category_name,
                func.count(Item.item_id),
                func.sum(Item.quantity_in_stock),
                func.sum(Item.quantity_in_stock * Item.unit_price),
            )
            .join(Item, Item.category_id == Category.category_id)
            .group_by(Category.category_name)
            .order_by(func.sum(Item.quantity_in_stock * Item.unit_price).desc())
            .all()
        )

        po_history = PurchaseOrder.query.order_by(
            PurchaseOrder.order_date.desc()
        ).all()

        return render_template(
            'reports.html',
            low_stock=low_stock,
            category_totals=category_totals,
            po_history=po_history
        )

    @app.route('/reference')
    @login_required
    def reference():
        return render_template('reference.html')
    
    
    @app.route('/users', methods=['GET', 'POST'])
    @role_required('Manager')
    def users():
        if request.method == 'POST':
            full_name = request.form['full_name'].strip()
            email = request.form['email'].strip().lower()
            role = request.form['role']
            password = request.form['password']

            existing_user = User.query.filter(func.lower(User.email) == email).first()
            if existing_user:
                flash('A user with that email already exists.', 'danger')
                return redirect(url_for('users'))

            new_user = User(full_name=full_name, email=email, role=role)
            new_user.set_password(password)
            
            set_db_user_context()
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully.', 'success')
            return redirect(url_for('users'))

        users_list = User.query.order_by(User.full_name).all()
        return render_template('users.html', users=users_list)

    @app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @role_required('Manager')
    def edit_user(user_id):
        user = User.query.get_or_404(user_id)

        if request.method == 'POST':
            full_name = request.form['full_name'].strip()
            email = request.form['email'].strip().lower()
            role = request.form['role']
            password = request.form.get('password', '').strip()

            existing_user = User.query.filter(func.lower(User.email) == email, User.user_id != user.user_id).first()
            if existing_user:
                flash('Another user with that email already exists.', 'danger')
                return redirect(url_for('edit_user', user_id=user.user_id))

            user.full_name = full_name
            user.email = email
            user.role = role

            if password:
                user.set_password(password)
            
            set_db_user_context()
            db.session.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('users'))

        return render_template('edit_user.html', user=user)

    @app.route('/users/<int:user_id>/delete', methods=['POST'])
    @role_required('Manager')
    def delete_user(user_id):
        user = User.query.get_or_404(user_id)

        if user.user_id == current_user.user_id:
            flash('You cannot delete your own account while logged in.', 'danger')
            return redirect(url_for('users'))

        if user.transactions:
            flash('Cannot delete a user who is linked to stock transactions.', 'danger')
            return redirect(url_for('users'))

        if user.purchase_orders:
            flash('Cannot delete a user who is linked to purchase orders.', 'danger')
            return redirect(url_for('users'))
        
        set_db_user_context()
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
        return redirect(url_for('users'))

    @app.route('/setup-demo')
    def setup_demo():
        if User.query.count() > 0:
            flash('Initial system data already exists.', 'warning')
            return redirect(url_for('login'))

        manager = User(full_name='Joseph Amankwah', email='josephamanks06@gmail.com', role='Manager')
        manager.set_password('password123')

        clerk = User(full_name='Sekyere Kofi Bempong', email='sekyere5261@gmail.com', role='Clerk')
        clerk.set_password('password123')

        procurement = User(full_name='Kofi Boateng Oware-Tano', email='kofiowaretano@gmail.com', role='Procurement')
        procurement.set_password('password123')

        auditor = User(full_name='Obeng Ruth', email='ruthobeng888@gmail.com', role='Auditor')
        auditor.set_password('password123')

        clerk2 = User(full_name='Daniel Dwomoh Frimpong', email='ddfrimpong@st.ug.edu.gh', role='Clerk')
        clerk2.set_password('password123')

        procurement2 = User(full_name="Mas'ud Nasir", email='masawudumohammednasiru@gmail.com', role='Procurement')
        procurement2.set_password('password123')

        clerk3 = User(full_name='Gilbert Akwasi Yeboah', email='gilbertyeboah5002@gmail.com', role='Clerk')
        clerk3.set_password('password123')

        auditor2 = User(full_name='Adu Bansu Mini', email='adumini42@gmail.com', role='Auditor')
        auditor2.set_password('password123')

        clerk4 = User(full_name='Quaicoo Emile', email='dmgchino99@gmail.com', role='Clerk')
        clerk4.set_password('password123')

        categories = [
            Category(category_name='Electronics', description='Electronic devices, accessories, and components'),
            Category(category_name='Office Supplies', description='Administrative and office-use materials'),
            Category(category_name='Industrial Tools', description='Maintenance and operational tools'),
            Category(category_name='Packaging', description='Packaging and dispatch materials'),
            Category(category_name='Cleaning Supplies', description='Cleaning and sanitation materials'),
        ]

        warehouse1 = Warehouse(
            warehouse_name='Central Warehouse',
            address='North Industrial Area, Accra',
            manager_name='System Manager'
        )

        warehouse2 = Warehouse(
            warehouse_name='Annex Storage Facility',
            address='Spintex Road, Accra',
            manager_name='Operations Supervisor'
        )

        db.session.add_all([
        manager, clerk, procurement, auditor,
        clerk2, procurement2, clerk3, auditor2, clerk4,
        *categories, warehouse1, warehouse2
    ])
        db.session.flush()

        locations = [
            Location(aisle='A', shelf='1', bin='01', warehouse_id=warehouse1.warehouse_id),
            Location(aisle='A', shelf='1', bin='02', warehouse_id=warehouse1.warehouse_id),
            Location(aisle='A', shelf='2', bin='01', warehouse_id=warehouse1.warehouse_id),
            Location(aisle='B', shelf='1', bin='01', warehouse_id=warehouse1.warehouse_id),
            Location(aisle='B', shelf='2', bin='03', warehouse_id=warehouse2.warehouse_id),
            Location(aisle='C', shelf='1', bin='01', warehouse_id=warehouse2.warehouse_id),
            Location(aisle='C', shelf='2', bin='02', warehouse_id=warehouse2.warehouse_id),
        ]
        db.session.add_all(locations)
        db.session.flush()

        suppliers_data = [
            Supplier(
                supplier_name='Prime Tech Supplies',
                contact_person='Daniel Mensah',
                phone='0241112233',
                email='sales@primetechsupplies.com',
                address='Accra, Ghana'
            ),
            Supplier(
                supplier_name='Metro Office Essentials',
                contact_person='Akosua Boadu',
                phone='0554445566',
                email='orders@metroofficeessentials.com',
                address='Kumasi, Ghana'
            ),
            Supplier(
                supplier_name='Industrial Resource Partners',
                contact_person='Michael Owusu',
                phone='0207778899',
                email='supply@irpghana.com',
                address='Tema, Ghana'
            ),
            Supplier(
                supplier_name='CleanCare Distributors',
                contact_person='Linda Asare',
                phone='0275551122',
                email='contact@cleancaregh.com',
                address='Takoradi, Ghana'
            ),
        ]
        db.session.add_all(suppliers_data)
        db.session.flush()

        items_data = [
            Item(
                item_name='USB-C Cable 2m',
                description='High-speed USB-C charging and data cable',
                quantity_in_stock=150,
                reorder_level=25,
                unit_price=Decimal('12.50'),
                category_id=categories[0].category_id,
                location_id=locations[0].location_id
            ),
            Item(
                item_name='AA Batteries Pack',
                description='Pack of 10 AA alkaline batteries',
                quantity_in_stock=200,
                reorder_level=40,
                unit_price=Decimal('6.00'),
                category_id=categories[0].category_id,
                location_id=locations[1].location_id
            ),
            Item(
                item_name='A4 Paper Ream',
                description='500-sheet ream of A4 office paper',
                quantity_in_stock=300,
                reorder_level=60,
                unit_price=Decimal('8.00'),
                category_id=categories[1].category_id,
                location_id=locations[2].location_id
            ),
            Item(
                item_name='Ballpoint Pens Box',
                description='Box of 50 blue ballpoint pens',
                quantity_in_stock=120,
                reorder_level=30,
                unit_price=Decimal('4.50'),
                category_id=categories[1].category_id,
                location_id=locations[3].location_id
            ),
            Item(
                item_name='Cordless Drill',
                description='18V cordless drill with rechargeable battery',
                quantity_in_stock=35,
                reorder_level=8,
                unit_price=Decimal('120.00'),
                category_id=categories[2].category_id,
                location_id=locations[4].location_id
            ),
            Item(
                item_name='Adjustable Spanner',
                description='Heavy-duty adjustable spanner for maintenance tasks',
                quantity_in_stock=50,
                reorder_level=10,
                unit_price=Decimal('22.00'),
                category_id=categories[2].category_id,
                location_id=locations[5].location_id
            ),
            Item(
                item_name='Bubble Wrap Roll',
                description='50m bubble wrap roll for protective packaging',
                quantity_in_stock=80,
                reorder_level=20,
                unit_price=Decimal('25.00'),
                category_id=categories[3].category_id,
                location_id=locations[6].location_id
            ),
            Item(
                item_name='Cleaning Detergent 5L',
                description='Industrial liquid detergent for facility cleaning',
                quantity_in_stock=45,
                reorder_level=12,
                unit_price=Decimal('18.00'),
                category_id=categories[4].category_id,
                location_id=locations[1].location_id
            ),
        ]
        db.session.add_all(items_data)
        db.session.flush()

        item_supplier_pairs = [
            (items_data[0], suppliers_data[0], '9.00'),
            (items_data[1], suppliers_data[0], '4.00'),
            (items_data[2], suppliers_data[1], '5.50'),
            (items_data[3], suppliers_data[1], '3.00'),
            (items_data[4], suppliers_data[2], '90.00'),
            (items_data[5], suppliers_data[2], '15.00'),
            (items_data[6], suppliers_data[2], '18.00'),
            (items_data[7], suppliers_data[3], '13.50'),
            (items_data[4], suppliers_data[0], '95.00'),
        ]

        for item_obj, supplier_obj, price in item_supplier_pairs:
            db.session.add(
                ItemSupplier(
                    item_id=item_obj.item_id,
                    supplier_id=supplier_obj.supplier_id,
                    supply_price=Decimal(price)
                )
            )

        po1 = PurchaseOrder(
            status='Delivered',
            supplier_id=suppliers_data[0].supplier_id,
            user_id=procurement.user_id,
            expected_delivery=datetime.strptime('2026-03-07', '%Y-%m-%d').date()
        )

        po2 = PurchaseOrder(
            status='Pending',
            supplier_id=suppliers_data[1].supplier_id,
            user_id=procurement.user_id,
            expected_delivery=datetime.strptime('2026-03-14', '%Y-%m-%d').date()
        )

        po3 = PurchaseOrder(
            status='Pending',
            supplier_id=suppliers_data[2].supplier_id,
            user_id=procurement.user_id,
            expected_delivery=datetime.strptime('2026-03-18', '%Y-%m-%d').date()
        )

        po4 = PurchaseOrder(
            status='Pending',
            supplier_id=suppliers_data[3].supplier_id,
            user_id=procurement.user_id,
            expected_delivery=datetime.strptime('2026-03-20', '%Y-%m-%d').date()
        )

        db.session.add_all([po1, po2, po3, po4])
        db.session.flush()

        po_items = [
            PurchaseOrderItem(quantity_ordered=100, unit_price=Decimal('9.00'), po_id=po1.po_id, item_id=items_data[0].item_id),
            PurchaseOrderItem(quantity_ordered=50, unit_price=Decimal('4.00'), po_id=po1.po_id, item_id=items_data[1].item_id),
            PurchaseOrderItem(quantity_ordered=200, unit_price=Decimal('5.50'), po_id=po2.po_id, item_id=items_data[2].item_id),
            PurchaseOrderItem(quantity_ordered=100, unit_price=Decimal('3.00'), po_id=po2.po_id, item_id=items_data[3].item_id),
            PurchaseOrderItem(quantity_ordered=20, unit_price=Decimal('90.00'), po_id=po3.po_id, item_id=items_data[4].item_id),
            PurchaseOrderItem(quantity_ordered=40, unit_price=Decimal('15.00'), po_id=po3.po_id, item_id=items_data[5].item_id),
            PurchaseOrderItem(quantity_ordered=25, unit_price=Decimal('13.50'), po_id=po4.po_id, item_id=items_data[7].item_id),
            PurchaseOrderItem(quantity_ordered=30, unit_price=Decimal('18.00'), po_id=po3.po_id, item_id=items_data[6].item_id),
        ]
        db.session.add_all(po_items)

        demo_txns = [
            StockTransaction(
                transaction_type='IN',
                quantity=100,
                notes='Received approved electronics shipment from Prime Tech Supplies',
                item_id=items_data[0].item_id,
                user_id=clerk.user_id
            ),
            StockTransaction(
                transaction_type='IN',
                quantity=50,
                notes='Received battery stock from Prime Tech Supplies',
                item_id=items_data[1].item_id,
                user_id=clerk.user_id
            ),
            StockTransaction(
                transaction_type='OUT',
                quantity=30,
                notes='Issued USB-C cables for internal operational use',
                item_id=items_data[0].item_id,
                user_id=clerk.user_id
            ),
            StockTransaction(
                transaction_type='OUT',
                quantity=15,
                notes='Released office paper for administrative use',
                item_id=items_data[2].item_id,
                user_id=clerk.user_id
            ),
            StockTransaction(
                transaction_type='IN',
                quantity=20,
                notes='Emergency replenishment of cordless drills',
                item_id=items_data[4].item_id,
                user_id=clerk.user_id
            ),
            StockTransaction(
                transaction_type='OUT',
                quantity=8,
                notes='Issued cleaning detergent for facility maintenance',
                item_id=items_data[7].item_id,
                user_id=clerk.user_id
            ),
        ]
        db.session.add_all(demo_txns)
        db.session.commit()

        flash('Initial warehouse data created successfully. Use the seeded staff credentials to log in.', 'success')
        return redirect(url_for('login'))