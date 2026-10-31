"""Constants for report types, statuses and the allowed status workflow."""

AE = "Suspected Adverse Event"
PQC = "Product Quality Complaint"
REPORT_TYPES = [AE, PQC]

REPORTER_TYPES = ["Consumer", "Healthcare professional", "Other"]

NEW = "New"
IN_REVIEW = "In Review"
CLOSED = "Closed"
STATUSES = [NEW, IN_REVIEW, CLOSED]

# Only one forward step is allowed; Closed is terminal.
ALLOWED_TRANSITIONS = {NEW: IN_REVIEW, IN_REVIEW: CLOSED}

COMMON_REQUIRED = {
    "report_type": "Report type",
    "product_name": "Product name",
    "batch_lot": "Batch/lot number",
    "date_received": "Date received",
    "reporter_type": "Reporter type",
    "description": "Description",
}
AE_REQUIRED = {
    "event_description": "Event description",
    "event_onset_date": "Event onset date",
}


def required_fields(report_type: str | None) -> dict[str, str]:
    """Mandatory fields (key -> label) for the given report type."""
    fields = dict(COMMON_REQUIRED)
    if report_type == AE:
        fields.update(AE_REQUIRED)
    return fields
