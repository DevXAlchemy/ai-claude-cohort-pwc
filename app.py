"""Pharma Safety Intake Tracker - training prototype (fictional data only). UI only."""
import sqlite3
from datetime import date

import streamlit as st

from tracker import db
from tracker.models import AE, ALLOWED_TRANSITIONS, REPORT_TYPES, REPORTER_TYPES, required_fields

st.set_page_config(page_title="Pharma Safety Intake Tracker", layout="wide")
db.init_db()

st.title("Pharma Safety Intake Tracker")
st.warning(
    "Training prototype - fictional data only. Do not enter real patient identifiers or "
    "contact details. This tool makes no clinical or regulatory decisions."
)

tab_intake, tab_reports, tab_audit = st.tabs(["New report", "Reports", "Audit log"])

with tab_intake:
    # Report type sits outside the form so the AE-only fields appear immediately.
    report_type = st.radio("Report type *", REPORT_TYPES, horizontal=True)
    required = required_fields(report_type)
    st.caption("Mandatory: " + ", ".join(required.values()) + ".")

    with st.form("intake", clear_on_submit=False):
        product_name = st.text_input("Product name *")
        batch_lot = st.text_input("Batch/lot number *")
        date_received = st.date_input("Date received *", value=date.today())
        reporter_type = st.selectbox("Reporter type *", [""] + REPORTER_TYPES)
        description = st.text_area("Short description *")
        event_description, onset_date = None, None
        if report_type == AE:
            event_description = st.text_area("Event description *")
            has_onset = st.checkbox("Event onset date known / entered *")
            onset_date = st.date_input("Event onset date *", value=date.today())
            if not has_onset:
                onset_date = None
        submitted = st.form_submit_button("Submit report")

    if submitted:
        data = {
            "report_type": report_type,
            "product_name": product_name,
            "batch_lot": batch_lot,
            "date_received": date_received,
            "reporter_type": reporter_type,
            "description": description,
            "event_description": event_description,
            "event_onset_date": onset_date,
        }
        try:
            ref = db.create_report(data)
            st.success(f"Report saved. Reference: {ref} (status: New)")
        except db.ValidationError as e:
            st.error("Report not saved. Please fix the following:")
            for message in e.errors.values():
                st.markdown(f"- {message}")
        except sqlite3.Error:
            st.error("The report could not be saved due to a storage error. Nothing was saved; please try again.")

with tab_reports:
    reports = db.list_reports()
    if not reports:
        st.info("No reports yet.")
    for r in reports:
        cols = st.columns([2, 3, 3, 2, 2, 2])
        cols[0].write(f"**{r['reference']}**")
        cols[1].write(r["report_type"])
        cols[2].write(r["product_name"])
        cols[3].write(r["date_received"])
        cols[4].write(f"**{r['status']}**")
        next_status = ALLOWED_TRANSITIONS.get(r["status"])
        if next_status:
            if cols[5].button(f"Move to {next_status}", key=f"mv-{r['reference']}"):
                try:
                    db.change_status(r["reference"], next_status)
                    st.rerun()
                except db.InvalidTransition as e:
                    st.error(str(e))
                except sqlite3.Error:
                    st.error("The status could not be changed due to a storage error. Nothing was changed.")
        else:
            cols[5].write("Final")

with tab_audit:
    audit = db.list_audit()
    if audit:
        st.dataframe(audit, width="stretch")
    else:
        st.info("No audit records yet.")
