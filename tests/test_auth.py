import unittest
import os
import sqlite3
import app.database as db_mod
import app.auth as auth_mod

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
        auth_mod.register_user("alice", "pass123")
        success, err = auth_mod.register_user("alice", "anotherpass")
        self.assertFalse(success)
        self.assertIn("already registered", err.lower())

    def test_invalid_login_credentials(self):
        auth_mod.register_user("bob", "secret")
        
        # Wrong password
        ok, err = auth_mod.authenticate_user("bob", "wrongpass")
        self.assertFalse(ok)
        self.assertIn("invalid", err.lower())

        # Non-existent user
        ok, err = auth_mod.authenticate_user("charlie", "secret")
        self.assertFalse(ok)
        self.assertIn("invalid", err.lower())

    def test_update_store_settings(self):
        auth_mod.register_user("david", "pass123", "Old Store", "Dave")
        ok, msg = auth_mod.update_store_settings("david", "New Supermart", "David M.")
        self.assertTrue(ok)

        profile = auth_mod.get_user_profile("david")
        self.assertEqual(profile["store_name"], "New Supermart")
        self.assertEqual(profile["store_owner_name"], "David M.")

    def test_delete_user_account(self):
        auth_mod.register_user("eva", "mypassword")
        
        # Wrong password fails
        ok_fail, msg_fail = auth_mod.delete_user_account("eva", "incorrect")
        self.assertFalse(ok_fail)
        self.assertIn("incorrect password", msg_fail.lower())

        # Correct password succeeds
        ok_del, msg_del = auth_mod.delete_user_account("eva", "mypassword")
        self.assertTrue(ok_del)

        # Confirm user is gone
        profile = auth_mod.get_user_profile("eva")
        self.assertIsNone(profile)
