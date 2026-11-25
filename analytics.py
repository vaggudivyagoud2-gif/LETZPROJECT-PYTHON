from collections import defaultdict
from statistics import mean, median
from datetime import date, timedelta

class Analytics:
    @staticmethod
    def summary(records):
        if not records:
            return {"count": 0, "total": 0.0, "average": 0.0, "median": 0.0, "maximum": 0.0, "minimum": 0.0, "wettest_day": "—", "dry_days": 0}
        vals = [r.rainfall_mm for r in records]
        wet = max(records, key=lambda r: r.rainfall_mm)
        return {"count": len(records), "total": round(sum(vals), 2), "average": round(mean(vals), 2),
                "median": round(median(vals), 2), "maximum": max(vals), "minimum": min(vals),
                "wettest_day": f"{wet.date} · {wet.location}", "dry_days": sum(v == 0 for v in vals)}

    @staticmethod
    def monthly(records):
        buckets = defaultdict(list)
        for r in records: buckets[r.date[:7]].append(r.rainfall_mm)
        return [{"month": k, "total": round(sum(v), 2), "average": round(mean(v), 2), "records": len(v)} for k, v in sorted(buckets.items())]

    @staticmethod
    def by_location(records):
        buckets = defaultdict(list)
        for r in records: buckets[r.location].append(r.rainfall_mm)
        return [{"location": k, "total": round(sum(v), 2), "average": round(mean(v), 2), "records": len(v)} for k, v in sorted(buckets.items())]

    @staticmethod
    def alerts(records, daily_limit=150.0, stale_days=30):
        alerts = []
        for r in records:
            if r.rainfall_mm >= daily_limit:
                alerts.append(f"HIGH RAINFALL · {r.date} · {r.location}: {r.rainfall_mm:.1f} mm (limit {daily_limit:.1f} mm)")
        if records:
            latest = max(date.fromisoformat(r.date) for r in records)
            cutoff = latest - timedelta(days=stale_days)
            for r in records:
                if date.fromisoformat(r.date) < cutoff:
                    alerts.append(f"OLDER RECORD · {r.date} · {r.location}: outside the latest {stale_days}-day window")
        return alerts

    @staticmethod
    def search(records, keyword="", category="All", location="All"):
        q = keyword.casefold().strip()
        return [r for r in records if (not q or q in " ".join([r.record_id, r.date, r.location, r.notes]).casefold())
                and (category == "All" or r.category == category)
                and (location == "All" or r.location == location)]
