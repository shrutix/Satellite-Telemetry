# 🛰️ Satellite Telemetry Monitor

A dashboard that simulates spacecraft health telemetry, injects known faults, and flags out-of-limit readings with a transparent, rule-based detector.

> **Prototype, not flight software.** All data is simulated and the limits are illustrative values chosen for this demo. They are not real spacecraft limits.

## Features

- **Simulated telemetry** for four channels: battery voltage, temperature, angular rate, and signal strength (600 samples at 10-second intervals)
- **Six scenarios**: one nominal case and five injected faults, so you can watch the detector respond
- **Rule-based anomaly detection** against configurable limits, with a per-channel violation flag and a readable alert message for each affected sample
- **Interactive time-series chart** (Plotly) with dashed limit lines and red markers on out-of-limit samples for the selected channel
- **Summary cards** showing the latest reading per channel plus a violation count, so a fault that has already passed (like a single-sample spike) is still visible
- **Alert log** table of every anomalous sample, with a **CSV download** of the full dataset
- **Deterministic output**: a fixed random seed means the same scenario always produces the same data
- **Automated tests** for the generator, the detector, and the app itself

![Satellite Telemetry Monitor dashboard showing a battery voltage drop fault](docs/batteryVoltageDropExample.png)

## Scenarios

| Scenario | What happens (second half of the run) |
| --- | --- |
| Normal | All channels stay within limits |
| Battery voltage drop | Voltage ramps down by 5 V |
| Thermal rise | Temperature ramps up by 45 °C |
| Excessive angular rate | Angular rate jumps by +3.5 °/s |
| Weak signal | Signal strength ramps down by 40 dB |
| Sensor spike | One temperature sample reads 95 °C |

## Detection limits

These are demo values defined in `detector.py`. A reading exactly on a bound counts as in range.

| Channel | Low | High |
| --- | --- | --- |
| Battery voltage (V) | 24.0 | 32.0 |
| Temperature (°C) | -10.0 | 60.0 |
| Angular rate (°/s) | -2.0 | 2.0 |
| Signal strength (dB) | -110.0 | -50.0 |

## Getting started

### Requirements

- Python 3.10 or newer
- The packages in `requirements.txt` (numpy, pandas, plotly, streamlit 1.50 or newer, pytest)

### Install

```bash
git clone <your-repo-url>
cd satellite-telemetry

python3 -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Run the app

```bash
python -m streamlit run app.py
```

Streamlit prints a local URL (usually <http://localhost:8501>). Open it, pick a scenario, then choose a channel to inspect.

### Run the tests

```bash
python -m pytest
```

The detector and telemetry tests run in under a second. The app tests launch the whole Streamlit script for every scenario and channel, so the full suite takes longer. To run only the fast tests:

```bash
python -m pytest tests/test_detector.py tests/test_telemetry.py
```

## How detection works

`detect_anomalies(df, limits=None)` takes a DataFrame of telemetry and returns a copy with three kinds of added columns:

- `<channel>_violation`: boolean, true where that channel is outside its limits
- `alerts`: the messages for that sample joined with `"; "` (empty if none)
- `is_anomaly`: boolean, true if any channel is out of limits

You can pass your own limits to override the defaults. NaN values are not flagged, and invalid limits (low greater than high) raise a `ValueError`.

```python
from telemetry import generate_telemetry
from detector import detect_anomalies

df = detect_anomalies(generate_telemetry("Thermal rise"))
print(df.loc[df["is_anomaly"], ["timestamp", "temperature_c", "alerts"]].head())
```

## License

This project is released under the [MIT License](LICENSE).