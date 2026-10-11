import matplotlib.pyplot as plt
import pandas as pd
import os

def generate_pareto_chart():
    # Defect categories derived from Q09 bug tracker data
    data = {
        "Defect_Category": [
            "Input Format / Type Mismatch",
            "Negative Stock Level Violation",
            "Duplicate SKU Constraint",
            "Malformed SKU Syntax",
            "Zero / Negative Price Boundary",
            "Unhandled SQLite Lock"
        ],
        "Count": [48, 32, 14, 8, 4, 2]
    }

    df = pd.DataFrame(data)
    df = df.sort_values(by="Count", ascending=False).reset_index(drop=True)
    df["Cumulative_Percentage"] = (df["Count"].cumsum() / df["Count"].sum()) * 100

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Bar chart for counts
    bars = ax1.bar(df["Defect_Category"], df["Count"], color="#2b5c8f", edgecolor="black", width=0.6)
    ax1.set_ylabel("Defect Frequency (Count)", color="#2b5c8f", fontsize=12, weight="bold")
    ax1.tick_params(axis="y", labelcolor="#2b5c8f")
    ax1.set_xticklabels(df["Defect_Category"], rotation=30, ha="right", fontsize=10)

    # Secondary axis for cumulative percentage
    ax2 = ax1.twinx()
    ax2.plot(df["Defect_Category"], df["Cumulative_Percentage"], color="#d9534f", marker="D", linewidth=2.5, markersize=7)
    ax2.axhline(80, color="gray", linestyle="--", linewidth=1.2, label="80% Cutoff Threshold")
    ax2.set_ylabel("Cumulative Percentage (%)", color="#d9534f", fontsize=12, weight="bold")
    ax2.tick_params(axis="y", labelcolor="#d9534f")
    ax2.set_ylim(0, 110)

    plt.title("Pareto Analysis (80/20 Rule) - Q09 Software Defect Elimination", fontsize=14, weight="bold", pad=15)
    fig.tight_layout()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pareto_analysis.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[SQC] Pareto chart saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_pareto_chart()