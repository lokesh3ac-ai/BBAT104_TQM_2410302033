import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory_q09.db")

DEFAULT_DEMO_USERNAME = "mega3ac"
DEFAULT_DEMO_PASSWORD = "@Mega123"

DEFAULT_SEED_ITEMS = [
    ("SKU-1002", "Mechanical RGB Keyboard", "Peripherals", 24, 3499.0, 5),
    ("SKU-1003", "Ultra-Wide Gaming Monitor 27\"", "Display", 3, 18500.0, 5),
    ("SKU-1004", "Braided Type-C Fast Cable", "Accessories", 50, 299.0, 10),
    ("SKU-1005", "High-Speed USB 3.2 Pendrive 128GB", "Storage", 40, 899.0, 8),
    ("SKU-1006", "Ergonomic Vertical Mouse", "Peripherals", 2, 1450.0, 4),
    ("SKU-1007", "Noise-Cancelling Wireless Headset", "Audio", 15, 4200.0, 5),
    ("SKU-1008", "Cat6 High-Speed Ethernet Cable 10m", "Networking", 35, 350.0, 8),
    ("SKU-1009", "4K Ultra-HD Stream Webcam", "Electronics", 2, 6200.0, 3),
]

def get_connection():
    """Returns a SQLite connection with foreign keys enabled and concurrency timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes tables for Inventory, Defect Tracking, and Users with data isolation."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Authentication & Store Settings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        store_name TEXT DEFAULT '',
        store_owner_name TEXT DEFAULT '',
        role TEXT DEFAULT 'Administrator',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Defect Tracker Table
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

    # 3. Base Inventory Master Table (with user_id foreign key)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        sku TEXT NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        unit_price REAL NOT NULL CHECK(unit_price > 0),
        reorder_level INTEGER NOT NULL DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check if migration is needed for existing items table lacking user_id
    cursor.execute("PRAGMA table_info(items)")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("""
        CREATE TABLE items_migrated (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            unit_price REAL NOT NULL CHECK(unit_price > 0),
            reorder_level INTEGER NOT NULL DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        INSERT INTO items_migrated (item_id, sku, name, category, quantity, unit_price, reorder_level, created_at)
        SELECT item_id, sku, name, category, quantity, unit_price, reorder_level, created_at FROM items;
        """)
        cursor.execute("DROP TABLE items;")
        cursor.execute("ALTER TABLE items_migrated RENAME TO items;")

    # Unique constraint per user: allows each user to own their SKUs while rejecting duplicates for the same user
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_items_user_sku ON items (COALESCE(user_id, 0), sku);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id);")

    # Seed or configure Demo Account: mega3ac / @Mega123
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (DEFAULT_DEMO_USERNAME,))
    demo_row = cursor.fetchone()
    demo_pw_hash = generate_password_hash(DEFAULT_DEMO_PASSWORD)
    if not demo_row:
        cursor.execute("""
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role)
            VALUES (?, ?, 'MEGA MART', 'Lokesh Maurya', 'Administrator')
        """, (DEFAULT_DEMO_USERNAME, demo_pw_hash))
        demo_user_id = cursor.lastrowid
    else:
        demo_user_id = demo_row[0]
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (demo_pw_hash, demo_user_id))

    # Associate legacy unowned items with demo user
    cursor.execute("UPDATE items SET user_id = ? WHERE user_id IS NULL OR user_id = 0", (demo_user_id,))

    # Seed default catalog items ONLY for the demo account if empty
    cursor.execute("SELECT COUNT(*) FROM items WHERE user_id = ?", (demo_user_id,))
    demo_item_count = cursor.fetchone()[0]
    if demo_item_count == 0:
        for sku, name, cat, qty, price, reorder in DEFAULT_SEED_ITEMS:
            cursor.execute("""
                INSERT OR IGNORE INTO items (user_id, sku, name, category, quantity, unit_price, reorder_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (demo_user_id, sku, name, cat, qty, price, reorder))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and demo account verified successfully.")
