import matplotlib.pyplot as plt
import os

def generate_fishbone_diagram():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Main spine and defect head
    ax.annotate("", xy=(8.5, 5), xytext=(1.0, 5),
                arrowprops=dict(arrowstyle="->", lw=3.5, color="#1a252f"))
    ax.text(8.7, 5, "Problem Statement:\nSoftware Runtime\nBugs & Crashes\n(Q09 Focus)",
            va="center", ha="left", fontsize=11, weight="bold",
            bbox=dict(boxstyle="square,pad=0.5", facecolor="#fadbd8", edgecolor="#e74c3c", lw=2))

    # Major bone branches
    categories = [
        ("People (Staff)", 3.0, 5, 2.0, 8.5),
        ("Process / Testing", 6.0, 5, 5.0, 8.5),
        ("Methods / Validation", 3.0, 5, 4.0, 1.5),
        ("Technology / DB", 6.0, 5, 7.0, 1.5)
    ]

    for label, x_start, y_start, x_end, y_end in categories:
        ax.annotate("", xy=(x_start, y_start), xytext=(x_end, y_end),
                    arrowprops=dict(arrowstyle="-", lw=2.2, color="#2c3e50"))
        ax.text(x_end, y_end + (0.3 if y_end > 5 else -0.5), label,
                ha="center", fontsize=11, weight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#ebf5fb", edgecolor="#2980b9"))

    # Root causes
    causes = [
        ("Typo in SKU input", 2.3, 7.5),
        ("Untrained clerk", 2.7, 6.5),
        ("No unit test coverage", 5.3, 7.5),
        ("Untracked exception stack", 5.7, 6.5),
        ("Missing Poka-Yoke guards", 3.7, 2.5),
        ("No lower-bound verification", 3.3, 3.5),
        ("Unchecked SQLite unique keys", 6.7, 2.5),
        ("Silent unhandled errors", 6.3, 3.5)
    ]

    for cause, x, y in causes:
        ax.text(x, y, f"• {cause}", fontsize=9, color="#34495e")

    plt.title("Ishikawa (Fishbone) Root Cause Diagram - Quality Goal Q09", fontsize=14, weight="bold", pad=20)
    fig.tight_layout()

    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "fishbone_diagram.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[SQC] Fishbone diagram saved successfully to: {output_path}")

if __name__ == "__main__":
    generate_fishbone_diagram()