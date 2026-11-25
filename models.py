from dataclasses import dataclass, asdict
from datetime import date
from typing import Any
import uuid

CATEGORIES = ("Normal", "Heavy", "Extreme", "Light", "Trace")

@dataclass
class RainfallRecord:
    record_id: str
    date: str
    location: str
    rainfall_mm: float
    category: str = "Normal"
    notes: str = ""
    status: str = "Valid"

    @classmethod
    def create(cls, date_value: str, location: str, rainfall_mm: float,
               category: str = "Normal", notes: str = "") -> "RainfallRecord":
        return cls(uuid.uuid4().hex[:10].upper(), date_value, location.strip(),
                   round(float(rainfall_mm), 2), category, notes.strip(), "Valid")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RainfallRecord":
        return cls(record_id=str(data.get("record_id") or uuid.uuid4().hex[:10].upper()),
                   date=str(data["date"]), location=str(data["location"]),
                   rainfall_mm=float(data["rainfall_mm"]),
                   category=str(data.get("category", "Normal")),
                   notes=str(data.get("notes", "")), status=str(data.get("status", "Valid")))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_record(date_value: str, location: str, rainfall: Any,
                    category: str = "Normal") -> tuple[bool, str, float | None]:
    try:
        date.fromisoformat(date_value.strip())
    except (ValueError, AttributeError):
        return False, "Date must use YYYY-MM-DD and be a real calendar date.", None
    if not location or not location.strip():
        return False, "Location cannot be blank.", None
    try:
        value = float(rainfall)
    except (TypeError, ValueError):
        return False, "Rainfall must be a numeric value.", None
    if value < 0:
        return False, "Rainfall cannot be negative.", None
    if value > 2000:
        return False, "Rainfall exceeds the safety limit of 2,000 mm per record.", None
    if category not in CATEGORIES:
        return False, f"Category must be one of: {', '.join(CATEGORIES)}.", None
    return True, "Valid", round(value, 2)
