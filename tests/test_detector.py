import pandas as pd
import pytest
 
from detector import LIMITS, detect_anomalies, violation_column
from telemetry import CHANNELS
 
 
def make_row(**overrides):
    """One in-range sample, with optional per-channel overrides."""
    row = {
        "timestamp": pd.Timestamp("2026-01-01"),
        "battery_voltage": 28.0,
        "temperature_c": 25.0,
        "angular_rate_dps": 0.0,
        "signal_strength_db": -80.0,
    }
    row.update(overrides)
    return row
 
 
def check(*rows, **kwargs):
    return detect_anomalies(pd.DataFrame(rows), **kwargs)
 
 
def test_nominal_sample_has_no_alerts():
    result = check(make_row())
    assert not result["is_anomaly"].any()
    assert result["alerts"].iloc[0] == ""
 
 
@pytest.mark.parametrize("channel", CHANNELS)
def test_low_and_high_violations_are_flagged(channel):
    low, high = LIMITS[channel]
    result = check(make_row(**{channel: low - 0.01}), make_row(**{channel: high + 0.01}))
    assert result["is_anomaly"].all()
    assert result[violation_column(channel)].all()
 
 
@pytest.mark.parametrize("channel", CHANNELS)
def test_limits_are_inclusive(channel):
    low, high = LIMITS[channel]
    result = check(make_row(**{channel: low}), make_row(**{channel: high}))
    assert not result["is_anomaly"].any()
 
 
def test_violation_flag_is_per_channel():
    result = check(make_row(temperature_c=95.0))
    assert result[violation_column("temperature_c")].iloc[0]
    for channel in CHANNELS:
        if channel != "temperature_c":
            assert not result[violation_column(channel)].iloc[0]
 
 
def test_multiple_violations_are_joined_without_trailing_separator():
    result = check(make_row(temperature_c=95.0, battery_voltage=10.0))
    alerts = result["alerts"].iloc[0]
    assert "Temperature outside limits" in alerts
    assert "Battery voltage outside limits" in alerts
    assert "; " in alerts
    assert not alerts.endswith(";") and not alerts.endswith("; ")
 
 
def test_input_is_not_mutated():
    df = pd.DataFrame([make_row(temperature_c=95.0)])
    before = df.copy()
    detect_anomalies(df)
    pd.testing.assert_frame_equal(df, before)
 
 
def test_custom_limits_override_defaults():
    result = check(make_row(temperature_c=25.0), limits={"temperature_c": (0.0, 20.0)})
    assert result["is_anomaly"].iloc[0]
    # Channels not in the custom limits are not checked.
    assert violation_column("battery_voltage") not in result.columns
 
 
def test_invalid_limits_raise():
    with pytest.raises(ValueError):
        check(make_row(), limits={"temperature_c": (10.0, 0.0)})
 
 
def test_nan_is_not_flagged():
    result = check(make_row(temperature_c=float("nan")))
    assert not result["is_anomaly"].iloc[0]
 
 
def test_empty_dataframe():
    empty = pd.DataFrame({c: [] for c in ["timestamp", *CHANNELS]})
    result = detect_anomalies(empty)
    assert result.empty
    assert "is_anomaly" in result.columns