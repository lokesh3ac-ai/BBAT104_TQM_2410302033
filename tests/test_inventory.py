import unittest
import os
import sqlite3
import app.database as db_mod
import app.inventory_logic as inv_logic

TEST_DB = os.path.join(os.path.dirname(__file__), "test_temp.db")

class TestInventoryQualityControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_mod.DB_PATH = TEST_DB
        db_mod.init_db()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except Exception:
                pass

    def clean_table(self):
        conn = sqlite3.connect(TEST_DB, timeout=20)
        try:
            with conn:
                conn.execute("DELETE FROM items;")
        finally:
            conn.close()

    def setUp(self):
        self.clean_table()

    # Test 1: Valid item creation
    def test_add_item_success(self):
        success, msg = inv_logic.add_item("SKU-101", "Keyboard", "Peripherals", "10", "450.0", "5")
        self.assertTrue(success)
        self.assertIn("successfully", msg.lower())

    # Test 2: Poka-Yoke Regex Pattern rejection for malformed SKU
    def test_invalid_sku_format(self):
        with self.assertRaises(ValueError):
            inv_logic.validate_item_data("INVALID_SKU_123", "Monitor", "Display", "5", "5000")

    # Test 3: Poka-Yoke Lower Bound rejection for negative quantity
    def test_negative_quantity_rejection(self):
        with self.assertRaises(ValueError):
            inv_logic.validate_item_data("SKU-102", "Mouse", "Peripherals", "-5", "300")

    # Test 4: Poka-Yoke Boundary check for zero or negative price
    def test_non_positive_price_rejection(self):
        with self.assertRaises(ValueError):
            inv_logic.validate_item_data("SKU-103", "Mouse Pad", "Accessories", "10", "0")
        with self.assertRaises(ValueError):
            inv_logic.validate_item_data("SKU-104", "Mouse Pad", "Accessories", "10", "-50")

    # Test 5: Duplicate SKU prevention (SQLite UNIQUE constraint)
    def test_duplicate_sku_handling(self):
        inv_logic.add_item("SKU-105", "Webcam", "Electronics", "2", "1200", "1")
        success, msg = inv_logic.add_item("SKU-105", "Duplicate Webcam", "Electronics", "5", "1200", "1")
        self.assertFalse(success)
        self.assertIn("already exists", msg)

    # Test 6: Stock deduction preventing negative inventory
    def test_stock_deduction_lower_bound(self):
        inv_logic.add_item("SKU-106", "Cable", "Electronics", "5", "150", "2")
        success, msg = inv_logic.update_stock("SKU-106", -10)
        self.assertFalse(success)
        self.assertIn("insufficient stock", msg.lower())

if __name__ == "__main__":
    unittest.main()