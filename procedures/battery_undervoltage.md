---
id: SOP-001
title: Battery Voltage Below Limit
channel: battery_voltage
severity: High
escalate_to: Power subsystem engineer on call
---
 
> Simulated procedure. Not for use on a real spacecraft.

## Prerequisites

- Telemetry display is live and the alert is visible in the alert log
- Incident log is open and ready to record entries

## Steps

1. Record the alert time and the battery voltage reading in the incident log.
2. Check the next two samples to confirm the low reading is not a
   single-sample sensor glitch. If voltage returns inside limits right away,
   log it as a suspected glitch and keep monitoring for 10 minutes.
3. Check whether the voltage is falling steadily or dropped suddenly, and
   note the rate of change in the incident log.
4. Check the other channels (temperature, signal strength) for related
   changes. Record anything unusual.
5. If the voltage is falling steadily, or stays below the limit for 3 or more
   consecutive samples, notify the escalation contact. State the reading, the
   trend, and the time it first went out of limits.
6. Follow the engineer's instructions and record each instruction and the time
   you carried it out. Take no action that is not covered by this procedure or
   directed by the engineer.
7. Continue monitoring and log the voltage at each check until the exit
   criteria are met or the engineer takes over.

## Exit criteria

- Voltage has stayed inside limits for 10 continuous minutes, or
- The escalation contact has formally taken over the incident
- The incident log is complete, with times, readings, and actions taken
