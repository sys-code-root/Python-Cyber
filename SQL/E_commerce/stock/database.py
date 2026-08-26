import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("inventory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY, 
        name TEXT, 
        current_stock INTEGER,
        status TEXT DEFAULT 'Active'
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        product_id INTEGER, 
        quantity INTEGER, 
        sale_date TEXT
    )
""")

cursor.execute("SELECT COUNT(*) FROM products")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?)",
        [(101, "Mechanical Keyboard", 15, "Active"), 
         (102, "Gaming Mouse", 80, "Active")]
    )
    today = datetime.now()
    d1 = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    d2 = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    d3 = (today - timedelta(days=3)).strftime('%Y-%m-%d')
    cursor.executemany(
        "INSERT INTO sales VALUES (?, ?, ?)",
        [(101, 5, d1), (101, 5, d2), (101, 5, d3),
         (102, 2, d1), (102, 4, d2), (102, 3, d3)]
    )
    conn.commit()