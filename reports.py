import csv
from pathlib import Path
from .analytics import Analytics

class Reports:
    @staticmethod
    def export(records, out_dir):
        out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
        summary = Analytics.summary(records); monthly = Analytics.monthly(records); alerts = Analytics.alerts(records)
        md = ["# Rainfall Data Explorer — Executive Summary", "", f"Generated records: **{summary['count']}**", "",
              "## Key indicators", "", f"- Total rainfall: **{summary['total']:.2f} mm**", f"- Average per record: **{summary['average']:.2f} mm**",
              f"- Median: **{summary['median']:.2f} mm**", f"- Maximum: **{summary['maximum']:.2f} mm**", f"- Minimum: **{summary['minimum']:.2f} mm**",
              f"- Dry records: **{summary['dry_days']}**", f"- Wettest observation: **{summary['wettest_day']}**", "", "## Monthly rainfall", "", "| Month | Total (mm) | Average (mm) | Records |", "|---|---:|---:|---:|"]
        md += [f"| {m['month']} | {m['total']:.2f} | {m['average']:.2f} | {m['records']} |" for m in monthly]
        md += ["", "## Threshold and data-age alerts", ""] + ([f"- {a}" for a in alerts] or ["- No alerts generated."])
        (out / "executive_summary.md").write_text("\n".join(md), encoding="utf-8")
        txt = "RAINFALL DATA EXPLORER — EXECUTIVE SUMMARY\n" + "="*48 + "\n" + "\n".join(f"{k.replace('_',' ').title()}: {v}" for k,v in summary.items()) + "\n\nALERTS\n" + ("\n".join(alerts) if alerts else "No alerts.")
        (out / "executive_summary.txt").write_text(txt, encoding="utf-8")
        if records:
            with (out / "rainfall_report.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(records[0].to_dict().keys())); w.writeheader(); w.writerows(r.to_dict() for r in records)
        return [out / "executive_summary.md", out / "executive_summary.txt", out / "rainfall_report.csv"]
