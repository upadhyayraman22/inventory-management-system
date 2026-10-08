from app import get_db, init_db
from datetime import datetime

init_db()
conn = get_db()

samples = [
    ("P001", "Wireless Mouse", "Accessories", 25, 799),
    ("P002", "Mechanical Keyboard", "Accessories", 12, 2499),
    ("P003", "USB-C Hub", "Electronics", 4, 1299),
    ("P004", "Webcam", "Electronics", 18, 1899),
    ("P005", "Laptop Stand", "Office", 3, 999),
]

for product in samples:
    try:
        conn.execute("""
            INSERT INTO products
            (product_id, name, category, quantity, price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (*product, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    except Exception:
        pass

conn.commit()
conn.close()
print("Sample data inserted.")
