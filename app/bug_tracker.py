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
        conn.close()
    except Exception as e:
        log_system_error("BugTracker", f"Failed to log bug in DB: {e}")

def get_all_bugs():
    """Fetches all reported bugs for the Bug Tracker UI."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bug_id, module_name, defect_type, severity, description, status, logged_at FROM bug_reports ORDER BY bug_id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_bug_status(bug_id: int, new_status: str):
    """Updates bug resolution status."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bug_reports SET status = ? WHERE bug_id = ?", (new_status, bug_id))
    conn.commit()
    conn.close()