import logging
import os
from app.database import get_connection

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "system_errors.log")

# Structured Error Logging Setup (Q09 Target Feature)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] Module:%(name)s Line:%(lineno)d - %(message)s",
)
logger = logging.getLogger("InventoryApp")

def log_system_error(module_name: str, error_message: str):
    """Writes error stack to file logger."""
    logger.error(f"[{module_name}] {error_message}")

def log_bug_to_db(module_name: str, defect_type: str, severity: int, description: str):
    """Inserts defect directly into Q09 Bug Tracker table."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bug_reports (module_name, defect_type, severity, description, status)
            VALUES (?, ?, ?, ?, 'Open')
            """,
            (module_name, defect_type, severity, description),
        )
        conn.commit()
    except Exception as e:
        log_system_error("BugTracker", f"Failed to log bug in DB: {e}")
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def get_all_bugs():
    """Fetches all reported bugs for the Bug Tracker UI."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT bug_id, module_name, defect_type, severity, description, status, logged_at FROM bug_reports ORDER BY bug_id DESC")
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        log_system_error("BugTracker", f"Fetch bugs failed: {e}")
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def update_bug_status(bug_id: int, new_status: str):
    """Updates bug resolution status ('Open', 'In-Progress', 'Resolved')."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bug_reports SET status = ? WHERE bug_id = ?", (new_status, bug_id))
        conn.commit()
        return True, f"Bug #{bug_id} status updated to '{new_status}'."
    except Exception as e:
        log_system_error("BugTracker", f"Update bug status failed: {e}")
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def delete_bug(bug_id: int):
    """Deletes a defect record by ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bug_reports WHERE bug_id = ?", (bug_id,))
        conn.commit()
        return True, f"Bug #{bug_id} deleted."
    except Exception as e:
        log_system_error("BugTracker", f"Delete bug failed: {e}")
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def clear_resolved_bugs():
    """Removes all bugs with status 'Resolved'."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bug_reports WHERE status = 'Resolved'")
        conn.commit()
        return True, "Resolved bugs cleared."
    except Exception as e:
        log_system_error("BugTracker", f"Clear resolved failed: {e}")
        return False, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

def get_bug_statistics():
    """Computes defect counts and resolution metrics for the Q09 tracker."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bugs,
                COALESCE(SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END), 0) as open_bugs,
                COALESCE(SUM(CASE WHEN status = 'In-Progress' THEN 1 ELSE 0 END), 0) as in_progress_bugs,
                COALESCE(SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END), 0) as resolved_bugs
            FROM bug_reports
        """)
        row = cursor.fetchone()
        return {
            "total_bugs": row[0] or 0,
            "open_bugs": row[1] or 0,
            "in_progress_bugs": row[2] or 0,
            "resolved_bugs": row[3] or 0
        }
    except Exception as e:
        log_system_error("BugTracker", f"Bug statistics calculation failed: {e}")
        return {
            "total_bugs": 0,
            "open_bugs": 0,
            "in_progress_bugs": 0,
            "resolved_bugs": 0
        }
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
