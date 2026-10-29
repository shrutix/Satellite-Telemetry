"""UI tests for the guided runner, using Streamlit's AppTest.
 
Each script below runs the section against simulated telemetry for one
scenario, the same way app.py will.
"""
 
import pytest
 
pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  ## noqa: E402
 
 
def _thermal_script():
    from detector import detect_anomalies
    from response_ui import render_guided_response
    from telemetry import CHANNELS, generate_telemetry
 
    render_guided_response(detect_anomalies(generate_telemetry("Thermal rise")), CHANNELS)
 
 
def _normal_script():
    from detector import detect_anomalies
    from response_ui import render_guided_response
    from telemetry import CHANNELS, generate_telemetry
 
    render_guided_response(detect_anomalies(generate_telemetry("Normal")), CHANNELS)
 
 
def button(at, label):
    matches = [b for b in at.button if b.label == label]
    assert matches, f"no button labelled {label!r}; found {[b.label for b in at.button]}"
    return matches[0]
 
 
def start_incident(at, operator="Alex"):
    at.text_input(key="operator_name").set_value(operator).run()
    button(at, "Start incident").click().run()
    return at
 
 
def test_no_alerts_means_no_procedure_to_run():
    at = AppTest.from_function(_normal_script, default_timeout=30).run()
    assert not at.exception
    assert any("no procedure to run" in i.value for i in at.info)
    assert not [b for b in at.button if b.label == "Start incident"]
 
 
def test_alert_offers_a_matching_procedure():
    at = AppTest.from_function(_thermal_script, default_timeout=30).run()
    assert not at.exception
    assert "SOP-002" in at.selectbox(key="procedure_choice").options
 
 
def test_starting_requires_an_operator_name():
    at = AppTest.from_function(_thermal_script, default_timeout=30).run()
    button(at, "Start incident").click().run()
    assert "operator" in at.error[0].value.lower()
    assert "incident_log" not in at.session_state
 
 
def test_start_incident_creates_a_log():
    at = start_incident(AppTest.from_function(_thermal_script, default_timeout=30).run())
    assert not at.exception
    log = at.session_state["incident_log"]
    assert log.procedure.id == "SOP-002" and log.operator == "Alex"
    assert "simulated time" in log.entries[0].note  # trigger text recorded
 
 
def test_marking_a_step_done_advances_the_incident():
    at = start_incident(AppTest.from_function(_thermal_script, default_timeout=30).run())
    button(at, "Mark step done").click().run()
    log = at.session_state["incident_log"]
    assert log.progress[0] == 1 and log.next_step == 2
 
 
def test_skip_without_a_reason_shows_an_error_and_does_not_advance():
    at = start_incident(AppTest.from_function(_thermal_script, default_timeout=30).run())
    button(at, "Skip step").click().run()
    assert "reason" in at.error[0].value.lower()
    assert at.session_state["incident_log"].progress[0] == 0
 
 
def test_cannot_close_as_resolved_with_steps_remaining():
    at = start_incident(AppTest.from_function(_thermal_script, default_timeout=30).run())
    button(at, "Close incident").click().run()
    assert at.error and not at.session_state["incident_log"].is_closed
 
 
def test_discard_returns_to_the_start_screen():
    at = start_incident(AppTest.from_function(_thermal_script, default_timeout=30).run())
    button(at, "Discard and start a new incident").click().run()
    assert "incident_log" not in at.session_state
    assert any(b.label == "Start incident" for b in at.button)