from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = "secret"

# ================= DB CONNECTION =================


conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row   # ✅ ADD THIS LINE
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    category TEXT,
    image TEXT
)
''')

conn.commit()

# ================= HOME =================
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    return render_template("index.html", products=products)


# ================= REGISTER =================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if not re.fullmatch(r'\d{6}', password):
            return "Password must be exactly 6 digits"

        cursor.execute(
        "INSERT INTO users (name,email,password) VALUES (?,?,?)",
        (name,email,password)
        )
        conn.commit()

        return redirect('/login')

    return render_template("register.html")


# ================= LOGIN =================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
        )
        user = cursor.fetchone()

        if user:
            session['user'] = user['name']
            return redirect('/')
        else:
            return "Invalid Login"

    return render_template("login.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')


# ================= ADD TO CART =================
@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'user' not in session:
        return redirect('/login')

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append(id)
    session.modified = True

    return redirect('/cart')


# ================= CART =================
@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect('/login')

    if 'cart' not in session or len(session['cart']) == 0:
        return render_template("cart.html", cart=[])

    ids = session['cart']
    format_strings = ','.join(['%s'] * len(ids))

    cursor.execute(
        f"SELECT * FROM products WHERE id IN ({format_strings})",
        tuple(ids)
    )
    cart_items = cursor.fetchall()

    return render_template("cart.html", cart=cart_items)


# ================= REMOVE =================
@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item != id]
        session.modified = True

    return redirect('/cart')


# ================= BUY =================
@app.route('/buy/<int:id>')
def buy(id):
    cursor.execute("SELECT * FROM products WHERE id=%s", (id,))
    product = cursor.fetchone()

    return render_template("buy.html", product=product)


# ================= SEARCH =================
@app.route('/search')
def search():
    query = request.args.get('q')

    cursor.execute(
        "SELECT * FROM products WHERE name LIKE %s",
        ('%' + query + '%',)
    )
    products = cursor.fetchall()

    return render_template("category.html", products=products)


# ================= CATEGORY =================
@app.route('/category/<name>')
def category(name):
    cursor.execute("SELECT * FROM products WHERE category=%s", (name,))
    products = cursor.fetchall()

    return render_template("category.html", products=products)


# ================= RUN =================


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))