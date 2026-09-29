import os
import re
import secrets
import hashlib

from flask import Flask, render_template, session, redirect, url_for, request, Response
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, initialize_database


app = Flask(__name__)


# =========================================================
# SECURITY SETTINGS
# =========================================================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ecolife-development-secret-change-before-deployment"
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)


initialize_database()


# =========================================================
# DATABASE PRODUCTS
# =========================================================

def get_store_products():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    store_products = {}

    for row in rows:

        image_name = row["image"] or ""

        if image_name == "bottle.jpg":
            product_id = "bottle"

        elif image_name == "bag.jpg":
            product_id = "bag"

        elif image_name == "bamboo.jpg":
            product_id = "bamboo"

        elif image_name == "solar.jpg":
            product_id = "solar"

        else:

            product_id = re.sub(
                r"[^a-z0-9]+",
                "-",
                row["name"].lower()
            ).strip("-")

        store_products[product_id] = {
            "db_id": row["id"],
            "name": row["name"],
            "price": row["price"],
            "image": row["image"],
            "description": row["description"],
            "stock": row["stock"],
            "rating": row["rating"],
            "reviews": row["reviews"]
        }

    return store_products


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# GOOGLE SITEMAP
# =========================================================

@app.route("/sitemap.xml")
def sitemap():

    store_products = get_store_products()

    urls = [
        url_for("home", _external=True),
        url_for("products_page", _external=True),
        url_for("cart", _external=True),
        url_for("register", _external=True),
        url_for("login", _external=True)
    ]

    # Add public product detail pages
    for product_id in store_products:
        urls.append(
            url_for(
                "product_details",
                product_id=product_id,
                _external=True
            )
        )

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    )

    for page_url in urls:
        xml.append("    <url>")
        xml.append(f"        <loc>{page_url}</loc>")
        xml.append("    </url>")

    xml.append("</urlset>")

    return Response(
        "\n".join(xml),
        mimetype="application/xml"
    )


# =========================================================
# ROBOTS.TXT
# =========================================================

@app.route("/robots.txt")
def robots_txt():

    sitemap_url = url_for(
        "sitemap",
        _external=True
    )

    robots = f"""User-agent: *
Allow: /

Sitemap: {sitemap_url}
"""

    return Response(
        robots,
        mimetype="text/plain"
    )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products_page():

    store_products = get_store_products()

    return render_template(
        "products.html",
        products=store_products
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<product_id>")
def product_details(product_id):

    store_products = get_store_products()

    product = store_products.get(product_id)

    if product is None:
        return "Product not found", 404

    return render_template(
        "product_details.html",
        product=product,
        product_id=product_id
    )


# =========================================================
# ADD TO CART
# =========================================================

@app.route("/add-to-cart/<product_id>")
def add_to_cart(product_id):

    store_products = get_store_products()

    if product_id not in store_products:
        return "Product not found", 404

    product = store_products[product_id]

    if product["stock"] <= 0:
        return "This product is out of stock.", 400

    cart = session.get("cart", {})

    current_quantity = int(cart.get(product_id, 0))

    if current_quantity >= product["stock"]:
        return "Maximum available stock reached.", 400

    cart[product_id] = current_quantity + 1

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    store_products = get_store_products()

    cart = session.get("cart", {})

    cart_items = []

    total = 0

    cleaned_cart = {}

    for product_id, quantity in cart.items():

        product = store_products.get(product_id)

        if product is None:
            continue

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        if product["stock"] <= 0:
            continue

        if quantity > product["stock"]:
            quantity = product["stock"]

        item_total = product["price"] * quantity

        cart_items.append({
            "id": product_id,
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "quantity": quantity,
            "item_total": item_total
        })

        cleaned_cart[product_id] = quantity

        total += item_total

    session["cart"] = cleaned_cart

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


# =========================================================
# INCREASE QUANTITY
# =========================================================

@app.route("/increase/<product_id>")
def increase_quantity(product_id):

    store_products = get_store_products()

    cart = session.get("cart", {})

    product = store_products.get(product_id)

    if product and product_id in cart:

        try:
            quantity = int(cart[product_id])
        except (TypeError, ValueError):
            quantity = 0

        if quantity < product["stock"]:
            cart[product_id] = quantity + 1

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================================================
# DECREASE QUANTITY
# =========================================================

@app.route("/decrease/<product_id>")
def decrease_quantity(product_id):

    cart = session.get("cart", {})

    if product_id in cart:

        try:
            cart[product_id] = int(cart[product_id]) - 1
        except (TypeError, ValueError):
            cart[product_id] = 0

        if cart[product_id] <= 0:
            del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================================================
# REMOVE FROM CART
# =========================================================

@app.route("/remove/<product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", {})

    if product_id in cart:
        del cart[product_id]

    session["cart"] = cart

    return redirect(url_for("cart"))


# =========================================================
# CHECKOUT
# =========================================================

@app.route("/checkout")
def checkout():

    store_products = get_store_products()

    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    total = 0

    for product_id, quantity in cart.items():

        product = store_products.get(product_id)

        if product:

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue

            if quantity > product["stock"]:
                quantity = product["stock"]

            total += product["price"] * quantity

    return render_template(
        "checkout.html",
        total=total
    )


# =========================================================
# PLACE ORDER
# =========================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    state = request.form.get("state", "").strip()
    pincode = request.form.get("pincode", "").strip()

    # Get payment safely
    payment = request.form.get("payment", "")

    if payment is None:
        payment = ""

    payment = str(payment).strip()

    # =====================================================
    # DEBUG
    # =====================================================

    print("========================================")
    print("PAYMENT RECEIVED FROM CHECKOUT:", repr(payment))
    print("========================================")

    # =====================================================
    # REQUIRED FIELD VALIDATION
    # =====================================================

    if not all([
        name,
        email,
        phone,
        address,
        city,
        state,
        pincode,
        payment
    ]):

        return "Please fill all required fields.", 400

    # =====================================================
    # EMAIL VALIDATION
    # =====================================================

    if not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email
    ):

        return "Invalid email address.", 400

    # =====================================================
    # PHONE VALIDATION
    # =====================================================

    if not re.match(
        r"^[0-9]{10}$",
        phone
    ):

        return "Invalid phone number.", 400

    # =====================================================
    # PINCODE VALIDATION
    # =====================================================

    if not re.match(
        r"^[0-9]{6}$",
        pincode
    ):

        return "Invalid pincode.", 400

    # =====================================================
    # PAYMENT VALIDATION
    # =====================================================

    # Normalize payment value
    payment_lower = payment.lower()

    if payment_lower in [
        "cash on delivery",
        "cod",
        "cash-on-delivery",
        "cash_on_delivery"
    ]:

        payment = "Cash on Delivery"

    elif payment_lower == "upi":

        payment = "UPI"

    elif payment_lower == "card":

        payment = "Card"

    else:

        return (
            f"Invalid payment method received: {repr(payment)}",
            400
        )

    # =====================================================
    # GET PRODUCTS AND CART
    # =====================================================

    store_products = get_store_products()

    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    total = 0

    order_items = []

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # =================================================
        # CHECK STOCK AND CALCULATE TOTAL
        # =================================================

        for product_id, quantity in cart.items():

            product = store_products.get(product_id)

            if product is None:
                continue

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue

            if quantity <= 0:
                continue

            if quantity > product["stock"]:

                connection.rollback()
                connection.close()

                return (
                    f"Not enough stock available for "
                    f"{product['name']}.",
                    400
                )

            item_total = product["price"] * quantity

            total += item_total

            order_items.append({
                "name": product["name"],
                "price": product["price"],
                "quantity": quantity,
                "item_total": item_total,
                "db_id": product["db_id"]
            })

        # =================================================
        # EMPTY CART CHECK
        # =================================================

        if not order_items:

            connection.close()

            return redirect(url_for("cart"))

        # =================================================
        # CREATE ORDER ID
        # =================================================

        order_id = "ECO" + secrets.token_hex(4).upper()

        # =================================================
        # SAVE ORDER
        # =================================================

        cursor.execute("""
            INSERT INTO orders
            (
                order_id,
                customer_name,
                email,
                phone,
                address,
                city,
                state,
                pincode,
                payment,
                total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            name,
            email,
            phone,
            address,
            city,
            state,
            pincode,
            payment,
            total
        ))

        # =================================================
        # SAVE ORDER ITEMS + UPDATE STOCK
        # =================================================

        for item in order_items:

            cursor.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_name,
                    price,
                    quantity,
                    item_total
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                item["name"],
                item["price"],
                item["quantity"],
                item["item_total"]
            ))

            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                AND stock >= ?
            """, (
                item["quantity"],
                item["db_id"],
                item["quantity"]
            ))

        # =================================================
        # COMMIT
        # =================================================

        connection.commit()

    except Exception as error:

        print("ORDER ERROR:", error)

        connection.rollback()
        connection.close()

        return "Unable to place order. Please try again.", 500

    connection.close()

    # =====================================================
    # CLEAR CART
    # =====================================================

    session["cart"] = {}

    # =====================================================
    # ORDER SUCCESS
    # =====================================================

    return render_template(
        "order_success.html",
        order_id=order_id,
        total=total,
        payment=payment
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password:

        return render_template(
            "register.html",
            error="Please fill all required fields."
        )

    if not re.match(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        email
    ):

        return render_template(
            "register.html",
            error="Please enter a valid email address."
        )

    if len(password) < 8:

        return render_template(
            "register.html",
            error="Password must contain at least 8 characters."
        )

    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match."
        )

    password_hash = generate_password_hash(password)

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                password
            )
            VALUES (?, ?, ?)
        """, (
            name,
            email,
            password_hash
        ))

        connection.commit()

    except Exception:

        connection.close()

        return render_template(
            "register.html",
            error="This email is already registered."
        )

    connection.close()

    return redirect(url_for("login"))


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:

        return render_template(
            "login.html",
            error="Please enter email and password."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    if user is None:

        connection.close()

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    stored_password = user["password"]

    password_valid = False
    needs_password_upgrade = False

    try:

        password_valid = check_password_hash(
            stored_password,
            password
        )

    except Exception:

        password_valid = False

    if not password_valid:

        old_hash = hashlib.sha256(
            password.encode()
        ).hexdigest()

        if secrets.compare_digest(
            old_hash,
            stored_password
        ):

            password_valid = True
            needs_password_upgrade = True

    if not password_valid:

        connection.close()

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    if needs_password_upgrade:

        new_password_hash = generate_password_hash(
            password
        )

        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (
            new_password_hash,
            user["id"]
        ))

        connection.commit()

    connection.close()

    session.clear()

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["user_role"] = user["role"]

    return redirect(url_for("home"))


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/my-orders")
def my_orders():

    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_email = session.get("user_email")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            customer_name,
            email,
            payment,
            total,
            order_date
        FROM orders
        WHERE email = ?
        ORDER BY order_date DESC
    """, (user_email,))

    orders = cursor.fetchall()

    connection.close()

    return render_template(
        "my_orders.html",
        orders=orders
    )


# =========================================================
# ADMIN SECURITY
# =========================================================

def admin_required():

    if not session.get("user_id"):
        return False

    if session.get("user_role") != "admin":
        return False

    return True


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
    """)

    total_users = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM orders
    """)

    total_orders = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(total), 0) AS total
        FROM orders
    """)

    total_sales = cursor.fetchone()["total"]

    connection.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_orders=total_orders,
        total_sales=total_sales
    )


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.route("/admin/orders")
def admin_orders():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        ORDER BY order_date DESC
    """)

    orders = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_orders.html",
        orders=orders
    )


# =========================================================
# ADMIN USERS
# =========================================================

@app.route("/admin/users")
def admin_users():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            role
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_users.html",
        users=users
    )


# =========================================================
# ADMIN PRODUCTS
# =========================================================

@app.route("/admin/products")
def admin_products():

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    admin_product_list = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_products.html",
        products=admin_product_list
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route("/admin/products/add", methods=["GET", "POST"])
def admin_add_product():

    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("admin_product_form.html")

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    image = request.form.get("image", "").strip()

    try:

        price = float(
            request.form.get("price", 0)
        )

        stock = int(
            request.form.get("stock", 0)
        )

        rating = float(
            request.form.get("rating", 0)
        )

        reviews = int(
            request.form.get("reviews", 0)
        )

    except (TypeError, ValueError):

        return render_template(
            "admin_product_form.html",
            error="Please enter valid product values."
        )

    if not name or price < 0 or stock < 0:

        return render_template(
            "admin_product_form.html",
            error="Please enter valid product information."
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO products
        (
            name,
            price,
            description,
            image,
            stock,
            rating,
            reviews
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        price,
        description,
        image,
        stock,
        rating,
        reviews
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_products"))


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route(
    "/admin/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
def admin_edit_product(product_id):

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    if request.method == "GET":

        cursor.execute("""
            SELECT *
            FROM products
            WHERE id = ?
        """, (product_id,))

        product = cursor.fetchone()

        connection.close()

        if product is None:
            return "Product not found", 404

        return render_template(
            "admin_product_form.html",
            product=product
        )

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    image = request.form.get("image", "").strip()

    try:

        price = float(
            request.form.get("price", 0)
        )

        stock = int(
            request.form.get("stock", 0)
        )

        rating = float(
            request.form.get("rating", 0)
        )

        reviews = int(
            request.form.get("reviews", 0)
        )

    except (TypeError, ValueError):

        connection.close()

        return render_template(
            "admin_product_form.html",
            error="Please enter valid product values."
        )

    if not name or price < 0 or stock < 0:

        connection.close()

        return render_template(
            "admin_product_form.html",
            error="Please enter valid product information."
        )

    cursor.execute("""
        UPDATE products
        SET
            name = ?,
            price = ?,
            description = ?,
            image = ?,
            stock = ?,
            rating = ?,
            reviews = ?
        WHERE id = ?
    """, (
        name,
        price,
        description,
        image,
        stock,
        rating,
        reviews,
        product_id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_products"))


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route("/admin/products/delete/<int:product_id>")
def admin_delete_product(product_id):

    if not admin_required():
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (product_id,))

    connection.commit()
    connection.close()

    return redirect(url_for("admin_products"))


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# NORMAL LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )