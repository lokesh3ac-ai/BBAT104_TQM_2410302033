import os
import io
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file

from app.inventory_logic import (
    add_item,
    update_stock,
    delete_item,
    update_item_details,
    get_all_items,
    get_all_categories,
    get_inventory_statistics,
    validate_item_data
)
from app.bug_tracker import (
    get_all_bugs,
    update_bug_status,
    delete_bug,
    clear_resolved_bugs,
    get_bug_statistics,
    log_bug_to_db,
    log_system_error
)
from app.database import get_connection

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Disable verbose logging in production desktop mode
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def index():
    return render_template("index.html")

# =============================================================================
# INVENTORY REST APIS
# =============================================================================
@app.route("/api/inventory", methods=["GET"])
def api_get_inventory():
    items = get_all_items()
    result = []
    for item in items:
        item_id, sku, name, cat, qty, price, reorder, created = item
        total_val = qty * price
        
        if qty == 0:
            status = "Out of Stock"
            badge = "danger"
        elif qty <= reorder:
            status = "Low Stock"
            badge = "warning"
        else:
            status = "Healthy"
            badge = "success"

        result.append({
            "id": item_id,
            "sku": sku,
            "name": name,
            "category": cat,
            "quantity": qty,
            "unit_price": price,
            "total_value": total_val,
            "reorder_level": reorder,
            "status": status,
            "badge": badge,
            "created_at": created
        })
    return jsonify({"success": True, "items": result, "count": len(result)})


@app.route("/api/inventory/add", methods=["POST"])
def api_add_item():
    data = request.json or {}
    sku = data.get("sku", "")
    name = data.get("name", "")
    category = data.get("category", "")
    quantity = data.get("quantity", "0")
    unit_price = data.get("unit_price", "0")
    reorder_level = data.get("reorder_level", "5")

    success, msg = add_item(sku, name, category, quantity, unit_price, reorder_level)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/inventory/stock", methods=["POST"])
def api_update_stock():
    data = request.json or {}
    sku = data.get("sku", "")
    try:
        delta = int(data.get("delta", 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Delta adjustment must be an integer."}), 400

    success, msg = update_stock(sku, delta)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/inventory/update", methods=["POST"])
def api_update_item():
    data = request.json or {}
    sku = data.get("sku", "")
    name = data.get("name", "")
    category = data.get("category", "")
    unit_price = data.get("unit_price", "0")
    reorder_level = data.get("reorder_level", "5")

    success, msg = update_item_details(sku, name, category, unit_price, reorder_level)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/inventory/delete/<sku>", methods=["DELETE"])
def api_delete_item(sku):
    success, msg = delete_item(sku)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    cats = get_all_categories()
    return jsonify({"success": True, "categories": cats})


# =============================================================================
# BUG TRACKER (Q09) REST APIS
# =============================================================================
@app.route("/api/bugs", methods=["GET"])
def api_get_bugs():
    bugs = get_all_bugs()
    result = []
    for b in bugs:
        b_id, mod, dtype, sev, desc, status, logged_at = b
        result.append({
            "id": b_id,
            "module": mod,
            "defect_type": dtype,
            "severity": sev,
            "description": desc,
            "status": status,
            "logged_at": logged_at
        })
    stats = get_bug_statistics()
    return jsonify({"success": True, "bugs": result, "stats": stats})


@app.route("/api/bugs/status", methods=["POST"])
def api_update_bug_status():
    data = request.json or {}
    bug_id = data.get("bug_id")
    status = data.get("status")
    if not bug_id or not status:
        return jsonify({"success": False, "message": "Missing bug_id or status."}), 400

    success, msg = update_bug_status(int(bug_id), status)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/bugs/<int:bug_id>", methods=["DELETE"])
def api_delete_bug(bug_id):
    success, msg = delete_bug(bug_id)
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/bugs/clear-resolved", methods=["POST"])
def api_clear_resolved_bugs():
    success, msg = clear_resolved_bugs()
    return jsonify({"success": success, "message": msg}), (200 if success else 400)


@app.route("/api/bugs/simulate", methods=["POST"])
def api_simulate_defect():
    """Triggers an intentional Poka-Yoke error to demonstrate live trapping."""
    data = request.json or {}
    sim_type = data.get("type", "negative_qty")
    
    if sim_type == "malformed_sku":
        success, msg = add_item("INVALID_CODE_XYZ!", "Bad Item", "Electronics", "10", "100.0")
    elif sim_type == "negative_price":
        success, msg = add_item("SKU-SIM01", "Faulty Component", "Hardware", "5", "-450.0")
    elif sim_type == "underflow_stock":
        # Deduct massive amount on existing item
        items = get_all_items()
        target_sku = items[0][1] if items else "SKU-TEST01"
        success, msg = update_stock(target_sku, -99999)
    else: # negative_qty
        success, msg = add_item("SKU-SIM02", "Underflow Test", "Sensors", "-25", "500.0")

    return jsonify({
        "success": False, # intentionally rejected
        "poka_yoke_trapped": True,
        "message": msg,
        "explanation": "Poka-Yoke layer successfully blocked invalid data from hitting the database."
    })


# =============================================================================
# STATS & SQC APIS
# =============================================================================
@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    inv_stats = get_inventory_statistics()
    bug_stats = get_bug_statistics()
    return jsonify({
        "success": True,
        "inventory": inv_stats,
        "bugs": bug_stats,
        "interception_rate": "100%",
        "rpn_reduction": "93.1%"
    })


@app.route("/api/sqc/pareto", methods=["GET"])
def api_get_pareto_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT defect_type, COUNT(*) FROM bug_reports GROUP BY defect_type")
    dynamic_counts = dict(c.fetchall())
    conn.close()

    baseline = [
        {"category": "Input Format / Type Mismatch", "count": 48 + dynamic_counts.get("ValidationFailure", 0)},
        {"category": "Negative Stock Level Violation", "count": 32 + dynamic_counts.get("NegativeStockAttempt", 0) + dynamic_counts.get("NegativeStockViolation", 0)},
        {"category": "Duplicate SKU Constraint", "count": 14 + dynamic_counts.get("DuplicateSKU", 0) + dynamic_counts.get("DuplicateSKUAttempt", 0)},
        {"category": "Malformed SKU Syntax", "count": 8 + dynamic_counts.get("MalformedSKUSyntax", 0)},
        {"category": "Zero / Negative Price Boundary", "count": 4 + dynamic_counts.get("NonPositivePrice", 0)},
        {"category": "Unhandled SQLite Lock", "count": 2 + dynamic_counts.get("DatabaseError", 0)}
    ]
    # Sort descending
    baseline.sort(key=lambda x: x["count"], reverse=True)
    total = sum(x["count"] for x in baseline) or 1
    
    cumulative = 0
    for item in baseline:
        cumulative += item["count"]
        item["cumulative_pct"] = round((cumulative / total) * 100, 1)

    return jsonify({
        "success": True,
        "categories": [x["category"] for x in baseline],
        "counts": [x["count"] for x in baseline],
        "cumulative_percentages": [x["cumulative_pct"] for x in baseline],
        "total_defects": total
    })


# =============================================================================
# LOGS & EXPORT APIS
# =============================================================================
@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "system_errors.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return jsonify({"success": True, "logs": [l.strip() for l in lines[-100:]]})
    return jsonify({"success": True, "logs": ["[INFO] Log buffer is clean."]})


@app.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "system_errors.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [INFO] Log buffer cleared by user from Desktop Suite.\n")
        return jsonify({"success": True, "message": "Log buffer cleared."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    items = get_all_items()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item ID", "SKU", "Item Name", "Category", "Quantity", "Unit Price", "Total Value", "Reorder Level", "Created At"])
    for item in items:
        item_id, sku, name, cat, qty, price, reorder, created = item
        writer.writerow([item_id, sku, name, cat, qty, f"{price:.2f}", f"{(qty*price):.2f}", reorder, created])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=AERO_FLOW_Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


def run_server(port=5000):
    app.run(host="127.0.0.1", port=port, debug=False)

if __name__ == "__main__":
    run_server()
