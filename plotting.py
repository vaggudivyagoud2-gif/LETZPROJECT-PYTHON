from pathlib import Path
from .analytics import Analytics

def create_charts(records, out_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Matplotlib is not installed. Run: pip install matplotlib") from exc
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    monthly = Analytics.monthly(records)
    if not monthly: raise ValueError("Add or import records before plotting.")
    labels = [m["month"] for m in monthly]; totals = [m["total"] for m in monthly]
    fig, ax = plt.subplots(figsize=(10, 5)); ax.plot(labels, totals, marker="o", linewidth=2.5)
    ax.set_title("Monthly Rainfall Trend", fontsize=16, weight="bold"); ax.set_xlabel("Month"); ax.set_ylabel("Rainfall (mm)")
    ax.grid(True, alpha=.25); fig.autofmt_xdate(); fig.tight_layout()
    trend = out / "monthly_rainfall_trend.png"; fig.savefig(trend, dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5)); ax.bar(labels, totals)
    ax.set_title("Monthly Rainfall Distribution", fontsize=16, weight="bold"); ax.set_xlabel("Month"); ax.set_ylabel("Total rainfall (mm)")
    ax.grid(axis="y", alpha=.25); fig.autofmt_xdate(); fig.tight_layout()
    dist = out / "monthly_rainfall_distribution.png"; fig.savefig(dist, dpi=180); plt.close(fig)
    return [trend, dist]
