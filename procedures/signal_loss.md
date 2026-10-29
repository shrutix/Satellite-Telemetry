---
id: SOP-004
title: Signal Strength Below Limit, Signal Loss
channel: signal_strength_db
severity: High
escalate_to: Communications and ground systems engineer on call
---
 
> Simulated procedure. Not for use on a real spacecraft.

## Prerequisites

- Telemetry display is live and the alert is visible in the alert log
- Incident log is open and ready to record entries

## Steps

1. Record the alert time, the signal strength reading, and whether it is
   below the low limit or above the high limit.
2. Check the next two samples to see whether the reading is real. If the
   value returns to normal immediately, log it as a brief fade and keep
   monitoring for 10 minutes.
3. Determine the trend: a gradual decline over many samples suggests
   something degrading, such as antenna pointing or a ground-side problem. A
   sudden drop suggests a switch or hardware event. Record the trend and the
   rate of decline.
4. Check the ground side first. Confirm the ground station antenna, receiver,
   and any weather or interference reports are normal, since many signal
   problems start there. Record what you checked.
5. Check the other channels. A change in angular rate may mean the
   spacecraft's antenna has stopped pointing at the ground station. A power or
   temperature problem may point to a hardware fault. Record anything unusual.
6. Notify the escalation contact if the reading stays out of limits for 3 or
   more consecutive samples, or if the ground-side checks are clean. State the
   reading, the trend, what you ruled out on the ground side, and the time it
   first went out of limits.
7. Follow the engineer's instructions and record each instruction and the time
   you carried it out. Take no action that is not covered by this procedure or
   directed by the engineer.
8. Continue monitoring and log the signal strength at each check until the
   exit criteria are met or the engineer takes over.

## Exit criteria

- Signal strength has stayed inside limits for 10 continuous minutes, or
- The escalation contact has formally taken over the incident
- The incident log is complete, with times, readings, and actions taken
