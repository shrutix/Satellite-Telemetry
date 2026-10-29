"""Streamlit UI for running an SOP against the current telemetry.
 
All rules live in ``incident.IncidentLog``. This module only draws the
controls and passes the operator's clicks through to it.
"""
 
import pandas as pd
import streamlit as st
 
from detector import violation_column
from incident import OUTCOMES, IncidentError, IncidentLog
from sop import ProcedureError, for_channel, load_all
 
LOG_KEY = "incident_log"
FLASH_KEY = "incident_flash_error"
 
STATUS_ICONS = {"done": "✅", "skipped": "⏭️", "current": "👉", "pending": "⬜"}
 
 
def _first_violation_text(df, channel):
    """Describe the first out-of-limit sample on a channel, for the log."""
    bad = df[df[violation_column(channel)]]
    if bad.empty:
        return ""
    row = bad.iloc[0]
    return f"{channel} = {row[channel]:.2f} at {row['timestamp']} (simulated time)"
 
 
def _run(action, *args):
    """Run a log action from a button callback, keeping any error to show later."""
    try:
        action(*args)
    except IncidentError as exc:
        st.session_state[FLASH_KEY] = str(exc)
 
 
def _start(procedure, trigger):
    name = st.session_state.get("operator_name", "")
    try:
        st.session_state[LOG_KEY] = IncidentLog(procedure, name, trigger)
    except IncidentError as exc:
        st.session_state[FLASH_KEY] = str(exc)
 
 
def _discard():
    st.session_state.pop(LOG_KEY, None)
 
 
def _complete(log, step):
    _run(log.complete_step, step, st.session_state.get(f"note_{step}", ""))
 
 
def _skip(log, step):
    _run(log.skip_step, step, st.session_state.get(f"note_{step}", ""))
 
 
def _note(log, step):
    _run(log.add_note, st.session_state.get(f"note_{step}", ""))
 
 
def _escalate(log):
    _run(log.escalate, st.session_state.get("escalation_note", ""))
 
 
def _close(log):
    _run(log.close, st.session_state.get("close_outcome", OUTCOMES[0]), st.session_state.get("close_note", ""))
 
 
def render_guided_response(df, channels):
    """Draw the guided-response section for a telemetry DataFrame.
 
    ``df`` must already have been through ``detect_anomalies``.
    """
    st.subheader("Guided response")
    st.caption("Work through the matching procedure step by step. Every action is time-stamped.")
 
    flash = st.session_state.pop(FLASH_KEY, None)
    if flash:
        st.error(flash)
 
    try:
        procedures = load_all()
    except (FileNotFoundError, ProcedureError) as exc:
        st.error(f"Could not load procedures: {exc}")
        return
 
    log = st.session_state.get(LOG_KEY)
    if log is None:
        _render_start(df, channels, procedures)
    else:
        _render_incident(log)
 
 
def _render_start(df, channels, procedures):
    in_alert = [c for c in channels if df[violation_column(c)].any()]
    if not in_alert:
        st.info("No channels are out of limits, so there is no procedure to run.")
        return
 
    options = [p for c in in_alert for p in for_channel(procedures, c)]
    if not options:
        st.warning("No procedure covers the channels in alert: " + ", ".join(in_alert))
        return
 
    by_id = {p.id: p for p in options}
    chosen = st.selectbox(
        "Procedure to run",
        list(by_id),
        format_func=lambda i: f"{i}: {by_id[i].title} ({by_id[i].severity})",
        key="procedure_choice",
    )
    procedure = by_id[chosen]
    st.text_input("Operator name", key="operator_name")
    st.button(
        "Start incident",
        on_click=_start,
        args=(procedure, _first_violation_text(df, procedure.channel)),
    )
 
 
def _render_incident(log):
    procedure = log.procedure
    done, total = log.progress
    state = "CLOSED: " + log.outcome if log.is_closed else "OPEN"
    st.markdown(f"**{procedure.id}: {procedure.title}**  \n"
                f"Severity: {procedure.severity} | Escalate to: {procedure.escalate_to} | {state}")
    st.progress(done / total, text=f"{done} of {total} steps handled")
 
    if procedure.prerequisites:
        with st.expander("Prerequisites"):
            for item in procedure.prerequisites:
                st.markdown(f"- {item}")
 
    for n, text in enumerate(procedure.steps, start=1):
        st.markdown(f"{STATUS_ICONS[log.step_status(n)]} **{n}.** {text}")
 
    if not log.is_closed:
        current = log.next_step
        if current is not None:
            st.text_input(
                f"Note for step {current} (required to skip)",
                key=f"note_{current}",
            )
            c1, c2, c3 = st.columns(3)
            c1.button("Mark step done", on_click=_complete, args=(log, current))
            c2.button("Skip step", on_click=_skip, args=(log, current))
            c3.button("Log note only", on_click=_note, args=(log, current))
        else:
            st.success("Every step is handled. Check the exit criteria, then close the incident.")
 
        st.text_input("Escalation note (optional)", key="escalation_note")
        st.button(f"Escalate to {procedure.escalate_to}", on_click=_escalate, args=(log,))
 
        st.markdown("**Exit criteria**")
        for item in procedure.exit_criteria:
            st.markdown(f"- {item}")
 
        st.selectbox("Close as", OUTCOMES, key="close_outcome")
        st.text_input("Closing note (optional)", key="close_note")
        st.button("Close incident", on_click=_close, args=(log,))
    else:
        st.success(f"Incident closed as {log.outcome}.")
 
    st.markdown("**Incident log**")
    st.dataframe(pd.DataFrame(log.to_rows()), width="stretch", hide_index=True)
 
    d1, d2 = st.columns(2)
    d1.download_button(
        "Download log (CSV)",
        data=log.to_csv().encode("utf-8"),
        file_name=f"{procedure.id}_incident_log.csv",
        mime="text/csv",
    )
    d2.download_button(
        "Download report (Markdown)",
        data=log.to_markdown().encode("utf-8"),
        file_name=f"{procedure.id}_incident_report.md",
        mime="text/markdown",
    )
 
    st.button("Discard and start a new incident", on_click=_discard)