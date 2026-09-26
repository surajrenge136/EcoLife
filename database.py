import sqlite3


DATABASE = "ecolife.db"


def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()


    # Users Table

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        role TEXT DEFAULT 'customer'

    )
    """)


    # Products Table

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


    # Orders Table

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


    # Order Items Table

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

    connection.close()


if __name__ == "__main__":

    initialize_database()

    print("EcoLife database initialized successfully! 🌱")