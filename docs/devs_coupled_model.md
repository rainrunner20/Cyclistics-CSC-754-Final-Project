# Cyclistics: coupled DEVS model — Milestone 2.3A

## Purpose

Connect previously tested atomic models into one DEVS network. DEVS-Suite's
`model.simulation.coordinator` is responsible for simulation time and event routing.
This is not a replacement for or extension to the Python reference simulation.

## Network and ports

| Source atomic model | Output port | Target | Input port | Meaning |
| --- | --- | --- | --- | --- |
| CyclistGenerator | arrival | LaneBottleneck | arrival | a cyclist reaches the lane |
| ObstructionController | block | LaneBottleneck | block | passage for new cyclists stops |
| ObstructionController | clear | LaneBottleneck | clear | queued cyclists may resume |
| LaneBottleneck | departed | CyclisticsCoupledModel | departed | external output coupling |

## Deterministic starter scenario

- Arrival schedule: `10, 15` seconds.
- Obstruction: `[12, 20]` seconds.
- One cyclist takes `4` seconds to pass the bottleneck.
- Expected reasoning: cyclist 1 begins at 10, finishes at 14 despite the truck
  arriving at 12. Cyclist 2 arrives at 15 but cannot start until clearance at 20,
  then finishes at 24. Expected departed count: 2. Expected maximum waiting
  queue: 1.
- The runner currently **checks final state and counts**, not an independently
  recorded timestamp trace. Recorded departure times are a later milestone.

## How to run

The 2009 DEVS-Suite 2.1.0 JAR is stored ONLY on the user's machine in
`devsjava/vendor/` and ignored by Git. Run in repository-root PowerShell:

```powershell
.\devsjava\scripts\run-real-coupled.ps1
```

The shell script compiles **only production classes** using the real external
DEVS-Suite JAR and runs `CyclisticsRunner` with the real `coordinator`.
If a Java exception occurs, copy the whole error output; do not commit a false
pass. Compilation of the three earlier atomic models already passed previously.

Optional fast smoke check (does NOT use DEVS-Suite):

```powershell
docker build -f devsjava/Dockerfile.coupled-structure-tests -t cyclistics-coupled-structure devsjava
docker run --rm cyclistics-coupled-structure
```

## Boundaries and next steps

1. The historical DEVS-Suite 2.1.0 JAR is **not confirmed** to be Dr. Gu's
   specific distribution.
2. This stage does not yet compute individual waiting times or departure-time
   comparisons with the Python reference model.
3. Real NYC counts inform a rate in the *Python* model, but this starter
   integration run uses a hand-written deterministic schedule.
4. Run the real coordinator before claiming this integration is verified.
5. Later tests should cover simultaneous block/clear/arrival/departure and
   conservation (generated = departed + queued + in-service).
