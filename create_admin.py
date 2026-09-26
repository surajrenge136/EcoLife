import sqlite3
import hashlib

connection = sqlite3.connect("ecolife.db")
cursor = connection.cursor()

name = "EcoLife Admin"
email = "admin@ecolife.com"
password = "Admin@123"

password_hash = hashlib.sha256(
    password.encode()
).hexdigest()

cursor.execute("""
    INSERT OR REPLACE INTO users
    (name, email, password, role)
    VALUES (?, ?, ?, ?)
""", (
    name,
    email,
    password_hash,
    "admin"
))

connection.commit()
connection.close()

print("Admin account created successfully!")
print("Email: admin@ecolife.com")
print("Password: Admin@123")