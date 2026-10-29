import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_connection

def register_user(username: str, password: str, store_name: str = "", store_owner_name: str = ""):
    """
    Registers a new user in the SQLite database with a hashed password.
    Returns (True, user_dict) on success, or (False, error_message).
    """
    username = str(username).strip()
    password = str(password).strip()
    store_name = str(store_name).strip()
    store_owner_name = str(store_owner_name).strip()

    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if username already exists (case-insensitive)
        cursor.execute("SELECT id FROM users WHERE username = ? COLLATE NOCASE", (username,))
        if cursor.fetchone():
            return False, f"Username '{username}' is already registered. Please choose another."

        password_hash = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role)
            VALUES (?, ?, ?, ?, 'Administrator')
            """,
            (username, password_hash, store_name, store_owner_name)
        )
        conn.commit()
        user_id = cursor.lastrowid

        return True, {
            "id": user_id,
            "username": username,
            "store_name": store_name,
            "store_owner_name": store_owner_name,
            "role": "Administrator"
        }
    except Exception as e:
        return False, f"Failed to register user: {e}"
    finally:
        if conn:
            conn.close()


def authenticate_user(username: str, password: str):
    """
    Authenticates a user by checking the password hash in SQLite.
    Returns (True, user_dict) on success, or (False, error_message).
    """
    username = str(username).strip()
    password = str(password).strip()

    if not username or not password:
        return False, "Please enter both username and password."

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, store_name, store_owner_name, role, created_at
            FROM users WHERE username = ? COLLATE NOCASE
            """,
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return False, "Invalid username or password."

        u_id, u_name, u_hash, s_name, s_owner, role, created_at = row
        if not check_password_hash(u_hash, password):
            return False, "Invalid username or password."

        return True, {
            "id": u_id,
            "username": u_name,
            "store_name": s_name or "",
            "store_owner_name": s_owner or "",
            "role": role or "Administrator",
            "created_at": created_at
        }
    except Exception as e:
        return False, f"Authentication error: {e}"
    finally:
        if conn:
            conn.close()


def get_user_profile(username: str):
    """Retrieves full profile and store configuration for a username."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, store_name, store_owner_name, role, created_at
            FROM users WHERE username = ? COLLATE NOCASE
            """,
            (username.strip(),)
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "store_name": row[2] or "",
            "store_owner_name": row[3] or "",
            "role": row[4] or "Administrator",
            "created_at": row[5]
        }
    finally:
        if conn:
            conn.close()


def update_store_settings(username: str, store_name: str, store_owner_name: str):
    """Updates the store name and store owner name for a user."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET store_name = ?, store_owner_name = ?
            WHERE username = ? COLLATE NOCASE
            """,
            (store_name.strip(), store_owner_name.strip(), username.strip())
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, "User account not found."
        return True, "Store settings saved successfully."
    except Exception as e:
        return False, f"Failed to update store settings: {e}"
    finally:
        if conn:
            conn.close()


def delete_user_account(username: str, password: str):
    """
    Deletes the user account permanently after verifying the password confirmation.
    Returns (True, message) on success or (False, error_message).
    """
    username = str(username).strip()
    password = str(password).strip()

    if not password:
        return False, "Password confirmation is required to delete your account."

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = ? COLLATE NOCASE",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return False, "User account not found."

        u_id, u_hash = row
        if not check_password_hash(u_hash, password):
            return False, "Incorrect password. Account deletion canceled."

        cursor.execute("DELETE FROM users WHERE id = ?", (u_id,))
        conn.commit()
        return True, "Account permanently deleted."
    except Exception as e:
        return False, f"Account deletion failed: {e}"
    finally:
        if conn:
            conn.close()
