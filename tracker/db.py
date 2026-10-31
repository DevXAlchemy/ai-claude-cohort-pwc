"""SQLite persistence. Every write and its audit row share one transaction."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from .models import ALLOWED_TRANSITIONS, AE, NEW
from .validation import validate_report

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    reference TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    product_name TEXT NOT NULL,
    batch_lot TEXT NOT NULL,
    date_received TEXT NOT NULL,
    reporter_type TEXT NOT NULL,
    description TEXT NOT NULL,
    event_description TEXT,
    event_onset_date TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    reference TEXT NOT NULL,
    action TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT
);
"""


class ValidationError(Exception):
    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


class InvalidTransition(Exception):
    pass


def _connect(db_path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DEFAULT_DB) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db_path)) as conn, conn:
        conn.executescript(SCHEMA)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _audit(conn, reference, action, old_status, new_status) -> None:
    conn.execute(
        "INSERT INTO audit_log (timestamp, reference, action, old_status, new_status)"
        " VALUES (?, ?, ?, ?, ?)",
        (_now(), reference, action, old_status, new_status),
    )


def create_report(data: dict, db_path=DEFAULT_DB) -> str:
    """Validate and save a report; returns its generated reference.

    Raises ValidationError (nothing saved) or sqlite3.Error (transaction rolled back).
    """
    errors = validate_report(data)
    if errors:
        raise ValidationError(errors)

    is_ae = data["report_type"] == AE
    with closing(_connect(db_path)) as conn, conn:
        prefix = f"PSI-{datetime.now():%Y%m%d}-"
        count = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE reference LIKE ?", (prefix + "%",)
        ).fetchone()[0]
        reference = f"{prefix}{count + 1:04d}"
        conn.execute(
            "INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                reference,
                data["report_type"],
                data["product_name"].strip(),
                data["batch_lot"].strip(),
                data["date_received"].isoformat(),
                data["reporter_type"],
                data["description"].strip(),
                data["event_description"].strip() if is_ae else None,
                data["event_onset_date"].isoformat() if is_ae else None,
                NEW,
                _now(),
            ),
        )
        _audit(conn, reference, "CREATED", None, NEW)
    return reference


def list_reports(db_path=DEFAULT_DB) -> list[dict]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC, reference DESC")
        return [dict(r) for r in rows]


def change_status(reference: str, new_status: str, db_path=DEFAULT_DB) -> None:
    """Move a report one step forward (New → In Review → Closed)."""
    with closing(_connect(db_path)) as conn, conn:
        row = conn.execute("SELECT status FROM reports WHERE reference = ?", (reference,)).fetchone()
        if row is None:
            raise InvalidTransition(f"Report {reference} does not exist.")
        old = row["status"]
        if ALLOWED_TRANSITIONS.get(old) != new_status:
            raise InvalidTransition(f"Cannot change status from '{old}' to '{new_status}'.")
        # Conditional update: if another session already changed the status, do nothing.
        cur = conn.execute(
            "UPDATE reports SET status = ? WHERE reference = ? AND status = ?",
            (new_status, reference, old),
        )
        if cur.rowcount != 1:
            raise InvalidTransition(f"Report {reference} was changed by someone else; please refresh.")
        _audit(conn, reference, "STATUS_CHANGED", old, new_status)


def list_audit(db_path=DEFAULT_DB) -> list[dict]:
    with closing(_connect(db_path)) as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM audit_log ORDER BY id DESC")]
