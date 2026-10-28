"""Smoke tests: the Streamlit app runs end to end for every scenario."""
 
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
 
from telemetry import CHANNELS, SCENARIOS
 
APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")

def run_app():
    return AppTest.from_file(APP_PATH, default_timeout=30).run()
 
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_app_runs_without_exception(scenario):
    at = run_app()
    at.selectbox[0].select(scenario).run()
    assert not at.exception
 
 
def test_every_channel_renders():
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    for channel in CHANNELS:
        at.selectbox[1].select(channel).run()
        assert not at.exception
 
 
def test_normal_shows_success_and_fault_shows_warning():
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert len(at.success) == 1 and len(at.warning) == 0
    at.selectbox[0].select("Thermal rise").run()
    assert len(at.warning) == 1
 