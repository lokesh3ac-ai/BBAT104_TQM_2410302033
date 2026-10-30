import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory_q09.db")

VALID_ROLES = ("Store Administrator", "Inventory Manager", "Billing Cashier")
DEFAULT_ROLE = "Store Administrator"

DEFAULT_DEMO_ADMIN = "mega3ac"
DEFAULT_DEMO_ADMIN_PW = "@Mega123"

DEFAULT_DEMO_MANAGER = "manager1"
DEFAULT_DEMO_MANAGER_PW = "@Manager123"

DEFAULT_DEMO_CASHIER = "cashier1"
DEFAULT_DEMO_CASHIER_PW = "@Cashier123"

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
    """Initializes tables for Inventory, Defect Tracking, RBAC Users, Sales/POS, and GRN Inwarding."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Authentication, Store Settings, and strict RBAC constraint)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        store_name TEXT DEFAULT '',
        store_owner_name TEXT DEFAULT '',
        role TEXT CHECK(role IN ('Store Administrator', 'Inventory Manager', 'Billing Cashier')) NOT NULL DEFAULT 'Store Administrator',
        is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
        created_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Check if migration is needed for existing users table to enforce role CHECK & active/creator fields
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    users_sql_row = cursor.fetchone()
    if users_sql_row and users_sql_row[0]:
        users_sql = users_sql_row[0]
        if "Store Administrator" not in users_sql or "is_active" not in users_sql:
            cursor.execute("""
            CREATE TABLE users_migrated (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                store_name TEXT DEFAULT '',
                store_owner_name TEXT DEFAULT '',
                role TEXT CHECK(role IN ('Store Administrator', 'Inventory Manager', 'Billing Cashier')) NOT NULL DEFAULT 'Store Administrator',
                is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
                created_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            INSERT INTO users_migrated (id, username, password_hash, store_name, store_owner_name, role, is_active, created_by, created_at)
            SELECT 
                id, 
                username, 
                password_hash, 
                COALESCE(store_name, ''), 
                COALESCE(store_owner_name, ''), 
                CASE 
                    WHEN role = 'Administrator' THEN 'Store Administrator'
                    WHEN role IN ('Store Administrator', 'Inventory Manager', 'Billing Cashier') THEN role
                    ELSE 'Store Administrator'
                END,
                1,
                NULL,
                created_at 
            FROM users;
            """)
            cursor.execute("DROP TABLE users;")
            cursor.execute("ALTER TABLE users_migrated RENAME TO users;")

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

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_items_user_sku ON items (COALESCE(user_id, 0), sku);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id);")

    # 4. Sales / POS Invoices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        cashier_username TEXT NOT NULL,
        invoice_number TEXT UNIQUE NOT NULL,
        customer_name TEXT DEFAULT 'Walk-in Customer',
        payment_method TEXT CHECK(payment_method IN ('Cash', 'Card', 'UPI')) DEFAULT 'Cash',
        subtotal REAL NOT NULL,
        tax REAL DEFAULT 0.0,
        discount REAL DEFAULT 0.0,
        total_amount REAL NOT NULL,
        items_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_user_id ON sales(user_id);")

    # 5. Goods Receipt Notes (GRN) Inwarding Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goods_receipts (
        grn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        grn_number TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        sku TEXT NOT NULL,
        received_qty INTEGER NOT NULL CHECK(received_qty > 0),
        unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
        inwarded_by TEXT NOT NULL,
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_grn_user_id ON goods_receipts(user_id);")

    # Seed or configure Demo Administrator Account: mega3ac / @Mega123
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (DEFAULT_DEMO_ADMIN,))
    demo_row = cursor.fetchone()
    demo_pw_hash = generate_password_hash(DEFAULT_DEMO_ADMIN_PW)
    if not demo_row:
        cursor.execute("""
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role, is_active)
            VALUES (?, ?, 'MEGA MART', 'Lokesh Maurya', 'Store Administrator', 1)
        """, (DEFAULT_DEMO_ADMIN, demo_pw_hash))
        demo_admin_id = cursor.lastrowid
    else:
        demo_admin_id = demo_row[0]
        cursor.execute("""
            UPDATE users SET password_hash = ?, role = 'Store Administrator', is_active = 1 WHERE id = ?
        """, (demo_pw_hash, demo_admin_id))

    # Seed Demo Staff: manager1 (Inventory Manager)
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (DEFAULT_DEMO_MANAGER,))
    mgr_row = cursor.fetchone()
    mgr_pw_hash = generate_password_hash(DEFAULT_DEMO_MANAGER_PW)
    if not mgr_row:
        cursor.execute("""
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role, is_active, created_by)
            VALUES (?, ?, 'MEGA MART', 'Inventory Team', 'Inventory Manager', 1, ?)
        """, (DEFAULT_DEMO_MANAGER, mgr_pw_hash, demo_admin_id))
    else:
        cursor.execute("""
            UPDATE users SET password_hash = ?, role = 'Inventory Manager', is_active = 1, created_by = ? WHERE id = ?
        """, (mgr_pw_hash, demo_admin_id, mgr_row[0]))

    # Seed Demo Staff: cashier1 (Billing Cashier)
    cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (DEFAULT_DEMO_CASHIER,))
    csh_row = cursor.fetchone()
    csh_pw_hash = generate_password_hash(DEFAULT_DEMO_CASHIER_PW)
    if not csh_row:
        cursor.execute("""
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role, is_active, created_by)
            VALUES (?, ?, 'MEGA MART', 'Front Desk', 'Billing Cashier', 1, ?)
        """, (DEFAULT_DEMO_CASHIER, csh_pw_hash, demo_admin_id))
    else:
        cursor.execute("""
            UPDATE users SET password_hash = ?, role = 'Billing Cashier', is_active = 1, created_by = ? WHERE id = ?
        """, (csh_pw_hash, demo_admin_id, csh_row[0]))

    # Associate legacy unowned items with demo admin
    cursor.execute("UPDATE items SET user_id = ? WHERE user_id IS NULL OR user_id = 0", (demo_admin_id,))

    # Seed default catalog items ONLY for the demo account if empty
    cursor.execute("SELECT COUNT(*) FROM items WHERE user_id = ?", (demo_admin_id,))
    demo_item_count = cursor.fetchone()[0]
    if demo_item_count == 0:
        for sku, name, cat, qty, price, reorder in DEFAULT_SEED_ITEMS:
            cursor.execute("""
                INSERT OR IGNORE INTO items (user_id, sku, name, category, quantity, unit_price, reorder_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (demo_admin_id, sku, name, cat, qty, price, reorder))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized and RBAC roles verified successfully.")
