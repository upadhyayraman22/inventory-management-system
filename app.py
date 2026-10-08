from flask import Flask, request, jsonify, render_template
import sqlite3
from pathlib import Path
from datetime import datetime
import math
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "inventory.db"

MAX_PRODUCT_ID_LENGTH = 50
MAX_NAME_LENGTH = 120
MAX_CATEGORY_LENGTH = 80
MAX_QUANTITY = 1_000_000_000
MAX_PRICE = 1_000_000_000

try:
    LOW_STOCK_THRESHOLD = max(0, int(os.getenv("LOW_STOCK_THRESHOLD", "5")))
except ValueError:
    LOW_STOCK_THRESHOLD = 5

app = Flask(__name__)
app.config["LOW_STOCK_THRESHOLD"] = LOW_STOCK_THRESHOLD

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL COLLATE NOCASE UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price REAL NOT NULL CHECK(price >= 0),
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_products_product_id_nocase
        ON products(product_id COLLATE NOCASE)
    """)
    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row)

def validation_error(message):
    return jsonify({"error": message}), 400

def parse_text(value, label, maximum_length):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string.")
    value = value.strip()
    if not value:
        raise ValueError(f"{label} is required.")
    if len(value) > maximum_length:
        raise ValueError(f"{label} must be at most {maximum_length} characters.")
    return value

def parse_quantity(value):
    """Return a bounded, non-negative JSON integer or raise ValueError."""
    if type(value) is not int:
        raise ValueError("Quantity must be an integer.")
    if value < 0:
        raise ValueError("Quantity must be zero or greater.")
    if value > MAX_QUANTITY:
        raise ValueError(f"Quantity must be at most {MAX_QUANTITY}.")
    return value

def parse_price(value):
    """Return a bounded, finite, non-negative JSON number or raise ValueError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Price must be a number.")
    price = float(value)
    if not math.isfinite(price):
        raise ValueError("Price must be a finite number.")
    if price < 0:
        raise ValueError("Price must be zero or greater.")
    if price > MAX_PRICE:
        raise ValueError(f"Price must be at most {MAX_PRICE}.")
    return price

def parse_product(data, include_product_id=True):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    product = {
        "name": parse_text(data.get("name"), "Product name", MAX_NAME_LENGTH),
        "category": parse_text(data.get("category"), "Category", MAX_CATEGORY_LENGTH),
        "quantity": parse_quantity(data.get("quantity")),
        "price": parse_price(data.get("price")),
    }
    if include_product_id:
        product["product_id"] = parse_text(
            data.get("product_id"), "Product ID", MAX_PRODUCT_ID_LENGTH
        )
    return product

@app.route("/")
def index():
    return render_template("index.html")

@app.get("/api/products")
def get_products():
    search = request.args.get("search", "").strip()
    conn = get_db()
    if search:
        rows = conn.execute("""
            SELECT * FROM products
            WHERE product_id LIKE ?
               OR name LIKE ?
               OR category LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([row_to_dict(row) for row in rows])

@app.get("/api/products/<product_id>")
def get_product(product_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(row_to_dict(row))

@app.post("/api/products")
def add_product():
    try:
        product = parse_product(request.get_json(silent=True))
    except ValueError as error:
        return validation_error(str(error))

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO products
            (product_id, name, category, quantity, price, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product["product_id"], product["name"], product["category"],
              product["quantity"], product["price"],
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Product ID already exists."}), 409
    conn.close()
    return jsonify({"message": "Product added successfully."}), 201

@app.put("/api/products/<product_id>")
def update_product(product_id):
    try:
        product = parse_product(request.get_json(silent=True), include_product_id=False)
    except ValueError as error:
        return validation_error(str(error))

    conn = get_db()
    cur = conn.execute("""
        UPDATE products
        SET name = ?, category = ?, quantity = ?, price = ?
        WHERE product_id = ?
    """, (product["name"], product["category"], product["quantity"],
          product["price"], product_id))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": "Product not found."}), 404
    return jsonify({"message": "Product updated successfully."})

@app.delete("/api/products/<product_id>")
def delete_product(product_id):
    conn = get_db()
    cur = conn.execute(
        "DELETE FROM products WHERE product_id = ?", (product_id,)
    )
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        return jsonify({"error": "Product not found."}), 404
    return jsonify({"message": "Product deleted successfully."})

@app.get("/api/stats")
def stats():
    threshold = app.config["LOW_STOCK_THRESHOLD"]
    conn = get_db()
    total_products = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    total_quantity = conn.execute("SELECT COALESCE(SUM(quantity),0) AS s FROM products").fetchone()["s"]
    low_stock = conn.execute(
        "SELECT COUNT(*) AS c FROM products WHERE quantity <= ?", (threshold,)
    ).fetchone()["c"]
    total_value = conn.execute("SELECT COALESCE(SUM(quantity * price),0) AS v FROM products").fetchone()["v"]
    conn.close()
    return jsonify({
        "total_products": total_products,
        "total_quantity": total_quantity,
        "low_stock": low_stock,
        "low_stock_threshold": threshold,
        "total_value": round(total_value, 2)
    })

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
