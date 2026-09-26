import sqlite3

connection = sqlite3.connect("ecolife.db")
cursor = connection.cursor()

# Remove old product records
cursor.execute("DELETE FROM products")


# Add EcoLife products
products = [
    (
        "Eco Bottle",
        299,
        "Reusable eco-friendly bottle designed for everyday hydration.",
        "bottle.jpg",
        50,
        4.8,
        124
    ),

    (
        "Organic Tote Bag",
        199,
        "Reusable organic cotton tote bag perfect for shopping and daily use.",
        "bag.jpg",
        50,
        4.6,
        89
    ),

    (
        "Bamboo Essentials",
        249,
        "Sustainable bamboo products designed for a greener home.",
        "bamboo.jpg",
        50,
        4.7,
        106
    ),

    (
        "Solar Light",
        599,
        "Simple solar-powered lighting solution for your everyday needs.",
        "solar.jpg",
        50,
        4.9,
        157
    )
]


cursor.executemany("""
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
""", products)


connection.commit()
connection.close()


print("====================================")
print("EcoLife products added successfully!")
print("====================================")
print("1. Eco Bottle")
print("2. Organic Tote Bag")
print("3. Bamboo Essentials")
print("4. Solar Light")
print("====================================")