"""Pure validation of a report dict. Returns field -> message; empty means valid."""
from datetime import date

from .models import REPORT_TYPES, REPORTER_TYPES, required_fields

DATE_FIELDS = ("date_received", "event_onset_date")


def validate_report(data: dict, today: date | None = None) -> dict[str, str]:
    today = today or date.today()
    errors: dict[str, str] = {}

    for key, label in required_fields(data.get("report_type")).items():
        value = data.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors[key] = f"{label} is required."
        elif key in DATE_FIELDS:
            if not isinstance(value, date):
                errors[key] = f"{label} must be a valid date."
        elif not isinstance(value, str):
            errors[key] = f"{label} must be text."

    if "report_type" not in errors and data["report_type"] not in REPORT_TYPES:
        errors["report_type"] = "Report type must be one of: " + ", ".join(REPORT_TYPES) + "."
    if "reporter_type" not in errors and data["reporter_type"] not in REPORTER_TYPES:
        errors["reporter_type"] = "Reporter type must be one of: " + ", ".join(REPORTER_TYPES) + "."

    for key, label in (("date_received", "Date received"), ("event_onset_date", "Event onset date")):
        value = data.get(key)
        if key not in errors and isinstance(value, date) and value > today:
            errors[key] = f"{label} cannot be in the future."
    return errors
