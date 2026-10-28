import pandas as pd
import pytest
 
from detector import detect_anomalies
from telemetry import CHANNELS, SCENARIOS, generate_telemetry
 
 
def test_shape_and_columns():
    df = generate_telemetry("Normal", samples=100)
    assert len(df) == 100
    assert list(df.columns) == ["timestamp", *CHANNELS]
    assert df["timestamp"].is_monotonic_increasing
 
 
def test_same_seed_is_deterministic():
    a = generate_telemetry("Thermal rise", seed=7)
    b = generate_telemetry("Thermal rise", seed=7)
    pd.testing.assert_frame_equal(a, b)
 
 
def test_different_seed_changes_data():
    a = generate_telemetry("Normal", seed=1)
    b = generate_telemetry("Normal", seed=2)
    assert not a["battery_voltage"].equals(b["battery_voltage"])
 
 
def test_unknown_scenario_raises():
    with pytest.raises(ValueError):
        generate_telemetry("Solar flare")
 
 
def test_too_few_samples_raises():
    with pytest.raises(ValueError):
        generate_telemetry("Normal", samples=1)
 
 
def test_normal_scenario_triggers_no_alerts():
    assert not detect_anomalies(generate_telemetry("Normal"))["is_anomaly"].any()
 
 
# Scenario -> the one channel that should be the only one violating limits.
FAULT_CHANNELS = {
    "Battery voltage drop": "battery_voltage",
    "Thermal rise": "temperature_c",
    "Excessive angular rate": "angular_rate_dps",
    "Weak signal": "signal_strength_db",
    "Sensor spike": "temperature_c",
}
 
 
@pytest.mark.parametrize("scenario,channel", FAULT_CHANNELS.items())
def test_fault_scenarios_trip_only_the_expected_channel(scenario, channel):
    result = detect_anomalies(generate_telemetry(scenario))
    assert result["is_anomaly"].any()
    for other in CHANNELS:
        flagged = result[f"{other}_violation"].any()
        assert flagged == (other == channel), other
 
 
def test_faults_start_in_second_half():
    n = 600
    result = detect_anomalies(generate_telemetry("Battery voltage drop", samples=n))
    first_bad = result.index[result["is_anomaly"]].min()
    assert first_bad >= n // 2
 
 
def test_sensor_spike_is_a_single_sample():
    result = detect_anomalies(generate_telemetry("Sensor spike"))
    assert int(result["is_anomaly"].sum()) == 1
 
 
def test_all_scenarios_are_covered_by_fault_table():
    assert set(SCENARIOS) == {"Normal", *FAULT_CHANNELS}