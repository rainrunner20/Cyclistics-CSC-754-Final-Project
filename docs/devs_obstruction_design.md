# Cyclistics — ObstructionController design (Milestone 2.1B)

**Branch:** `feat/devs-atomic-models`
**Status:** Standalone Java atomic logic and local smoke tests. We have **not** run this against the official DEVSJAVA coordinator yet.

**Current verification (November 14, 2026):** The production Java sources have been merged into `feat/final-integration`; five classes compile against the external historical DEVS-Suite 2.1 JAR, and the coupled coordinator ran the deterministic two-cyclist fixture (departures at 14 s and 24 s). This does not establish field validation or equivalence to the course-provided distribution.

## Why does this component exist?

The Python model already uses obstruction periods. We want DEVSJAVA to emit the same kinds of events without hardcoding a truck inside the cyclist generator. Keeping these responsibilities separate also makes coupled DEVS easier later.

An obstruction is a time window `[start, end]`, in seconds from simulation start. For example, `[[300, 600], [750, 870]]` represents two truck blockages. The model emits `block` and `clear` events at the boundaries.

```text
Simulation clock   0 -------- 300 -------- 600 ---- 750 ------ 870
                                     |                |
Port output                    block / clear     block / clear
State                clear -> blocked -> clear -> blocked -> clear
```

## DEVS model (in course terminology)

\(M = \langle X, S, Y, \delta_{int}, \delta_{ext}, \lambda, ta \rangle\)

| Element | Cyclistics meaning |
| --- | --- |
| `X` | Empty for now — the controller is driven by a prepared schedule |
| `S` | `nextEventIndex`, `blocked`, current phase and remaining time (`sigma`) |
| `Y` | `block`, `clear` output events |
| `delta_int` | Apply scheduled state change, advance to next event |
| `delta_ext` | No accepted inputs; preserve remaining time for an empty event bag |
| `lambda` | Announce the upcoming block/clear event before `deltint` |
| `ta` | Time until next scheduled transition; infinity when finished |

**Why use relative time in `holdIn`?** Suppose the first truck arrives at 300s and leaves at 600s. After processing the first event, the next transition is *300 seconds away*, not 600 seconds away. The model uses `600 - 300`.

**What if obstructions touch?** `[[0, 5], [5, 7]]` is permitted. The controller emits `clear` at 5 seconds, then `block` after a zero-duration time advance at the same timestamp. A future coupled model must define how it processes these microsteps.

**Assumptions and limits:** We're representing exogenous blockage schedules, not detecting real trucks. These are scenario inputs, not measured NYC obstruction-duration data. The same event schedule can later be used by the `LaneBottleneck` and the NetLogo environment. The smoke test uses a fake DEVSJAVA adapter, not the real framework.

## Reproduce the tests

From repository root in VS Code PowerShell:

```powershell
docker build -f devsjava/Dockerfile.obstruction-tests -t cyclistics-obstruction-tests devsjava
docker run --rm cyclistics-obstruction-tests
```

Also run the existing generator test and Python regression suite to check for accidental breakage.

## Development journal prompts — complete using your actual experience

1. Why does `out()` announce the event *before* `deltint()` updates `blocked`?
2. Why do we reject overlapping time windows?
3. What happens if the truck arrives at exactly the same time a cyclist arrives? (The coupled model will need to resolve this.)
4. What did your actual local test output say? Record the command and result.

## Next

Implement `LaneBottleneck`, then obtain Dr. Gu's official DEVSJAVA distribution to validate API compatibility, coordinate the atomic models, and test real DEVS event routing.
