# Cyclistics v2 — Java DEVS-Suite offline event replay

**Implemented:** An independent Java CSV parser and a real-coordinator runner accepting a dynamically supplied obstruction schedule. It is not live NetLogo–Java coupling.

## Reproduce the parser (CI, no external JAR)

The Java 17 schedule parser recognizes the event bridge's validated time_s,event_type CSV, requires nonnegative sorted whole-second timestamps, rejects overlapping/unclosed or nonpositive block windows, and converts each start/end pair into a DEVS obstruction interval. Independent Java tests exercise both valid and deliberately malformed synthetic schedules.

The GitHub workflow V2 Java schedule parser compiles ObstructionSchedule.java and its test class with JDK 17. **It does not run the production coordinator**, because the historical DEVS-Suite JAR is not redistributable in Git.

## Execute the actual DEVS-Suite coordinator on your computer

Obtain a compatible historical DEVS-Suite 2.1 JAR under the ignored devsjava/vendor folder, as required by the original integration workflow. From repository-root PowerShell:

~~~powershell
.\devsjava\scripts\run-v2-replay.ps1
~~~

Default inputs: netlogo/fixtures/v2_synthetic_obstruction.csv, cyclist arrivals at 10/15 seconds, service headway 4 seconds. That synthetic event CSV blocks the modeled lane between t=12 and t=20; on an actual historical Java runtime this matches the already verified **14/24-second** deterministic setup, but **the new replay class itself must be executed locally before its output is claimed verified**.

You can provide your own **validated** event-bridge CSV and controlled arrivals:

~~~powershell
.\devsjava\scripts\run-v2-replay.ps1 -EventFile 'outputs/v2_replay/netlogo_obstruction_events.csv' -Arrivals '10,15' -Headway '4'
~~~

Paths are relative to the repository; external JAR files stay local. The script compiles all production Java files against your real DEVS-Suite library and invokes CyclisticsReplayRunner. It prints departures and validates accounting from the external coordinator.

## What we cannot claim

- No Python/Java/NetLogo *live* single-clock coordination has been implemented.
- Imported windows are *simulation-second* schedules, not geographic or UTC camera timestamps.
- The historical Java coordinator previously passed one deterministic run in v1; the new configurable Java replay runner still requires its own real external-JAR execution check.
- No real-world cyclist delays, lane closures or crash probabilities have been validated.

**CSC 754 mapping:** Input/output event messaging, atomic generator/controller/bottleneck responsibilities, coupled DEVS ports, real coordinator-driven time advance, and a deterministic offline event-exchange experiment.
