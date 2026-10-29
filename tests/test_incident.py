import csv
import io
from datetime import datetime, timedelta, timezone
 
import pytest
 
from incident import OUTCOMES, IncidentError, IncidentLog
from sop import load_all, parse_procedure
from sop import PROCEDURES_DIR, load_procedure, parse_procedure
 
SOP_TEXT = """---
id: SOP-077
title: Test procedure
channel: temperature_c
severity: High
escalate_to: Thermal engineer
---
 
## Steps
1. First step.
2. Second step.
3. Third step.
 
## Exit criteria
- Back in limits
"""
 
 
@pytest.fixture
def procedure():
    return parse_procedure(SOP_TEXT)
 
 
@pytest.fixture
def clock():
    """A fake clock that advances one minute each time it is read."""
    state = {"now": datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)}
 
    def tick():
        value = state["now"]
        state["now"] += timedelta(minutes=1)
        return value
 
    return tick
 
 
@pytest.fixture
def log(procedure, clock):
    return IncidentLog(procedure, "Alex", trigger="temperature_c = 61.00", clock=clock)
 
 
def finish_all_steps(log):
    for n in range(1, len(log.procedure.steps) + 1):
        log.complete_step(n)
 
 
# --- opening an incident ---
 
def test_new_incident_logs_a_started_entry(log):
    (entry,) = log.entries
    assert entry.event == "started"
    assert "SOP-077" in entry.detail
    assert entry.note == "temperature_c = 61.00"
    assert entry.operator == "Alex"
 
 
@pytest.mark.parametrize("name", ["", "   ", None])
def test_operator_name_is_required(procedure, name):
    with pytest.raises(IncidentError, match="operator"):
        IncidentLog(procedure, name)
 
 
def test_operator_name_is_trimmed(procedure):
    assert IncidentLog(procedure, "  Alex  ").operator == "Alex"
 
 
def test_default_clock_gives_timezone_aware_utc_timestamps(procedure):
    entry = IncidentLog(procedure, "Alex").entries[0]
    assert entry.timestamp.utcoffset() == timedelta(0)
 
 
def test_entries_cannot_be_modified_from_outside(log):
    assert isinstance(log.entries, tuple)
 
 
# --- steps ---
 
def test_steps_must_be_handled_in_order(log):
    with pytest.raises(IncidentError, match="Step 1 must be handled next"):
        log.complete_step(2)
 
 
def test_a_step_cannot_be_completed_twice(log):
    log.complete_step(1)
    with pytest.raises(IncidentError, match="Step 2 must be handled next"):
        log.complete_step(1)
 
 
def test_completing_a_step_logs_its_text_and_note(log):
    log.complete_step(1, note="  reading confirmed  ")
    entry = log.entries[-1]
    assert (entry.event, entry.step) == ("step_done", 1)
    assert entry.detail == "First step."
    assert entry.note == "reading confirmed"
 
 
def test_cannot_act_past_the_last_step(log):
    finish_all_steps(log)
    assert log.next_step is None
    with pytest.raises(IncidentError, match="already been handled"):
        log.complete_step(4)
 
 
def test_skipping_requires_a_reason(log):
    for reason in ("", "   ", None):
        with pytest.raises(IncidentError, match="reason"):
            log.skip_step(1, reason)
    assert log.next_step == 1  # nothing was recorded
 
 
def test_skipped_step_is_logged_and_counts_as_handled(log):
    log.skip_step(1, "Not applicable in this scenario")
    entry = log.entries[-1]
    assert (entry.event, entry.note) == ("step_skipped", "Not applicable in this scenario")
    assert log.next_step == 2
    assert log.progress == (1, 3)
 
 
def test_step_status_values(log):
    log.complete_step(1)
    log.skip_step(2, "reason")
    assert [log.step_status(n) for n in (1, 2, 3)] == ["done", "skipped", "current"]
    log.escalate()
    log.close("handed_over")
    assert log.step_status(3) == "pending"  # never reached
 
 
def test_step_status_rejects_unknown_step(log):
    with pytest.raises(IncidentError):
        log.step_status(0)
    with pytest.raises(IncidentError):
        log.step_status(4)
 
 
# --- notes and escalation ---
 
def test_add_note_logs_text_and_rejects_blank(log):
    log.add_note("Ground station reports clear weather")
    assert log.entries[-1].event == "note"
    assert log.entries[-1].note == "Ground station reports clear weather"
    with pytest.raises(IncidentError, match="empty"):
        log.add_note("  ")
 
 
def test_escalation_records_the_contact(log):
    log.escalate("Temperature still rising")
    entry = log.entries[-1]
    assert (entry.event, entry.detail) == ("escalated", "Thermal engineer")
    assert entry.note == "Temperature still rising"
    assert log.escalated
 
 
# --- closing ---
def test_cannot_resolve_with_steps_remaining(log):
    log.complete_step(1)
    with pytest.raises(IncidentError, match="every step"):
        log.close("resolved")
    assert not log.is_closed
 
 
def test_resolve_after_all_steps(log):
    finish_all_steps(log)
    log.close("resolved", note="Back in limits")
    assert log.is_closed and log.outcome == "resolved"
    assert log.entries[-1].event == "closed"
 
 
def test_resolve_after_skipping_the_remaining_steps(log):
    log.complete_step(1)
    log.skip_step(2, "Not applicable")
    log.skip_step(3, "Not applicable")
    log.close("resolved")
    assert log.is_closed
 
 
def test_handover_requires_escalation_first(log):
    with pytest.raises(IncidentError, match="Escalate"):
        log.close("handed_over")
    log.escalate()
    log.close("handed_over")  # allowed with steps still pending
    assert log.outcome == "handed_over"
 
 
def test_invalid_outcome_is_rejected(log):
    with pytest.raises(IncidentError, match="Outcome"):
        log.close("abandoned")
 
 
def test_nothing_can_be_added_after_closing(log):
    log.escalate()
    log.close("handed_over")
    with pytest.raises(IncidentError, match="closed"):
        log.complete_step(1)
    with pytest.raises(IncidentError, match="closed"):
        log.add_note("late note")
    with pytest.raises(IncidentError, match="closed"):
        log.escalate()
    with pytest.raises(IncidentError, match="closed"):
        log.close("handed_over")
 
 
def test_a_rejected_action_does_not_change_the_log(log):
    before = log.entries
    with pytest.raises(IncidentError):
        log.complete_step(3)
    assert log.entries == before
 
 
# --- time and export --------------------------------------------------------------
 
def test_timestamps_are_recorded_in_order(log):
    finish_all_steps(log)
    stamps = [e.timestamp for e in log.entries]
    assert stamps == sorted(stamps) and len(set(stamps)) == len(stamps)
 
 
def test_csv_has_one_row_per_entry_and_a_header(log):
    finish_all_steps(log)
    rows = list(csv.DictReader(io.StringIO(log.to_csv())))
    assert len(rows) == len(log.entries) == 4
    assert list(rows[0]) == ["timestamp", "incident", "operator", "event", "step", "detail", "note"]
    assert rows[1]["event"] == "step_done" and rows[1]["step"] == "1"
    assert rows[0]["step"] == ""
    assert rows[0]["incident"] == "SOP-077"
 
 
def test_csv_preserves_commas_quotes_and_newlines(log):
    nasty = 'Reading, "61.2 C"\nsecond line'
    log.add_note(nasty)
    rows = list(csv.DictReader(io.StringIO(log.to_csv())))
    assert rows[-1]["note"] == nasty
 
 
def test_markdown_report_contents(log):
    log.complete_step(1, note="confirmed")
    log.escalate()
    log.close("handed_over", note="Engineer in control")
    report = log.to_markdown()
    assert report.startswith("# Incident report: SOP-077")
    assert "Simulated" in report
    assert "**Status:** handed_over" in report
    assert "**Steps handled:** 1 of 3" in report
    assert "step done 1: First step. (note: confirmed)" in report
    assert "2026-01-01 12:00:00 UTC" in report
 
 
def test_markdown_report_for_an_open_incident(log):
    assert "**Status:** open" in log.to_markdown()
 
 
# --- real procedures ---

SOP_FILES = sorted(
    p for p in PROCEDURES_DIR.glob("*.md") if not p.name.startswith("_")
)


@pytest.mark.parametrize("path", SOP_FILES, ids=lambda p: p.name)
def test_every_shipped_procedure_can_be_run_to_resolution(path):
    procedure = load_procedure(path)
    log = IncidentLog(procedure, "Test Operator")
    finish_all_steps(log)
    log.close("resolved")
    assert log.progress == (len(procedure.steps),) * 2
    assert len(list(csv.DictReader(io.StringIO(log.to_csv())))) == len(procedure.steps) + 2
 
#@pytest.mark.parametrize("sop_id", sorted(load_all()))
#def test_every_shipped_procedure_can_be_run_to_resolution(sop_id):
#    procedure = load_all()[sop_id]
#    log = IncidentLog(procedure, "Test Operator")
#    finish_all_steps(log)
#    log.close("resolved")
#    assert log.progress == (len(procedure.steps),) * 2
#    assert len(list(csv.DictReader(io.StringIO(log.to_csv())))) == len(procedure.steps) + 2
 
 
def test_outcomes_constant_matches_what_close_accepts(log):
    log.escalate()
    finish_all_steps(log)
    for outcome in OUTCOMES:
        fresh = IncidentLog(log.procedure, "Alex")
        fresh.escalate()
        finish_all_steps(fresh)
        fresh.close(outcome)
        assert fresh.outcome == outcome