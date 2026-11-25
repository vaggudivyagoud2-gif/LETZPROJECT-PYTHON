import csv, json
from pathlib import Path
from .models import RainfallRecord

FIELDS = ["record_id", "date", "location", "rainfall_mm", "category", "notes", "status"]

class Storage:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.data_dir / "rainfall.json"
        self.csv_path = self.data_dir / "rainfall.csv"
        self.audit_path = self.data_dir / "audit.log"

    def load(self) -> list[RainfallRecord]:
        if self.json_path.exists():
            try:
                raw = json.loads(self.json_path.read_text(encoding="utf-8"))
                if not isinstance(raw, list): raise ValueError("JSON root must be a list")
                return [RainfallRecord.from_dict(item) for item in raw]
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError) as exc:
                self.audit(f"RECOVERY: Could not load JSON ({exc}); trying CSV/template.")
        if self.csv_path.exists():
            try:
                with self.csv_path.open(newline="", encoding="utf-8-sig") as f:
                    return [RainfallRecord.from_dict(row) for row in csv.DictReader(f)]
            except (OSError, ValueError, KeyError, TypeError) as exc:
                self.audit(f"RECOVERY: Could not load CSV ({exc}); starting empty.")
        return []

    def save(self, records: list[RainfallRecord]) -> None:
        payload = [r.to_dict() for r in records]
        temp = self.json_path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(self.json_path)
        with self.csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader(); writer.writerows(payload)

    def audit(self, message: str) -> None:
        from datetime import datetime
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} | {message}\n")

    def import_csv(self, path: str | Path) -> tuple[list[RainfallRecord], list[str]]:
        imported, errors = [], []
        with Path(path).open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"date", "location", "rainfall_mm"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError("CSV must include date, location, rainfall_mm columns")
            for line, row in enumerate(reader, start=2):
                from .models import validate_record
                category = (row.get("category") or "Normal").strip() or "Normal"
                ok, message, amount = validate_record(row.get("date", ""), row.get("location", ""), row.get("rainfall_mm", ""), category)
                if not ok:
                    errors.append(f"Row {line}: {message}"); continue
                imported.append(RainfallRecord.create(row["date"], row["location"], amount, category, row.get("notes", "")))
        return imported, errors
