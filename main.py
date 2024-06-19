from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the database schema
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float, nullable=False)

class TransactionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(50))
    unit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Float)
    operation = db.Column(db.String(10))
    date = db.Column(db.DateTime, default=db.func.current_timestamp())
    def to_dict(self):
        return {
            "id": self.id,
            "product_name": self.product_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "operation": self.operation,
            "date": self.date.isoformat(),
        }

# Initialize the database and tables
def init_db():
    with app.app_context():
        db.create_all()
        if Account.query.first() is None:
            initial_balance = Account(balance=10000.00)
            db.session.add(initial_balance)
            db.session.commit()

# Define routes for each HTML file
@app.route('/')
def index():
    products = Product.query.all()
    account = Account.query.first()
    return render_template('index.html', products=products, account_balance=account.balance)

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    account = Account.query.first()
    if request.method == 'POST':
        try:
            operation_type = request.form['operation-type']
            value = float(request.form['value'])

            if operation_type == 'add':
                account.balance += value
            elif operation_type == 'subtract':
                if account.balance >= value:
                    account.balance -= value
                else:
                    return jsonify({'success': False, 'message': 'Insufficient funds'}), 400

            transaction = TransactionHistory(
                product_name="Balance Change",
                unit_price=0,
                quantity=0,
                total_price=value,
                operation=operation_type
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Balance updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f"An error occurred: {e}"}), 500
    return render_template('balance.html', account_balance=account.balance)

@app.route('/history')
def history():
    transactions = TransactionHistory.query.all()
    account = Account.query.first()
    transactions_json = jsonify([transaction.to_dict() for transaction in transactions])
    print(transactions_json)
    # transactions_json = [
    #     {
    #         'product_name': t.product_name,
    #         'unit_price': t.unit_price,
    #         'quantity': t.quantity,
    #         'total_price': t.total_price,
    #         'operation': t.operation,
    #         'date': t.date.strftime('%Y-%m-%d %H:%M:%S')
    #     } for t in transactions
    # ]
    return render_template('history.html', transactions_json=transactions_json, transactions=transactions, account_balance=account.balance)

@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    account = Account.query.first()
    if request.method == 'POST':
        try:
            product_name = request.form['product-name']
            unit_price = float(request.form['unit-price'])
            quantity = int(request.form['quantity'])
            total_price = unit_price * quantity

            if total_price > account.balance:
                return jsonify({'success': False, 'message': 'Insufficient funds'}), 400

            product = Product.query.filter_by(name=product_name).first()
            if product:
                product.quantity += quantity
            else:
                new_product = Product(name=product_name, unit_price=unit_price, quantity=quantity)
                db.session.add(new_product)
            
            account.balance -= total_price

            transaction = TransactionHistory(
                product_name=product_name,
                unit_price=unit_price,
                quantity=quantity,
                total_price=total_price,
                operation='purchase'
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Purchase successful'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f"An error occurred: {e}"}), 500
    return render_template('purchase.html', account_balance=account.balance)

@app.route('/sale', methods=['GET', 'POST'])
def sale():
    account = Account.query.first()
    if request.method == 'POST':
        try:
            product_name = request.form['product-name']
            unit_price = float(request.form['unit-price'])
            quantity = int(request.form['quantity'])

            product = Product.query.filter_by(name=product_name).first()
            if not product or product.quantity < quantity:
                return jsonify({'success': False, 'message': 'Insufficient stock'}), 400

            total_price = unit_price * quantity
            product.quantity -= quantity
            if product.quantity == 0:
                db.session.delete(product)
            account.balance += total_price

            transaction = TransactionHistory(
                product_name=product_name,
                unit_price=unit_price,
                quantity=quantity,
                total_price=total_price,
                operation='sale'
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Sale successful'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f"An error occurred: {e}"}), 500
    products = Product.query.all()
    return render_template('sale.html',products = products, account_balance=account.balance)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5500)
