"""Transparent, rule-based limit checking for simulated telemetry."""
 
import pandas as pd
 
# Illustrative simulation limits, NOT real spacecraft limits.
LIMITS = {
    "battery_voltage": (24.0, 32.0),
    "temperature_c": (-10.0, 60.0),
    "angular_rate_dps": (-2.0, 2.0),
    "signal_strength_db": (-110.0, -50.0),
}
 
MESSAGES = {
    "battery_voltage": "Battery voltage outside limits",
    "temperature_c": "Temperature outside limits",
    "angular_rate_dps": "Angular rate outside limits",
    "signal_strength_db": "Signal strength outside limits",
}
 
 
def violation_column(channel):
    """Name of the per-channel boolean column added by detect_anomalies."""
    return f"{channel}_violation"
 
 
def detect_anomalies(df, limits=None):
    """Flag samples that fall outside configured limits.
 
    Returns a copy of ``df`` with:
      - ``<channel>_violation``: bool, True where that channel is out of limits
      - ``alerts``: "; "-joined messages for the row ("" if none)
      - ``is_anomaly``: bool, True if any channel is out of limits
 
    Limits are inclusive: a value exactly equal to a bound is in range.
    NaN values are not flagged (comparisons with NaN are False).
    """
    limits = LIMITS if limits is None else limits
    result = df.copy()
 
    row_messages = []
    for channel, (low, high) in limits.items():
        if low > high:
            raise ValueError(f"Invalid limits for {channel}: {low} > {high}")
        bad = (result[channel] < low) | (result[channel] > high)
        result[violation_column(channel)] = bad
        message = MESSAGES.get(channel, f"{channel} outside limits")
        row_messages.append(bad.map({True: message, False: ""}))
 
    if row_messages:
        result["alerts"] = [
            "; ".join(m for m in row if m) for row in zip(*row_messages)
        ]
    else:
        result["alerts"] = ""
    result["is_anomaly"] = result["alerts"].ne("")
    return result