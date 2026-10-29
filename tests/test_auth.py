import unittest
import os
import sqlite3
import app.database as db_mod
import app.auth as auth_mod
from app.desktop_web.server import app

TEST_DB = os.path.join(os.path.dirname(__file__), "test_auth_temp.db")

class TestUserAuthenticationAndSettings(unittest.TestCase):
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
        conn = sqlite3.connect(TEST_DB, timeout=20)
        try:
            with conn:
                conn.execute("DELETE FROM users;")
        finally:
            conn.close()

    def test_register_and_authenticate_success(self):
        success, user = auth_mod.register_user("lokesh", "SecurePass123!", "Tech Haven", "Lokesh Maurya")
        self.assertTrue(success)
        self.assertIsInstance(user, dict)
        self.assertEqual(user["username"], "lokesh")
        self.assertEqual(user["store_name"], "Tech Haven")

        # Authenticate with correct credentials
        auth_ok, auth_user = auth_mod.authenticate_user("lokesh", "SecurePass123!")
        self.assertTrue(auth_ok)
        self.assertEqual(auth_user["username"], "lokesh")

    def test_duplicate_username_rejected(self):
        auth_mod.register_user("alice", "Pass1234#")
        success, err = auth_mod.register_user("alice", "AnotherPass99$")
        self.assertFalse(success)
        self.assertIn("already registered", err.lower())

    def test_username_max_length_rejected(self):
        # 14 characters should be rejected (limit is 13)
        long_username = "user1234567890"  # 14 chars
        success, err = auth_mod.register_user(long_username, "Pass1234#")
        self.assertFalse(success)
        self.assertEqual(err, "Username must not exceed 13 characters.")

        # Exactly 13 chars should be accepted
        exact_username = "user123456789"  # 13 chars
        success, user = auth_mod.register_user(exact_username, "Pass1234#")
        self.assertTrue(success)

    def test_password_complexity_enforcement(self):
        # Missing uppercase
        ok, err = auth_mod.register_user("user1", "weakpass123#")
        self.assertFalse(ok)
        self.assertEqual(err, "Password must include at least one uppercase letter, one number, and one special character.")

        # Missing numeric digit
        ok, err = auth_mod.register_user("user2", "WeakPassword#")
        self.assertFalse(ok)
        self.assertEqual(err, "Password must include at least one uppercase letter, one number, and one special character.")

        # Missing special character
        ok, err = auth_mod.register_user("user3", "WeakPass1234")
        self.assertFalse(ok)
        self.assertEqual(err, "Password must include at least one uppercase letter, one number, and one special character.")

        # Valid strong password
        ok, user = auth_mod.register_user("user4", "ValidPass123@")
        self.assertTrue(ok)

    def test_invalid_login_credentials(self):
        auth_mod.register_user("bob", "SecretPass123#")
        
        # Wrong password
        ok, err = auth_mod.authenticate_user("bob", "WrongPass123#")
        self.assertFalse(ok)
        self.assertIn("invalid", err.lower())

        # Non-existent user
        ok, err = auth_mod.authenticate_user("charlie", "SecretPass123#")
        self.assertFalse(ok)
        self.assertIn("invalid", err.lower())

    def test_update_store_settings(self):
        auth_mod.register_user("david", "StrongPass123!", "Old Store", "Dave")
        ok, msg = auth_mod.update_store_settings("david", "New Supermart", "David M.")
        self.assertTrue(ok)

        profile = auth_mod.get_user_profile("david")
        self.assertEqual(profile["store_name"], "New Supermart")
        self.assertEqual(profile["store_owner_name"], "David M.")

    def test_delete_user_account(self):
        auth_mod.register_user("eva", "MyPassword123#")
        
        # Wrong password fails
        ok_fail, msg_fail = auth_mod.delete_user_account("eva", "incorrect")
        self.assertFalse(ok_fail)
        self.assertIn("incorrect password", msg_fail.lower())

        # Correct password succeeds
        ok_del, msg_del = auth_mod.delete_user_account("eva", "MyPassword123#")
        self.assertTrue(ok_del)

        # Confirm user is gone
        profile = auth_mod.get_user_profile("eva")
        self.assertIsNone(profile)

    def test_api_validation_routes(self):
        client = app.test_client()

        # Test registration with username > 13 chars
        res = client.post('/api/auth/register', json={
            'username': 'verylongusername',
            'password': 'ValidPass123!'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Username must not exceed 13 characters.", res.get_json()["message"])

        # Test registration with weak password (missing special char)
        res = client.post('/api/auth/register', json={
            'username': 'validuser',
            'password': 'NoSpecialChar12'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Password must include at least one uppercase letter, one number, and one special character.", res.get_json()["message"])

        # Test registration with weak password (missing uppercase)
        res = client.post('/api/auth/register', json={
            'username': 'validuser',
            'password': 'nouppercase12!'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Password must include at least one uppercase letter, one number, and one special character.", res.get_json()["message"])

        # Test registration with weak password (missing number)
        res = client.post('/api/auth/register', json={
            'username': 'validuser',
            'password': 'NoNumberPassword!'
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Password must include at least one uppercase letter, one number, and one special character.", res.get_json()["message"])

        # Test valid registration via API
        res = client.post('/api/auth/register', json={
            'username': 'validuser',
            'password': 'ValidPass123!',
            'store_name': 'Valid Mart'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["success"])
