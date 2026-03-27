from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "admin_secret_key"
DB_NAME = "database.db"

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "grow12"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u, p = request.form['username'], request.form['password']
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/dashboard')
        return render_template('admin_login.html', error="Invalid Credentials")
    return render_template('admin_login.html')

@app.route('/dashboard')
def admin_dashboard():
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    reviews = conn.execute("SELECT * FROM reviews ORDER BY date DESC").fetchall()
    conn.close()
    return render_template('admin.html', products=products, orders=orders, reviews=reviews)

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    conn.execute("INSERT INTO products (name, description, price, category, image) VALUES (?,?,?,?,?)",
                 (request.form['name'], request.form['description'], request.form['price'], request.form['category'], request.form['image']))
    conn.commit(); conn.close()
    return redirect('/dashboard')

@app.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    # Updated to include Category editing
    conn.execute("UPDATE products SET name=?, price=?, category=?, image=? WHERE id=?",
                 (request.form['name'], request.form['price'], request.form['category'], request.form['image'], product_id))
    conn.commit(); conn.close()
    return redirect('/dashboard')

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit(); conn.close()
    return redirect('/dashboard')

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (request.form['status'], order_id))
    conn.commit(); conn.close()
    return redirect('/dashboard')

@app.route('/database')
def database_view():
    if 'admin' not in session: return redirect('/')
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    products = conn.execute("SELECT * FROM products").fetchall()
    orders = conn.execute("SELECT * FROM orders").fetchall()
    reviews = conn.execute("SELECT * FROM reviews").fetchall()
    conn.close()
    return render_template('database.html', users=users, products=products, orders=orders, reviews=reviews)

@app.route('/logout')
def admin_logout():
    session.clear(); return redirect('/')

if __name__ == '__main__':
    app.run(port=5001, debug=True)