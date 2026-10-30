import unittest
import os
import sqlite3
import app.database as db_mod
import app.inventory_logic as inv_logic
from app.desktop_web.server import app

TEST_DB = os.path.join(os.path.dirname(__file__), "test_isolation_temp.db")

class TestUserDataIsolation(unittest.TestCase):
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

    def setUp(self):
        self.client = app.test_client()

    def test_demo_account_has_seeded_items(self):
        res = self.client.post('/api/auth/login', json={'username': 'mega3ac', 'password': '@Mega123'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])

        # Verify inventory has seeded catalog items
        res_inv = self.client.get('/api/inventory')
        self.assertEqual(res_inv.status_code, 200)
        items = res_inv.get_json()['items']
        self.assertGreater(len(items), 0)

        # Verify stats reflect seeded catalog
        res_stats = self.client.get('/api/stats')
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()['inventory']
        self.assertEqual(stats['total_skus'], len(items))
        self.assertGreater(stats['total_units'], 0)

        self.client.post('/api/auth/logout')

    def test_new_user_starts_with_blank_inventory(self):
        import uuid
        username = f'iso_{uuid.uuid4().hex[:4]}'
        res_reg = self.client.post('/api/auth/register', json={
            'username': username,
            'password': 'SecurePassword123!',
            'store_name': 'My Clean Store'
        })
        self.assertEqual(res_reg.status_code, 200)

        # Inventory must be completely empty (0 items)
        res_inv = self.client.get('/api/inventory')
        self.assertEqual(res_inv.status_code, 200)
        items = res_inv.get_json()['items']
        self.assertEqual(len(items), 0)

        # Stats must be completely 0
        res_stats = self.client.get('/api/stats')
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()['inventory']
        self.assertEqual(stats['total_skus'], 0)
        self.assertEqual(stats['total_units'], 0)
        self.assertEqual(stats['total_valuation'], 0.0)
        self.assertEqual(stats['low_stock_count'], 0)

        # Adding an item only affects this user
        res_add = self.client.post('/api/inventory/add', json={
            'sku': 'SKU-ISO01',
            'name': 'Isolated Item',
            'category': 'Electronics',
            'quantity': 10,
            'unit_price': 100.0,
            'reorder_level': 2
        })
        self.assertEqual(res_add.status_code, 200)

        res_inv2 = self.client.get('/api/inventory')
        self.assertEqual(len(res_inv2.get_json()['items']), 1)

        self.client.post('/api/auth/logout')

        # Demo user does NOT see new user's item
        self.client.post('/api/auth/login', json={'username': 'mega3ac', 'password': '@Mega123'})
        res_demo_inv = self.client.get('/api/inventory')
        demo_skus = [i['sku'] for i in res_demo_inv.get_json()['items']]
        self.assertNotIn('SKU-ISO01', demo_skus)
        self.client.post('/api/auth/logout')

if __name__ == "__main__":
    unittest.main()
