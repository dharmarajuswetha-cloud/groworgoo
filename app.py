from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "grow_orgo_secret_key"
DB_NAME = "database.db"

UPLOAD_FOLDER = 'static/uploads/reviews'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        price TEXT,
        image TEXT,
        category TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        username TEXT,
        rating INTEGER,
        comment TEXT,
        image_path TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        product_name TEXT,
        product_image TEXT,
        product_price TEXT,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        status TEXT DEFAULT 'Order Placed',
        order_date TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # AUTO ADD PRODUCTS
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        c.executemany("""
            INSERT INTO products (name, description, price, image, category)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Stone-Ground Wheat", "Organic whole grain flour", "80",
             "https://t3.ftcdn.net/jpg/07/56/66/28/360_F_756662819_M4cJj07c4o4CWRpP07vH41nG3uhuz5jA.jpg", "grains"),

            ("Fresh Mushrooms", "Premium mushrooms", "200",
             "https://static.vecteezy.com/system/resources/thumbnails/031/994/844/small_2x/mushrooms-in-a-wooden-plate-on-a-napkin-photo.jpg", "fresh harvest"),

            ("Organic A2 Milk", "Pure milk", "95",
             "https://static.toiimg.com/thumb/msid-108571967,width-1280,height-720,resizemode-4/108571967.jpg", "dairy")
        ])

    conn.commit()
    conn.close()


init_db()

# ================= ROUTES =================

@app.route('/')
def home():
    return render_template('frontpage.html', user=session.get('user', ''))


@app.route('/products')
def products():
    conn = get_db()

    products_data = conn.execute("SELECT * FROM products").fetchall()
    reviews_data = conn.execute("SELECT * FROM reviews").fetchall()

    avg_ratings = {}
    for p in products_data:
        res = conn.execute(
            "SELECT AVG(rating), COUNT(id) FROM reviews WHERE product_id=?",
            (p['id'],)
        ).fetchone()

        score = round(res[0], 1) if res[0] else 5.0

        avg_ratings[p['id']] = {
            'score': score,
            'count': res[1],
            'int_score': int(round(score))
        }

    conn.close()

    return render_template(
        'products.html',
        products=products_data,
        avg_ratings=avg_ratings,
        user=session.get('user', ''),
        reviews=[dict(r) for r in reviews_data]
    )
@app.route('/order_page/<int:product_id>')
def order_page(product_id):
    conn = get_db()
    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()
    conn.close()

    return render_template('order.html', product=product)
@app.route('/place_order/<int:product_id>', methods=['POST'])
def place_order(product_id):
    if 'email' not in session:
        return redirect('/')

    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    conn.execute("""
        INSERT INTO orders 
        (user_email, product_name, product_image, product_price, customer_name, phone, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session['email'],
        product['name'],
        product['image'],
        product['price'],
        name,
        phone,
        address
    ))

    conn.commit()
    conn.close()

    return redirect('/orders')

# ✅ ORDERS ROUTE (FIXED)
@app.route('/orders')
def orders():
    if 'email' not in session:
        return redirect('/')

    conn = get_db()
    orders_data = conn.execute(
        "SELECT * FROM orders WHERE user_email=?",
        (session['email'],)
    ).fetchall()
    conn.close()

    return render_template(
        'orders.html',
        orders=orders_data,
        user=session.get('user', '')
    )
@app.route('/order_details/<int:order_id>')
def order_details(order_id):
    if 'email' not in session:
        return redirect('/')

    conn = get_db()
    order = conn.execute(
        "SELECT * FROM orders WHERE id=? AND user_email=?",
        (order_id, session['email'])
    ).fetchone()
    conn.close()

    return render_template('order_details.html', order=order)


# ✅ TEST ORDER (VERY IMPORTANT FOR YOU)
@app.route('/test_order')
def test_order():
    if 'email' not in session:
        return "Login first"

    conn = get_db()
    conn.execute("""
        INSERT INTO orders 
        (user_email, product_name, product_image, product_price, customer_name, phone, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session['email'],
        "Test Product",
        "https://via.placeholder.com/150",
        "100",
        "Test User",
        "9999999999",
        "Test Address"
    ))
    conn.commit()
    conn.close()

    return "Order added successfully! Now go to /orders"


# ✅ DEBUG ROUTE
@app.route('/check')
def check():
    return str(session)


@app.route('/submit_review', methods=['POST'])
def submit_review():
    product_id = request.form['product_id']
    rating = request.form['rating']
    comment = request.form['comment']
    username = session.get('user', 'Guest')

    image = request.files.get('review_image')
    image_path = ""

    if image and image.filename:
        filename = secure_filename(image.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(path)
        image_path = "/" + path

    conn = get_db()
    conn.execute(
        "INSERT INTO reviews (product_id, username, rating, comment, image_path) VALUES (?, ?, ?, ?, ?)",
        (product_id, username, rating, comment, image_path)
    )
    conn.commit()
    conn.close()

    return redirect('/products')


@app.route('/login', methods=['POST'])
def login():
    i = request.form['identifier']
    p = request.form['password']

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE (email=? OR username=?) AND password=?",
        (i, i, p)
    ).fetchone()
    conn.close()

    if user:
        session.clear()   # 🔥 important
        session['user'] = user['username']
        session['email'] = user['email']
        return redirect('/')

    return "Invalid login"


@app.route('/signup', methods=['POST'])
def signup():
    u = request.form['username']
    e = request.form['email']
    p = request.form['password']

    conn = get_db()

    # ✅ CHECK IF EMAIL ALREADY EXISTS
    existing_user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (e,)
    ).fetchone()

    if existing_user:
        conn.close()
        return "Email already exists. Please login instead."

    # ✅ INSERT NEW USER
    conn.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (u, e, p)
    )
    conn.commit()
    conn.close()

    # ✅ SET SESSION
    session.clear()
    session['user'] = u
    session['email'] = e

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================

if __name__ == '__main__':
    app.run(debug=True)