import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_connection, VALID_ROLES, DEFAULT_ROLE

def validate_password_complexity(password: str) -> tuple[bool, str]:
    """
    Validates strict password complexity:
    - Must contain at least one uppercase letter (A-Z)
    - Must contain at least one numeric digit (0-9)
    - Must contain at least one special character (e.g. @$!%*?&#)
    Returns (True, "") or (False, "Password must include at least one uppercase letter, one number, and one special character.")
    """
    if not password:
        return False, "Password cannot be empty."
    if not re.search(r'[A-Z]', password):
        return False, "Password must include at least one uppercase letter, one number, and one special character."
    if not re.search(r'[0-9]', password):
        return False, "Password must include at least one uppercase letter, one number, and one special character."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must include at least one uppercase letter, one number, and one special character."
    return True, ""


def register_user(username: str, password: str, store_name: str = "", store_owner_name: str = "", role: str = DEFAULT_ROLE, created_by: int = None):
    """
    Registers a new user in the SQLite database with a hashed password and role.
    Returns (True, user_dict) on success, or (False, error_message).
    """
    username = str(username).strip()
    password = str(password).strip()
    store_name = str(store_name).strip()
    store_owner_name = str(store_owner_name).strip()
    role = str(role).strip() if role else DEFAULT_ROLE

    if role not in VALID_ROLES:
        return False, f"Invalid role '{role}'. Allowed roles: {', '.join(VALID_ROLES)}."

    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 13:
        return False, "Username must not exceed 13 characters."

    pw_ok, pw_err = validate_password_complexity(password)
    if not pw_ok:
        return False, pw_err

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
            INSERT INTO users (username, password_hash, store_name, store_owner_name, role, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (username, password_hash, store_name, store_owner_name, role, created_by)
        )
        conn.commit()
        user_id = cursor.lastrowid

        return True, {
            "id": user_id,
            "username": username,
            "store_name": store_name,
            "store_owner_name": store_owner_name,
            "role": role,
            "is_active": 1,
            "created_by": created_by
        }
    except Exception as e:
        return False, f"Failed to register user: {e}"
    finally:
        if conn:
            conn.close()


def authenticate_user(username: str, password: str):
    """
    Authenticates a user by checking the password hash and active status in SQLite.
    Returns (True, user_dict) on success, or (False, error_message).
    """
    username = str(username).strip()
    password = str(password).strip()

    if not username or not password:
        return False, "Please enter both username and password."

    if len(username) > 13:
        return False, "Username must not exceed 13 characters."

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, password_hash, store_name, store_owner_name, role, is_active, created_by, created_at
            FROM users WHERE username = ? COLLATE NOCASE
            """,
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return False, "Invalid username or password."

        u_id, u_name, u_hash, s_name, s_owner, role, is_active, created_by, created_at = row
        if not check_password_hash(u_hash, password):
            return False, "Invalid username or password."

        if is_active == 0:
            return False, "Account has been deactivated. Please contact your Store Administrator."

        return True, {
            "id": u_id,
            "username": u_name,
            "store_name": s_name or "",
            "store_owner_name": s_owner or "",
            "role": role or DEFAULT_ROLE,
            "is_active": is_active,
            "created_by": created_by,
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
            SELECT id, username, store_name, store_owner_name, role, is_active, created_by, created_at
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
            "role": row[4] or DEFAULT_ROLE,
            "is_active": row[5],
            "created_by": row[6],
            "created_at": row[7]
        }
    finally:
        if conn:
            conn.close()


def get_user_profile_by_id(user_id: int):
    """Retrieves profile by user ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, store_name, store_owner_name, role, is_active, created_by, created_at
            FROM users WHERE id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "store_name": row[2] or "",
            "store_owner_name": row[3] or "",
            "role": row[4] or DEFAULT_ROLE,
            "is_active": row[5],
            "created_by": row[6],
            "created_at": row[7]
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


# =============================================================================
# STAFF MANAGEMENT FUNCTIONS (STORE ADMINISTRATOR ROLE ONLY)
# =============================================================================

def create_staff_user(admin_user_id: int, username: str, password: str, role: str):
    """
    Creates a new staff credential linked to the administrator's store.
    Role can be 'Inventory Manager' or 'Billing Cashier'.
    """
    admin_profile = get_user_profile_by_id(admin_user_id)
    if not admin_profile:
        return False, "Store Administrator not found."
    if admin_profile["role"] != "Store Administrator":
        return False, "Only a Store Administrator can create staff credentials."

    if role not in ("Inventory Manager", "Billing Cashier", "Store Administrator"):
        return False, f"Invalid staff role '{role}'."

    return register_user(
        username=username,
        password=password,
        store_name=admin_profile["store_name"],
        store_owner_name=admin_profile["store_owner_name"],
        role=role,
        created_by=admin_user_id
    )


def list_staff_users(admin_user_id: int):
    """Lists all staff accounts created by this administrator."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, role, is_active, created_at
            FROM users
            WHERE created_by = ?
            ORDER BY id DESC
            """,
            (admin_user_id,)
        )
        rows = cursor.fetchall()
        staff = []
        for r in rows:
            staff.append({
                "id": r[0],
                "username": r[1],
                "role": r[2],
                "is_active": bool(r[3]),
                "created_at": r[4]
            })
        return staff
    finally:
        if conn:
            conn.close()


def toggle_staff_status(admin_user_id: int, staff_id: int):
    """Toggles active/deactive status for a staff account created by this admin."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, is_active, username FROM users WHERE id = ? AND created_by = ?", (staff_id, admin_user_id))
        row = cursor.fetchone()
        if not row:
            return False, "Staff account not found or access denied."

        current_active = row[1]
        new_active = 0 if current_active == 1 else 1
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_active, staff_id))
        conn.commit()

        status_label = "activated" if new_active == 1 else "deactivated"
        return True, f"Staff account '{row[2]}' has been {status_label}."
    except Exception as e:
        return False, f"Failed to update staff status: {e}"
    finally:
        if conn:
            conn.close()


def delete_staff_user(admin_user_id: int, staff_id: int):
    """Revokes and permanently deletes a staff account created by this admin."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE id = ? AND created_by = ?", (staff_id, admin_user_id))
        row = cursor.fetchone()
        if not row:
            return False, "Staff account not found or access denied."

        cursor.execute("DELETE FROM users WHERE id = ? AND created_by = ?", (staff_id, admin_user_id))
        conn.commit()
        return True, f"Staff account '{row[1]}' permanently deleted."
    except Exception as e:
        return False, f"Failed to delete staff account: {e}"
    finally:
        if conn:
            conn.close()
