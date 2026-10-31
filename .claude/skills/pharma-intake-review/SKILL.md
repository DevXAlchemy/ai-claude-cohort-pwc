---
name: pharma-intake-review
description: Use when reviewing the Pharma Safety Intake Tracker's intake forms, report validation, status transitions or audit records. Review-only checklist covering data minimisation, required fields, fictional data, error handling, auditability and tests. Makes no clinical or regulatory judgements.
---

# Pharma intake review

Review the project against this checklist. **Do not edit files**: return prioritised
findings (High / Medium / Low) with file references and suggested tests.

## Hard boundary
Never assess causality, recommend treatment, determine reportability/seriousness, or
make any clinical or regulatory decision. Flag any code, text or UI that does so.

## Checklist
1. **Data minimisation** - No reporter names/contact details, patient identifiers or
   unnecessary personal data in the form, DB schema or audit log.
2. **Required fields** - All common fields mandatory (type, product, batch/lot, date
   received, reporter type, description); AE adds event description and onset date.
   Enforced server-side (tracker/validation.py), not only in the UI.
3. **Fictional data** - Visible fictional-data notice; seed/test/sample data synthetic;
   no real product or commercially sensitive data.
4. **Validation** - Messages are field-specific and actionable; whitespace-only input
   rejected; invalid dates and enum values handled.
5. **Error handling** - Save/status failures caught, user-friendly message, no partial
   writes (single transaction), no stack traces or report content leaked to the UI.
6. **Status workflow** - Only New → In Review → Closed; no skips, reversals or edits
   after Closed; all changes go through one function; changes visible in the UI.
7. **Auditability** - Creation and every status change recorded with reference,
   action, old/new status, timestamp; audit rows written in the same transaction;
   no free-text report content; audit log not editable via the UI.
8. **Tests** - Cover required fields per type, valid creation, valid/invalid
   transitions, audit contents. List requirements that are untested.

## Output format
- Findings table: priority, checklist item, file:line, issue, suggested fix.
- Suggested tests (names + what they assert).
- Passed / failed / untested summary, plus any boundary violations.
