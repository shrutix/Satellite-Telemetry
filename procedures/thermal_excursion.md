---
id: SOP-002
title: Temperature Outside Limits, Thermal Excursion
channel: thermal_excursion
severity: High
escalate_to: Thermal subsystem engineer on call
---

> Simulated procedure. Not for use on a real spacecraft.

## Prerequisites

- Telemetry display is live and the alert is visible in the alert log
- Incident log is open and ready to record entries

## Steps

1. Record the alert time, the temperature reading, and whether it is above
   the high limit or below the low limit.
2. Check the next two samples to see whether the reading is real. If the
   value returns to normal immediately and the other channels show no change,
   log it as a suspected sensor glitch, keep monitoring for 10 minutes, and
   tell the engineer at the next handover.
3. If the reading stays out of limits, determine the trend: rising or falling,
   and the approximate rate of change per minute. Record both in the incident
   log.
4. Check the other channels (battery voltage, angular rate, signal strength)
   for related changes, since a thermal problem can accompany a power or
   attitude problem. Record anything unusual.
5. Notify the escalation contact if the reading stays out of limits for 3 or
   more consecutive samples, or immediately if the temperature is still moving
   away from the limit. State the reading, the trend, the rate of change, and
   the time it first went out of limits.
6. Follow the engineer's instructions and record each instruction and the time
   you carried it out. Take no action that is not covered by this procedure or
   directed by the engineer.
7. Continue monitoring and log the temperature at each check until the exit
   criteria are met or the engineer takes over.

## Exit criteria

- Temperature has stayed inside limits for 10 continuous minutes, or
- The escalation contact has formally taken over the incident
- The incident log is complete, with times, readings, and actions taken
