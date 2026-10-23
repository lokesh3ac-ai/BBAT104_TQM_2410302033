import matplotlib.pyplot as plt
import os

def generate_fishbone_diagram():
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 6.8), facecolor="#0e1526")
    ax.set_facecolor("#0e1526")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Main spine and defect head
    ax.annotate("", xy=(8.3, 5), xytext=(0.8, 5),
                arrowprops=dict(arrowstyle="->", lw=3.5, color="#38bdf8"))
    
    # Problem Head Box
    ax.text(8.4, 5, "PROBLEM STATEMENT:\nSoftware Runtime\nDefects & Crashes\n(Q09 Target Goal)",
            va="center", ha="left", fontsize=10, weight="bold", color="#ffffff",
            bbox=dict(boxstyle="square,pad=0.6", facecolor="#881337", edgecolor="#f43f5e", lw=2))

    # Major bone branches (4M/4P Categories)
    categories = [
        ("People (Staff / Users)", 2.8, 5, 1.8, 8.4),
        ("Process & Testing", 5.8, 5, 4.8, 8.4),
        ("Methods (Validation)", 2.8, 5, 3.8, 1.6),
        ("Technology (SQLite / OS)", 5.8, 5, 6.8, 1.6)
    ]

    for label, x_start, y_start, x_end, y_end in categories:
        ax.annotate("", xy=(x_start, y_start), xytext=(x_end, y_end),
                    arrowprops=dict(arrowstyle="-", lw=2.2, color="#60a5fa"))
        ax.text(x_end, y_end + (0.35 if y_end > 5 else -0.55), label,
                ha="center", fontsize=10, weight="bold", color="#ffffff",
                bbox=dict(boxstyle="round,pad=0.35", facecolor="#1e293b", edgecolor="#38bdf8", lw=1.5))

    # Root causes
    causes = [
        ("• Typo in SKU formatting", 2.0, 7.4),
        ("• Untrained clerk data entry", 2.3, 6.5),
        ("• Missing regression unit test suite", 5.0, 7.4),
        ("• Untracked exception stack traces", 5.3, 6.5),
        ("• Absence of Poka-Yoke input guards", 3.4, 2.7),
        ("• Negative quantity underflow ignored", 3.1, 3.6),
        ("• Uncaught SQLite UNIQUE key clashes", 6.3, 2.7),
        ("• Silent unhandled runtime exceptions", 6.0, 3.6)
    ]

    for cause, x, y in causes:
        ax.text(x, y, cause, fontsize=9, color="#cbd5e1", weight="medium")

    plt.title("Ishikawa (Fishbone) Root Cause Diagram - Quality Goal Q09 Defect Prevention", 
              fontsize=13, weight="bold", pad=20, color="#38bdf8")
    fig.tight_layout()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fishbone_diagram.png")
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[SQC] Fishbone diagram saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_fishbone_diagram()
