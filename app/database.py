import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory_q09.db")

def get_connection():
    """Returns a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables for Inventory and Q09 Bug Tracking."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Base Inventory Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        unit_price REAL NOT NULL CHECK(unit_price > 0),
        reorder_level INTEGER NOT NULL DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Q09 In-App Bug Tracker Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bug_reports (
        bug_id INTEGER PRIMARY KEY AUTOINCREMENT,
        module_name TEXT NOT NULL,
        defect_type TEXT NOT NULL,
        severity INTEGER NOT NULL CHECK(severity BETWEEN 1 AND 5),
        description TEXT NOT NULL,
        status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'In-Progress', 'Resolved')),
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")