from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"balance": 0, "stock_level": 0, "history": [], "items": []}
    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def add_to_history(data, description):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['history'].append({"date": timestamp, "description": description})
    save_data(data)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', balance=data['balance'], stock_level=data['stock_level'], items=data['items'])

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    data = load_data()
    if request.method == 'POST':
        try:
            operation = request.form['operation-type']
            value = float(request.form['value'])
            if operation == 'add':
                data['balance'] += value
                add_to_history(data, f"Added {value} to balance. New balance: {data['balance']}")
                save_data(data)
                return jsonify({"success": True, "message": "Your funds have been allocated successfully"})
            elif operation == 'subtract':
                if value > data['balance']:
                    return jsonify({"success": False, "message": "Insufficient balance"}), 400
                data['balance'] -= value
                add_to_history(data, f"Subtracted {value} from balance. New balance: {data['balance']}")
                save_data(data)
                return jsonify({"success": True, "message": "Your funds have been allocated successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    return render_template('balance.html', balance=data['balance'])

@app.route('/purchase', methods=['POST', 'GET'])
def handle_purchase():
    data = load_data()
    if request.method == 'POST':
        try:
            product_name = request.form['product-name']
            unit_price = float(request.form['unit-price'])
            number_of_pieces = int(request.form['number-of-pieces'])
            total_cost = unit_price * number_of_pieces

            if total_cost > data['balance']:
                return jsonify({"success": False, "message": "Insufficient balance for purchase"}), 400

            data['balance'] -= total_cost
            data['stock_level'] += number_of_pieces
            data['items'].append({"name": product_name, "unit_price": unit_price, "quantity": number_of_pieces})
            add_to_history(data, f"Purchased {number_of_pieces} of {product_name} for ${total_cost}")
            save_data(data)
            return jsonify({"success": True, "message": "Your purchase has been completed successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    return render_template('purchase.html', balance=data['balance'])

@app.route('/sale', methods=['POST', 'GET'])
def handle_sale():
    data = load_data()
    if request.method == 'POST':
        try:
            product_name = request.form['product-name']
            unit_price = float(request.form['unit-price'])
            number_of_pieces = int(request.form['number-of-pieces'])
            total_revenue = unit_price * number_of_pieces

            item_in_stock = next((item for item in data['items'] if item['name'] == product_name), None)
            if not item_in_stock or item_in_stock['quantity'] < number_of_pieces:
                return jsonify({"success": False, "message": "Insufficient stock for sale"}), 400

            data['balance'] += total_revenue
            data['stock_level'] -= number_of_pieces
            add_to_history(data, f"Sold {number_of_pieces} of {product_name} for ${total_revenue}")

            # Update existing item or remove if quantity is zero
            item_in_stock['quantity'] -= number_of_pieces
            if item_in_stock['quantity'] <= 0:
                data['items'].remove(item_in_stock)

            save_data(data)
            return jsonify({"success": True, "message": "Sale completed successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    return render_template('sale.html', balance=data['balance'], items=data['items'])

@app.route('/history/<line_from>/<line_to>/', methods=['GET'])
@app.route('/history/', defaults={'line_from': None, 'line_to': None}, methods=['GET'])
def history(line_from, line_to):
    data = load_data()
    history = data['history']
    
    if line_from and line_to:
        history = [entry for entry in history if line_from <= entry['date'] <= line_to]
    
    return render_template('history.html', balance=data['balance'], history=history)

if __name__ == "__main__":
    app.run(debug=True, port=5500)
