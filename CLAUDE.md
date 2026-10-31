# Pharma Safety Intake Tracker (training prototype)

## Purpose
Local prototype that captures fictional product quality complaints and suspected
adverse event reports, validates required fields, tracks review status
(New → In Review → Closed) and keeps a local audit trail.

## Scope boundaries (hard rules)
- This is NOT a pharmacovigilance decision system. It must NOT make clinical or
  regulatory decisions: no causality assessment, no treatment advice, no
  reportability determination, no seriousness/severity classification.
- Fictional/synthetic data only. No real patient names, identifiers, contact
  details, medical records or commercially sensitive product data. Collect no
  reporter personal details.
- Audit records store reference, action, old/new status and timestamp only, never
  free-text report content.
- Ask before adding dependencies, new features or expanding scope. Keep v1 small.

## Structure
app.py (Streamlit UI only) · tracker/models.py (constants, allowed transitions) ·
tracker/validation.py (pure validation) · tracker/db.py (SQLite + audit) ·
tests/ · data/ (local DB, gitignored) · logs/ (dev audit log from hook)

## Conventions
- Python 3, type hints, small functions; no business logic in app.py.
- Validation and status rules live in tracker/, are enforced server-side, and
  return clear field-specific messages.
- Status changes only via db.change_status; invalid transitions raise an error.
- Writes and their audit rows share one transaction.

## Commands
- Run: .venv/bin/streamlit run app.py
- Test: .venv/bin/python -m pytest

## Tests
- Cover required fields per report type, valid creation, status transitions
  (valid and invalid), and audit rows containing no free text. Write a failing
  test before fixing a validation bug. Run tests after each increment.

## Where other guidance lives
Detailed review checklists → .claude/skills/pharma-intake-review. Deterministic
actions (edit logging) → hooks in .claude/settings.json.
