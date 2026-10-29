import plotly.express as px
import streamlit as st
 
from detector import LIMITS, detect_anomalies, violation_column
from telemetry import CHANNELS, SCENARIOS, generate_telemetry
from response_ui import render_guided_response
 
st.set_page_config(
    page_title="Satellite Telemetry Monitor",
    page_icon="🛰️",
    layout="wide",
)
 
UNITS = {
    "battery_voltage": "V",
    "temperature_c": "°C",
    "angular_rate_dps": "°/s",
    "signal_strength_db": "dB",
}
 
 
@st.cache_data
def load_data(scenario):
    """Generate and check telemetry; cached so widget changes don't recompute."""
    return detect_anomalies(generate_telemetry(scenario))
 
 
st.title("🛰️ Satellite Telemetry Monitor")
st.caption(
    "Simulated spacecraft health monitoring | "
    "Prototype — not flight software"
)
 
scenario = st.selectbox("Select simulation scenario", SCENARIOS)
df = load_data(scenario)
 
alert_count = int(df["is_anomaly"].sum())
 
# Summary cards: latest reading, with a flag if any sample on that channel
# violated its limits (the latest value alone can look normal after a spike).
cols = st.columns(len(CHANNELS) + 1)
for col, channel in zip(cols, CHANNELS):
    n_bad = int(df[violation_column(channel)].sum())
    col.metric(
        channel.replace("_", " ").title(),
        f"{df[channel].iloc[-1]:.2f} {UNITS[channel]}",
        delta=f"{n_bad} violations" if n_bad else None,
        delta_color="inverse",
    )
cols[-1].metric("Anomalous samples", alert_count)
 
if alert_count:
    st.warning(
        f"{alert_count} telemetry samples violated at least one configured limit."
    )
else:
    st.success("No configured limit violations detected.")
 
st.subheader("Telemetry time series")
 
parameter = st.selectbox(
    "Telemetry channel",
    CHANNELS,
    format_func=lambda c: c.replace("_", " ").title(),
)
 
fig = px.line(
    df,
    x="timestamp",
    y=parameter,
    title=parameter.replace("_", " ").title(),
    labels={"timestamp": "Time", parameter: f"{parameter} ({UNITS[parameter]})"},
)
 
low, high = LIMITS[parameter]
fig.add_hline(y=low, line_dash="dash", line_color="orange", annotation_text="low limit")
fig.add_hline(y=high, line_dash="dash", line_color="orange", annotation_text="high limit")
 
# Mark only samples where *this* channel is out of limits.
channel_bad = df[df[violation_column(parameter)]]
if not channel_bad.empty:
    fig.add_scatter(
        x=channel_bad["timestamp"],
        y=channel_bad[parameter],
        mode="markers",
        name="Out of limits",
        marker={"color": "red", "size": 8},
    )
 
st.plotly_chart(fig, width="stretch")
 
st.subheader("Alert log")
 
alerts = df[df["is_anomaly"]][["timestamp", *CHANNELS, "alerts"]]
if alerts.empty:
    st.info("No alerts to display.")
else:
    st.dataframe(alerts, width="stretch")
 
export_cols = ["timestamp", *CHANNELS, "alerts", "is_anomaly"]

render_guided_response(df, CHANNELS)

st.download_button(
    "Download telemetry CSV",
    data=df[export_cols].to_csv(index=False).encode("utf-8"),
    file_name="simulated_telemetry.csv",
    mime="text/csv",
)