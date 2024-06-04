from flask import Flask, render_template

app = Flask(__name__)



# Define routes for each HTML file
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/balance')
def balance():
    return render_template('balance.html')


@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

@app.route('/sale')
def sale():
    return render_template('sale.html')



app.run(debug=True, port=5500)
