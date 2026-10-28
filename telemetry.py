"""Deterministic simulated spacecraft telemetry (not real flight data)."""
 
import numpy as np
import pandas as pd
 
CHANNELS = [
    "battery_voltage",
    "temperature_c",
    "angular_rate_dps",
    "signal_strength_db",
]
 
SCENARIOS = [
    "Normal",
    "Battery voltage drop",
    "Thermal rise",
    "Excessive angular rate",
    "Weak signal",
    "Sensor spike",
]
 
 
def generate_telemetry(scenario="Normal", samples=600, seed=42):
    """Generate deterministic, simulated telemetry.
 
    Faults are injected from the midpoint of the series onward
    (or at a single sample for "Sensor spike").
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario!r}")
    if samples < 2:
        raise ValueError("samples must be at least 2")
 
    rng = np.random.default_rng(seed)
 
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=samples, freq="10s"),
        "battery_voltage": 28.0 + rng.normal(0, 0.12, samples),
        "temperature_c": 25.0 + rng.normal(0, 0.35, samples),
        "angular_rate_dps": rng.normal(0, 0.08, samples),
        "signal_strength_db": -80.0 + rng.normal(0, 1.0, samples),
    })
 
    start = samples // 2
    n_fault = samples - start
 
    if scenario == "Battery voltage drop":
        df.loc[start:, "battery_voltage"] -= np.linspace(0, 5, n_fault)
    elif scenario == "Thermal rise":
        df.loc[start:, "temperature_c"] += np.linspace(0, 45, n_fault)
    elif scenario == "Excessive angular rate":
        df.loc[start:, "angular_rate_dps"] += 3.5
    elif scenario == "Weak signal":
        df.loc[start:, "signal_strength_db"] -= np.linspace(0, 40, n_fault)
    elif scenario == "Sensor spike":
        df.loc[start, "temperature_c"] = 95.0
 
    return df