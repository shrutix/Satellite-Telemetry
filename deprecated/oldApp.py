
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Satellite Telemetry Monitor",
    page_icon="🛰️",
    layout="wide",
)

# Illustrative simulation limits, NOT real spacecraft limits.
LIMITS = {
    "battery_voltage": (24.0, 32.0),
    "temperature_c": (-10.0, 60.0),
    "angular_rate_dps": (-2.0, 2.0),
    "signal_strength_db": (-110.0, -50.0),
}


def generate_telemetry(
    scenario="Normal",
    samples=600,
    seed=42,
):
    """Generate deterministic, simulated telemetry."""
    rng = np.random.default_rng(seed)

    df = pd.DataFrame({
        "timestamp": pd.date_range(
            "2026-01-01", periods=samples, freq="10s"
        ),
        "battery_voltage": (
            28.0 + rng.normal(0, 0.12, samples)
        ),
        "temperature_c": (
            25.0 + rng.normal(0, 0.35, samples)
        ),
        "angular_rate_dps": (
            rng.normal(0, 0.08, samples)
        ),
        "signal_strength_db": (
            -80.0 + rng.normal(0, 1.0, samples)
        ),
    })

    # Inject known faults for testing the detector.
    start = samples // 2

    if scenario == "Battery voltage drop":
        df.loc[start:, "battery_voltage"] -= np.linspace(
            0, 5, samples - start
        )

    elif scenario == "Thermal rise":
        df.loc[start:, "temperature_c"] += np.linspace(
            0, 45, samples - start
        )

    elif scenario == "Excessive angular rate":
        df.loc[start:, "angular_rate_dps"] += 3.5

    elif scenario == "Sensor spike":
        df.loc[start, "temperature_c"] = 95.0

    return df


def detect_anomalies(df):
    """Apply transparent, rule-based detection."""
    result = df.copy()
    result["alerts"] = ""

    rules = {
        "battery_voltage": (
            "Battery voltage outside limits",
            *LIMITS["battery_voltage"],
        ),
        "temperature_c": (
            "Temperature outside limits",
            *LIMITS["temperature_c"],
        ),
        "angular_rate_dps": (
            "Angular rate outside limits",
            *LIMITS["angular_rate_dps"],
        ),
        "signal_strength_db": (
            "Signal strength outside limits",
            *LIMITS["signal_strength_db"],
        ),
    }

    for column, (message, low, high) in rules.items():
        bad = (result[column] < low) | (result[column] > high)
        result.loc[bad, "alerts"] = (
            result.loc[bad, "alerts"] + message + "; "
        )

    result["is_anomaly"] = result["alerts"].ne("")
    return result


st.title("🛰️ Satellite Telemetry Monitor")
st.caption(
    "Simulated spacecraft health monitoring | "
    "Portfolio prototype — not flight software"
)

scenario = st.selectbox(
    "Select simulation scenario",
    [
        "Normal",
        "Battery voltage drop",
        "Thermal rise",
        "Excessive angular rate",
        "Sensor spike",
    ],
)

df = generate_telemetry(scenario)
df = detect_anomalies(df)

alert_count = int(df["is_anomaly"].sum())
latest = df.iloc[-1]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Battery voltage", f"{latest['battery_voltage']:.2f} V")
c2.metric("Temperature", f"{latest['temperature_c']:.1f} °C")
c3.metric("Angular rate", f"{latest['angular_rate_dps']:.2f} °/s")
c4.metric("Anomalous samples", alert_count)

if alert_count:
    st.warning(
        f"{alert_count} telemetry samples violated "
        "at least one configured limit."
    )
else:
    st.success("No configured limit violations detected.")

st.subheader("Telemetry time series")

parameter = st.selectbox(
    "Telemetry channel",
    [
        "battery_voltage",
        "temperature_c",
        "angular_rate_dps",
        "signal_strength_db",
    ],
)

fig = px.line(
    df,
    x="timestamp",
    y=parameter,
    title=parameter.replace("_", " ").title(),
    labels={"timestamp": "Time", parameter: parameter},
)

# Mark detected anomalous readings.
anomalies = df[df["is_anomaly"]]
if not anomalies.empty:
    fig.add_scatter(
        x=anomalies["timestamp"],
        y=anomalies[parameter],
        mode="markers",
        name="Anomalous sample",
        marker={"color": "red", "size": 8},
    )

st.plotly_chart(fig, use_container_width=True)

st.subheader("Alert log")

alerts = df[df["is_anomaly"]][
    ["timestamp", "battery_voltage", "temperature_c",
     "angular_rate_dps", "signal_strength_db", "alerts"]
]

if alerts.empty:
    st.info("No alerts to display.")
else:
    st.dataframe(alerts, use_container_width=True)

st.download_button(
    "Download telemetry CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="simulated_telemetry.csv",
    mime="text/csv",
)
