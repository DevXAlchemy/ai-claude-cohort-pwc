from datetime import date, timedelta

import pytest

from tracker.models import AE, PQC
from tracker.validation import validate_report


def pqc():
    return {
        "report_type": PQC, "product_name": "Examplol 10 mg", "batch_lot": "LOT-TEST-001",
        "date_received": date.today(), "reporter_type": "Consumer", "description": "Fictional tablet colour issue",
    }


def ae():
    return {**pqc(), "report_type": AE, "event_description": "Fictional mild headache",
            "event_onset_date": date.today()}


def test_valid_reports_have_no_errors():
    assert validate_report(pqc()) == {}
    assert validate_report(ae()) == {}


@pytest.mark.parametrize("field", ["product_name", "batch_lot", "date_received", "reporter_type", "description"])
def test_common_required_fields(field):
    data = pqc()
    data[field] = "  " if isinstance(data[field], str) else None
    assert field in validate_report(data)


@pytest.mark.parametrize("field", ["event_description", "event_onset_date"])
def test_ae_only_required_fields(field):
    data = ae()
    data[field] = None
    assert field in validate_report(data)
    # The same fields are not required for a quality complaint.
    assert validate_report(pqc()) == {}


def test_future_dates_rejected():
    data = ae()
    data["date_received"] = date.today() + timedelta(days=1)
    data["event_onset_date"] = date.today() + timedelta(days=1)
    errors = validate_report(data)
    assert "future" in errors["date_received"] and "future" in errors["event_onset_date"]


def test_messages_are_helpful():
    assert validate_report({})["product_name"] == "Product name is required."


def test_invalid_enum_values_rejected():
    data = pqc()
    data["report_type"] = "Bogus"
    assert "report_type" in validate_report(data)
    data = pqc()
    data["reporter_type"] = "Bogus"
    assert "reporter_type" in validate_report(data)


@pytest.mark.parametrize("field", ["date_received", "event_onset_date"])
def test_non_date_values_rejected(field):
    data = ae()
    data[field] = "2026-01-01"
    assert "valid date" in validate_report(data)[field]


def test_non_string_text_rejected():
    data = pqc()
    data["product_name"] = 123
    assert "product_name" in validate_report(data)
