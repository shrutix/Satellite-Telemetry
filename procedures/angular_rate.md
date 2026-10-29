---
id: SOP-003
title: Angular Rate Outside Limits
channel: angular_rate_dps
severity: Critical
escalate_to: Attitude control engineer on call
---
 
> Simulated procedure. Not for use on a real spacecraft.

## Prerequisites

- Telemetry display is live and the alert is visible in the alert log
- Incident log is open and ready to record entries

## Steps

1. Record the alert time and the angular rate reading, including its sign
   (direction of rotation).
2. Check the next two samples to see whether the reading is real. If the
   value returns to normal immediately and the other channels show no change,
   log it as a suspected sensor glitch and keep monitoring for 10 minutes.
3. If the reading stays out of limits, determine whether the rate is steady,
   growing, or shrinking, and record the trend. A steady offset can point to a
   stuck control actuator. A growing rate means the spacecraft is spinning up
   and is more urgent.
4. Check the other channels. Falling signal strength can mean the spacecraft
   is no longer pointing at the ground station. A temperature or power change
   may point to a related fault. Record anything unusual.
5. Notify the escalation contact immediately if the reading stays out of
   limits for 2 or more consecutive samples or the rate is growing. This
   condition is time-critical, so do not wait for a third sample. State the
   reading, direction, trend, and the time it first went out of limits.
6. Follow the engineer's instructions and record each instruction and the time
   you carried it out. Take no action that is not covered by this procedure or
   directed by the engineer.
7. Continue monitoring and log the angular rate at each check until the exit
   criteria are met or the engineer takes over.

## Exit criteria

- Angular rate has stayed inside limits for 10 continuous minutes, or
- The escalation contact has formally taken over the incident
- The incident log is complete, with times, readings, and actions taken
