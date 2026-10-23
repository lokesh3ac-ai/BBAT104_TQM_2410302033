import re
from app.database import get_connection
from app.bug_tracker import log_bug_to_db, log_system_error

def validate_item_data(sku: str, name: str, category: str, quantity: str, unit_price: str, reorder_level: str = "5"):
    """
    Poka-Yoke Validation Layer (Q09 Target):
    Prevents bad data entry before interacting with SQLite.
    """
    sku = str(sku).strip()
    name = str(name).strip()
    category = str(category).strip()

    # 1. SKU Format Check: Pattern 'SKU-XXXX' (alphanumeric 3 to 8 chars)
    if not re.match(r"^SKU-[A-Z0-9]{3,8}$", sku):
        raise ValueError("Invalid SKU format. Must match pattern 'SKU-XXXX' (e.g., SKU-101, SKU-AB01).")

    # 2. Item Name & Category Validation
    if not name or len(name) < 2:
        raise ValueError("Item name must be at least 2 characters long.")
    if not category:
        raise ValueError("Category cannot be blank.")

    # 3. Numeric & Boundary Checks
    try:
        qty = int(quantity)
    except ValueError:
        raise ValueError("Quantity must be a valid integer.")

    if qty < 0:
        raise ValueError("Quantity cannot be negative (Poka-Yoke lower limit violation).")

    try:
        price = float(unit_price)
    except ValueError:
        raise ValueError("Unit price must be a valid number.")

    if price <= 0:
        raise ValueError("Unit price must be strictly greater than 0.")

    try:
        reorder = int(reorder_level)
    except ValueError:
        raise ValueError("Reorder level must be an integer.")

    if reorder < 0:
        raise ValueError("Reorder level cannot be negative.")

    return sku, name, category, qty, price, reorder


def add_item(sku, name, category, quantity, unit_price, reorder_level="5"):
    """Adds a new inventory item with strict exception handling and logging."""
    conn = None
    try:
        v_sku, v_name, v_cat, v_qty, v_price, v_reorder = validate_item_data(
            sku, name, category, quantity, unit_price, reorder_level
        )
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO items (sku, name, category, quantity, unit_price, reorder_level)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (v_sku, v_name, v_cat, v_qty, v_price, v_reorder),
        )
        conn.commit()
        return True, "Item added successfully."
    except ValueError as ve:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        log_system_error("Validation", str(ve))
        log_bug_to_db("ValidationModule", "ValidationFailure", 2, f"Failed entry for SKU '{sku}': {ve}")
        return False, str(ve)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        error_msg = str(e)
        if "UNIQUE constraint failed" in error_msg:
            msg = f"Item with SKU '{sku}' already exists."
            defect_type = "DuplicateSKU"
        else:
            msg = f"Database operation failed: {error_msg}"
            defect_type = "DatabaseError"

        log_system_error("InventoryLogic", error_msg)
        log_bug_to_db("InventoryCRUD", defect_type, 4, f"SKU: {sku} | Error: {error_msg}")
        return False, msg
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def get_all_items():
    """Fetches all inventory items."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT item_id, sku, name, category, quantity, unit_price, reorder_level, created_at FROM items ORDER BY item_id DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        log_system_error("InventoryLogic", f"Fetch error: {e}")
        return []


def delete_item(identifier):
    """Safely deletes an item by SKU or numeric item_id."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        id_str = str(identifier).strip()
        if id_str.isdigit():
            cursor.execute("DELETE FROM items WHERE item_id = ? OR sku = ?", (int(id_str), id_str))
        else:
            cursor.execute("DELETE FROM items WHERE sku = ?", (id_str,))
        
        conn.commit()
        if cursor.rowcount == 0:
            return False, f"Item '{identifier}' not found in database."
        return True, f"Item '{identifier}' deleted successfully."
    except Exception as e:
        log_system_error("InventoryLogic", f"Delete error: {e}")
        log_bug_to_db("InventoryCRUD", "DeleteFailure", 3, str(e))
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def update_stock(sku: str, delta: int):
    """Adjusts stock levels (Stock In / Stock Out) with lower bound Poka-Yoke check."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM items WHERE sku = ?", (sku,))
        row = cursor.fetchone()
        if not row:
            return False, "Item not found."

        current_qty = row[0]
        new_qty = current_qty + delta
        if new_qty < 0:
            raise ValueError(f"Insufficient stock. Available: {current_qty}, Requested deduction: {abs(delta)}")

        cursor.execute("UPDATE items SET quantity = ? WHERE sku = ?", (new_qty, sku))
        conn.commit()
        return True, f"Stock updated. New Quantity: {new_qty}"
    except ValueError as ve:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        log_system_error("StockControl", str(ve))
        log_bug_to_db("StockModule", "NegativeStockAttempt", 3, str(ve))
        return False, str(ve)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        log_system_error("StockControl", f"Update error: {e}")
        log_bug_to_db("StockModule", "UpdateFailure", 4, str(e))
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def update_item_details(sku: str, name: str, category: str, unit_price: str, reorder_level: str):
    """Updates non-stock attributes of an existing item with validation."""
    conn = None
    try:
        # Validate input parameters
        name = str(name).strip()
        category = str(category).strip()
        if not name or len(name) < 2:
            raise ValueError("Item name must be at least 2 characters long.")
        if not category:
            raise ValueError("Category cannot be blank.")

        try:
            price = float(unit_price)
        except ValueError:
            raise ValueError("Unit price must be a valid number.")
        if price <= 0:
            raise ValueError("Unit price must be strictly greater than 0.")

        try:
            reorder = int(reorder_level)
        except ValueError:
            raise ValueError("Reorder level must be an integer.")
        if reorder < 0:
            raise ValueError("Reorder level cannot be negative.")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE items
            SET name = ?, category = ?, unit_price = ?, reorder_level = ?
            WHERE sku = ?
            """,
            (name, category, price, reorder, sku)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, f"Item with SKU '{sku}' not found."
        return True, f"Item '{sku}' updated successfully."
    except ValueError as ve:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        log_system_error("Validation", str(ve))
        log_bug_to_db("ValidationModule", "ValidationFailure", 2, f"Failed update for SKU '{sku}': {ve}")
        return False, str(ve)
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
                conn = None
            except Exception:
                pass
        log_system_error("InventoryLogic", f"Update item error: {e}")
        log_bug_to_db("InventoryCRUD", "UpdateFailure", 4, str(e))
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def get_all_categories():
    """Returns list of distinct categories present in inventory."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM items ORDER BY category ASC")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return ["Peripherals", "Display", "Electronics", "Accessories"]


def get_inventory_statistics():
    """Computes high-level KPI metrics for the inventory dashboard."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_skus,
                COALESCE(SUM(quantity), 0) as total_units,
                COALESCE(SUM(quantity * unit_price), 0.0) as total_valuation,
                COALESCE(SUM(CASE WHEN quantity <= reorder_level THEN 1 ELSE 0 END), 0) as low_stock_count,
                COALESCE(SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END), 0) as out_of_stock_count
            FROM items
        """)
        row = cursor.fetchone()
        conn.close()
        return {
            "total_skus": row[0] or 0,
            "total_units": row[1] or 0,
            "total_valuation": float(row[2] or 0.0),
            "low_stock_count": row[3] or 0,
            "out_of_stock_count": row[4] or 0
        }
    except Exception as e:
        log_system_error("InventoryLogic", f"Stats calculation error: {e}")
        return {
            "total_skus": 0,
            "total_units": 0,
            "total_valuation": 0.0,
            "low_stock_count": 0,
            "out_of_stock_count": 0
        }
