# Milestone 2.3B: departure times and reference consistency

## What changed

`LaneBottleneck` now keeps an **absolute local logical clock** and records
`(cyclistId, timeSeconds)` whenever a service-completion transition happens.
The **real DEVS-Suite coordinator still drives time**: the lane only accounts
for the elapsed time passed to `deltext` and for its own already-scheduled
service completion. Its `out()` method remains side-effect free.

- During `deltext(e, x)`, the model advances its local time by `e` while the
  parent framework's `Continue(e)` adjusts remaining service time.
- When service starts, its due time is `localTime + passageSeconds`.
- During `deltint()` or `deltcon()` the model records the completion at that due
  time, before starting another service.
- `departureTrace()` returns an unmodifiable snapshot (not a live mutable list).

The production Java runner now **fails** unless departures occur in FIFO order
at `cyclist-1 = 14s` and `cyclist-2 = 24s`. It also emits lines such as:

```text
DEPARTURE,14.000,cyclist-1
DEPARTURE,24.000,cyclist-2
PASS: real coordinator departure timestamps match 14s and 24s.
```

This is a **deterministic verification example**, not an observation about a
specific NYC street. The first cyclist already in service may finish during
blockage. Cyclist 2 arrives at 15s, waits until clearance at 20s, and takes
four seconds to complete the bottleneck passage. Thus wait = 5 seconds.

## How to test (Windows PowerShell, repository root)

```powershell
# Compile all production classes against the external jar, then execute
# the real external coordinator (not the test adapter).
.\devsjava\scripts\run-real-coupled.ps1

# Independently exercise the timestamp bookkeeping with the tiny test adapter.
docker build -f devsjava/Dockerfile.timestamp-tests -t cyclistics-timestamp-tests devsjava
docker run --rm cyclistics-timestamp-tests

# Includes a Python reference check of the same deterministic inputs.
docker compose run --build --rm tests
```

The Python test checks the independent `cyclistics.simulation.simulate`
reference: event times are 10, 12, 14, 15, 20, 24 seconds, max queue = 1,
mean wait = 2.5 seconds. The Java runner checks its own two completion times.
Agreement on this **single fixture** is not a general Java-vs-Python parity
suite; future work should use shared input fixtures across many scenarios,
simultaneous event cases, repeated obstructions, and larger NYC-informed rates.

## Scope & attribution

- External integration tested using historical **DEVS-Suite 2.1.0** (when
  run with that locally installed JAR); this is not proven to be the
  professor's exact course distribution.
- `test_support/` is a tiny adapter used only in standalone smoke tests.
  The real runner compiles production classes against the external JAR.
- Python arrivals are synthetic or data-informed, **not measured individual
  bicycle trajectories**. Do not present scenario timings as real-world validation.

## DEVS lecture vocabulary

**Atomic model**: lane bottleneck's state = blockage status, FIFO queue,
current service, and sigma. **Output**: departure emitted before an internal
transition. **External transition**: handles cyclist arrival and BLOCK/CLEAR.
**Confluent transition**: resolves a completion occurring at the same instant
as a new input. **Time advance**: remaining time until scheduled completion.
**Coupled model**: ports route generator/obstruction events into the lane.
**Coordinator**: advances the global simulation clock, NOT this test harness.
