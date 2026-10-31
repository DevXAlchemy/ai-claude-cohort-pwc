import sqlite3

import pytest

from tests.test_validation import ae, pqc
from tracker import db


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "t.db"
    db.init_db(p)
    return p


def test_create_report_valid(path):
    ref = db.create_report(ae(), path)
    assert ref.startswith("PSI-")
    [r] = db.list_reports(path)
    assert r["reference"] == ref and r["status"] == "New"


def test_references_unique(path):
    assert db.create_report(pqc(), path) != db.create_report(pqc(), path)


def test_invalid_report_not_saved(path):
    bad = pqc()
    bad["product_name"] = ""
    with pytest.raises(db.ValidationError) as e:
        db.create_report(bad, path)
    assert "product_name" in e.value.errors
    assert db.list_reports(path) == [] and db.list_audit(path) == []


def test_status_workflow(path):
    ref = db.create_report(pqc(), path)
    db.change_status(ref, "In Review", path)
    db.change_status(ref, "Closed", path)
    assert db.list_reports(path)[0]["status"] == "Closed"


@pytest.mark.parametrize("target", ["Closed", "New", "Bogus"])
def test_invalid_transitions_from_new(path, target):
    ref = db.create_report(pqc(), path)
    with pytest.raises(db.InvalidTransition):
        db.change_status(ref, target, path)


def test_closed_is_terminal_and_unknown_ref(path):
    ref = db.create_report(pqc(), path)
    db.change_status(ref, "In Review", path)
    db.change_status(ref, "Closed", path)
    with pytest.raises(db.InvalidTransition):
        db.change_status(ref, "In Review", path)
    with pytest.raises(db.InvalidTransition):
        db.change_status("PSI-NOPE", "In Review", path)


def test_audit_records_and_no_free_text(path):
    data = ae()
    ref = db.create_report(data, path)
    db.change_status(ref, "In Review", path)
    audit = db.list_audit(path)
    assert [(a["action"], a["old_status"], a["new_status"]) for a in reversed(audit)] == [
        ("CREATED", None, "New"), ("STATUS_CHANGED", "New", "In Review")]
    blob = str(audit)
    assert data["description"] not in blob and data["event_description"] not in blob
    assert set(audit[0]) == {"id", "timestamp", "reference", "action", "old_status", "new_status"}


def test_create_rolls_back_when_audit_fails(path, monkeypatch):
    def boom(*a, **k):
        raise sqlite3.OperationalError("audit failed")
    monkeypatch.setattr(db, "_audit", boom)
    with pytest.raises(sqlite3.Error):
        db.create_report(pqc(), path)
    monkeypatch.undo()
    assert db.list_reports(path) == [] and db.list_audit(path) == []


def test_status_change_rolls_back_when_audit_fails(path, monkeypatch):
    ref = db.create_report(pqc(), path)
    def boom(*a, **k):
        raise sqlite3.OperationalError("audit failed")
    monkeypatch.setattr(db, "_audit", boom)
    with pytest.raises(sqlite3.Error):
        db.change_status(ref, "In Review", path)
    monkeypatch.undo()
    assert db.list_reports(path)[0]["status"] == "New"
    assert len(db.list_audit(path)) == 1


def test_pqc_stores_no_ae_fields(path):
    db.create_report(pqc(), path)
    r = db.list_reports(path)[0]
    assert r["event_description"] is None and r["event_onset_date"] is None


def test_reference_format_and_sequence(path):
    import re
    first, second = db.create_report(pqc(), path), db.create_report(pqc(), path)
    assert re.fullmatch(r"PSI-\d{8}-\d{4}", first)
    assert first.endswith("-0001") and second.endswith("-0002")


def test_audit_closed_transition(path):
    ref = db.create_report(pqc(), path)
    db.change_status(ref, "In Review", path)
    db.change_status(ref, "Closed", path)
    seq = [(a["action"], a["old_status"], a["new_status"]) for a in reversed(db.list_audit(path))]
    assert seq == [("CREATED", None, "New"), ("STATUS_CHANGED", "New", "In Review"),
                   ("STATUS_CHANGED", "In Review", "Closed")]


def test_stale_status_change_writes_no_extra_audit_row(path, monkeypatch):
    ref = db.create_report(pqc(), path)
    db.change_status(ref, "In Review", path)
    # Simulate a second session that read the status as "New" before the first change.
    real = db._connect
    def stale(p):
        conn = real(p)
        class Proxy:
            def __init__(s): s.c = conn
            def execute(s, sql, params=()):
                if sql.startswith("SELECT status"):
                    class R:  # stale read
                        def __getitem__(self, k): return "New"
                    class Cur:
                        def fetchone(self): return R()
                    return Cur()
                return s.c.execute(sql, params)
            def __enter__(s): s.c.__enter__(); return s
            def __exit__(s, *a): return s.c.__exit__(*a)
            def close(s): s.c.close()
        return Proxy()
    monkeypatch.setattr(db, "_connect", stale)
    with pytest.raises(db.InvalidTransition):
        db.change_status(ref, "In Review", path)
    monkeypatch.undo()
    assert len(db.list_audit(path)) == 2
    assert db.list_reports(path)[0]["status"] == "In Review"
