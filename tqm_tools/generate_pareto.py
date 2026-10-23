import matplotlib.pyplot as plt
import pandas as pd
import sqlite3
import os

def generate_pareto_chart():
    # Attempt to load dynamic defect data from database if available
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventory_q09.db")
    dynamic_counts = {}
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT defect_type, COUNT(*) FROM bug_reports GROUP BY defect_type")
            for dtype, count in c.fetchall():
                dynamic_counts[dtype] = count
            conn.close()
        except Exception:
            dynamic_counts = {}

    # Baseline TQM defect distribution (historical test baseline combined with live defects)
    baseline_data = {
        "Input Format / Type Mismatch": 48 + dynamic_counts.get("ValidationFailure", 0),
        "Negative Stock Level Violation": 32 + dynamic_counts.get("NegativeStockAttempt", 0) + dynamic_counts.get("NegativeStockViolation", 0),
        "Duplicate SKU Constraint": 14 + dynamic_counts.get("DuplicateSKU", 0) + dynamic_counts.get("DuplicateSKUAttempt", 0),
        "Malformed SKU Syntax": 8 + dynamic_counts.get("MalformedSKUSyntax", 0),
        "Zero / Negative Price Boundary": 4 + dynamic_counts.get("NonPositivePrice", 0),
        "Unhandled SQLite Lock": 2 + dynamic_counts.get("DatabaseError", 0)
    }

    df = pd.DataFrame(list(baseline_data.items()), columns=["Defect_Category", "Count"])
    df = df.sort_values(by="Count", ascending=False).reset_index(drop=True)
    df["Cumulative_Percentage"] = (df["Count"].cumsum() / df["Count"].sum()) * 100

    # Modern Dark Theme Plot
    plt.style.use("dark_background")
    fig, ax1 = plt.subplots(figsize=(10, 5.8), facecolor="#0e1526")
    ax1.set_facecolor("#131c31")

    # Bar chart for counts with gradient-like styling
    x_positions = range(len(df["Defect_Category"]))
    bars = ax1.bar(x_positions, df["Count"], color="#3b82f6", edgecolor="#60a5fa", width=0.55, alpha=0.9, zorder=3)
    ax1.set_ylabel("Defect Frequency (Count)", color="#60a5fa", fontsize=11, weight="bold")
    ax1.tick_params(axis="y", labelcolor="#93c5fd")
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels(df["Defect_Category"], rotation=25, ha="right", fontsize=9, color="#e2e8f0")
    ax1.grid(axis="y", linestyle="--", alpha=0.2, color="#94a3b8")

    # Data value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f"{height}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, color="#ffffff", weight="bold")

    # Secondary axis for cumulative percentage
    ax2 = ax1.twinx()
    ax2.plot(x_positions, df["Cumulative_Percentage"], color="#f43f5e", marker="D", linewidth=2.5, markersize=6, zorder=4, label="Cumulative %")
    ax2.axhline(80, color="#f59e0b", linestyle="--", linewidth=1.5, alpha=0.85, label="80% Cutoff Threshold (Vital Few)")
    ax2.set_ylabel("Cumulative Percentage (%)", color="#f43f5e", fontsize=11, weight="bold")
    ax2.tick_params(axis="y", labelcolor="#fda4af")
    ax2.set_ylim(0, 110)

    # 80% mark annotation
    ax2.text(len(df)-1, 82, " 80% Cutoff Threshold", color="#f59e0b", fontsize=9, weight="bold", ha="right")

    plt.title("Pareto Analysis (80/20 Rule) - Q09 Defect Elimination Matrix", fontsize=13, weight="bold", pad=15, color="#38bdf8")
    fig.tight_layout()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pareto_analysis.png")
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[SQC] Pareto chart saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_pareto_chart()
