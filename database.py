import os
import sqlite3

DATABASE = "ecolife.db"
DATABASE_URL = os.environ.get("DATABASE_URL")


# =========================================================
# POSTGRES QMARK COMPATIBILITY
# =========================================================

class PostgresCursor:

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("?", "%s")

        if params is None:
            return self.cursor.execute(query)

        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self.cursor, name)


class PostgresConnection:

    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        from psycopg2.extras import RealDictCursor

        cursor = self.connection.cursor(
            cursor_factory=RealDictCursor
        )

        return PostgresCursor(cursor)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    # Production / Render PostgreSQL
    if DATABASE_URL:

        import psycopg2

        connection = psycopg2.connect(
            DATABASE_URL
        )

        return PostgresConnection(connection)

    # Local development SQLite
    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# SEED DEFAULT PRODUCTS
# =========================================================

def seed_default_products(connection):

    cursor = connection.cursor()

    # Check whether products already exist
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM products
    """)

    result = cursor.fetchone()

    if DATABASE_URL:
        product_count = result["count"]
    else:
        product_count = result["count"]

    # Do not duplicate products
    if product_count > 0:
        return

    products = [

        (
            "Eco Bottle",
            299,
            "Reusable eco-friendly bottle made for everyday hydration.",
            "bottle.jpg",
            50,
            4.8,
            124
        ),

        (
            "Organic Tote Bag",
            199,
            "Durable organic cotton tote bag for shopping and everyday use.",
            "bag.jpg",
            50,
            4.6,
            89
        ),

        (
            "Bamboo Essentials",
            249,
            "Eco-friendly bamboo essentials for a sustainable lifestyle.",
            "bamboo.jpg",
            50,
            4.7,
            106
        ),

        (
            "Solar Light",
            599,
            "Energy-saving solar light powered by renewable energy.",
            "solar.jpg",
            50,
            4.9,
            157
        )

    ]

    for product in products:

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
        """, product)

    connection.commit()

    print("Default EcoLife products added successfully! 🌱")


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    if DATABASE_URL:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
        """)

    else:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        )
        """)

    # -----------------------------------------------------
    # PRODUCTS
    # -----------------------------------------------------

    if DATABASE_URL:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            reviews INTEGER DEFAULT 0
        )
        """)

    else:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            reviews INTEGER DEFAULT 0
        )
        """)

    # -----------------------------------------------------
    # ORDERS
    # -----------------------------------------------------

    if DATABASE_URL:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            payment TEXT NOT NULL,
            total REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    else:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            pincode TEXT NOT NULL,
            payment TEXT NOT NULL,
            total REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    # -----------------------------------------------------
    # ORDER ITEMS
    # -----------------------------------------------------

    if DATABASE_URL:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            item_total REAL NOT NULL
        )
        """)

    else:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            item_total REAL NOT NULL
        )
        """)

    connection.commit()

    # -----------------------------------------------------
    # ADD DEFAULT PRODUCTS IF DATABASE IS EMPTY
    # -----------------------------------------------------

    seed_default_products(connection)

    connection.close()


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":

    initialize_database()

    if DATABASE_URL:
        print("EcoLife PostgreSQL database initialized successfully! 🌱")
    else:
        print("EcoLife SQLite database initialized successfully! 🌱")