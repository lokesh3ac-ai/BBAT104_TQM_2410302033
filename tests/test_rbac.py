import unittest
import json
import uuid
from app.desktop_web.server import app
from app.database import (
    init_db,
    DEFAULT_DEMO_ADMIN,
    DEFAULT_DEMO_ADMIN_PW,
    DEFAULT_DEMO_MANAGER,
    DEFAULT_DEMO_MANAGER_PW,
    DEFAULT_DEMO_CASHIER,
    DEFAULT_DEMO_CASHIER_PW
)

class TestRoleBasedAccessControl(unittest.TestCase):
    def setUp(self):
        init_db()
        self.app = app.test_client()
        self.app.testing = True

    def test_demo_user_roles_authentication(self):
        """Verify that demo accounts for all three roles authenticate and carry correct roles."""
        # 1. Admin
        res_admin = self.app.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_ADMIN,
            "password": DEFAULT_DEMO_ADMIN_PW
        })
        self.assertEqual(res_admin.status_code, 200)
        data_admin = res_admin.get_json()
        self.assertEqual(data_admin["user"]["role"], "Store Administrator")

        # 2. Manager
        res_mgr = self.app.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_MANAGER,
            "password": DEFAULT_DEMO_MANAGER_PW
        })
        self.assertEqual(res_mgr.status_code, 200)
        data_mgr = res_mgr.get_json()
        self.assertEqual(data_mgr["user"]["role"], "Inventory Manager")

        # 3. Cashier
        res_csh = self.app.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_CASHIER,
            "password": DEFAULT_DEMO_CASHIER_PW
        })
        self.assertEqual(res_csh.status_code, 200)
        data_csh = res_csh.get_json()
        self.assertEqual(data_csh["user"]["role"], "Billing Cashier")

    def test_admin_staff_management_lifecycle(self):
        """Store Administrator can create staff, toggle their status, and deactivated staff cannot login."""
        # Login as Admin
        self.app.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_ADMIN,
            "password": DEFAULT_DEMO_ADMIN_PW
        })

        # Create new staff cashier
        staff_user = f"csh_{uuid.uuid4().hex[:6]}"
        res_create = self.app.post("/api/staff/create", json={
            "username": staff_user,
            "password": "@Staff123",
            "role": "Billing Cashier"
        })
        self.assertEqual(res_create.status_code, 200)
        staff_data = res_create.get_json()["staff"]
        staff_id = staff_data["id"]

        # List staff
        res_list = self.app.get("/api/staff")
        self.assertEqual(res_list.status_code, 200)
        staff_ids = [s["id"] for s in res_list.get_json()["staff"]]
        self.assertIn(staff_id, staff_ids)

        # Toggle status to deactivated
        res_toggle = self.app.post("/api/staff/toggle-status", json={"staff_id": staff_id})
        self.assertEqual(res_toggle.status_code, 200)

        # Attempt to login with deactivated staff account -> should fail
        client_staff = app.test_client()
        res_staff_login = client_staff.post("/api/auth/login", json={
            "username": staff_user,
            "password": "@Staff123"
        })
        self.assertEqual(res_staff_login.status_code, 401)
        self.assertIn("deactivated", res_staff_login.get_json()["message"].lower())

        # Reactivate staff
        res_toggle_back = self.app.post("/api/staff/toggle-status", json={"staff_id": staff_id})
        self.assertEqual(res_toggle_back.status_code, 200)

        # Now staff can log in
        res_staff_login2 = client_staff.post("/api/auth/login", json={
            "username": staff_user,
            "password": "@Staff123"
        })
        self.assertEqual(res_staff_login2.status_code, 200)

    def test_inventory_manager_permissions_and_restrictions(self):
        """Inventory Manager can manage inventory and GRN inwarding, but cannot access staff or clear logs."""
        client = app.test_client()
        # Login as Inventory Manager
        client.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_MANAGER,
            "password": DEFAULT_DEMO_MANAGER_PW
        })

        # Can add inventory
        sku = f"SKU-{uuid.uuid4().hex[:4].upper()}"
        res_add = client.post("/api/inventory/add", json={
            "sku": sku,
            "name": "Manager Inwarded Item",
            "category": "Electronics",
            "quantity": 10,
            "unit_price": 500.0,
            "reorder_level": 5
        })
        self.assertEqual(res_add.status_code, 200)

        # Can inward GRN
        res_grn = client.post("/api/inventory/grn", json={
            "sku": sku,
            "supplier_name": "Apex Electronics Ltd",
            "received_qty": 15,
            "unit_cost": 420.0
        })
        self.assertEqual(res_grn.status_code, 200)
        self.assertEqual(res_grn.get_json()["new_stock"], 25)

        # Cannot access staff management -> 403 Forbidden
        res_staff = client.get("/api/staff")
        self.assertEqual(res_staff.status_code, 403)
        self.assertIn("403 Forbidden", res_staff.get_json()["message"])

        # Cannot clear system logs -> 403 Forbidden
        res_logs = client.post("/api/logs/clear")
        self.assertEqual(res_logs.status_code, 403)

        # Cannot delete account -> 403 Forbidden
        res_del = client.post("/api/auth/delete-account", json={"password": DEFAULT_DEMO_MANAGER_PW})
        self.assertEqual(res_del.status_code, 403)

    def test_billing_cashier_pos_and_restrictions(self):
        """Billing Cashier has read-only catalog access, cannot edit/delete/add items, but can process checkout."""
        client = app.test_client()
        # Login as Billing Cashier
        client.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_CASHIER,
            "password": DEFAULT_DEMO_CASHIER_PW
        })

        # Read-only catalog is allowed
        res_inv = client.get("/api/inventory")
        self.assertEqual(res_inv.status_code, 200)
        items = res_inv.get_json()["items"]
        self.assertGreater(len(items), 0)

        # Cannot add new SKU -> 403 Forbidden
        res_add = client.post("/api/inventory/add", json={
            "sku": "SKU-HACK",
            "name": "Disallowed Item",
            "category": "Electronics",
            "quantity": 1,
            "unit_price": 10.0
        })
        self.assertEqual(res_add.status_code, 403)

        # Cannot delete SKU -> 403 Forbidden
        res_del = client.delete("/api/inventory/delete/SKU-1002")
        self.assertEqual(res_del.status_code, 403)

        # Cannot modify stock directly -> 403 Forbidden
        res_stock = client.post("/api/inventory/stock", json={"sku": "SKU-1002", "delta": 5})
        self.assertEqual(res_stock.status_code, 403)

        # Cannot access Defect Tracker -> 403 Forbidden
        res_bugs = client.get("/api/bugs")
        self.assertEqual(res_bugs.status_code, 403)

        # Cannot access Logs -> 403 Forbidden
        res_logs = client.get("/api/logs")
        self.assertEqual(res_logs.status_code, 403)

        # Can perform POS Checkout
        test_item = items[0]
        initial_stock = test_item["quantity"]
        if initial_stock > 1:
            res_checkout = client.post("/api/pos/checkout", json={
                "customer_name": "Test Customer",
                "payment_method": "Card",
                "items": [{"sku": test_item["sku"], "quantity": 1}],
                "discount": 0.0
            })
            self.assertEqual(res_checkout.status_code, 200)
            chk_data = res_checkout.get_json()
            self.assertTrue(chk_data["success"])
            self.assertIn("INV-", chk_data["invoice_number"])

            # Verify stock deduction
            res_inv_after = client.get("/api/inventory")
            items_after = {it["sku"]: it["quantity"] for it in res_inv_after.get_json()["items"]}
            self.assertEqual(items_after[test_item["sku"]], initial_stock - 1)

    def test_pos_insufficient_stock_rejection(self):
        """Poka-yoke: Cashier cannot sell more stock than is available."""
        client = app.test_client()
        client.post("/api/auth/login", json={
            "username": DEFAULT_DEMO_CASHIER,
            "password": DEFAULT_DEMO_CASHIER_PW
        })

        res_checkout = client.post("/api/pos/checkout", json={
            "customer_name": "Greedy Buyer",
            "payment_method": "Cash",
            "items": [{"sku": "SKU-1002", "quantity": 999999}],
            "discount": 0.0
        })
        self.assertEqual(res_checkout.status_code, 400)
        self.assertIn("insufficient stock", res_checkout.get_json()["message"].lower())


if __name__ == "__main__":
    unittest.main()
