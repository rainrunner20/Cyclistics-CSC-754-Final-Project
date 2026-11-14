# Milestone 3.5 — comparing the Cyclistics simulation models

## Question

Do the independently implemented event-driven models agree on a *controlled,
identical* bottleneck scenario, and what can we responsibly learn from a spatial
agent-based simulation with different assumptions?

We have three approaches, not one three-way co-simulation:

- **Python DES reference:** event heap, FIFO passage server, continuous event
  timestamps, service headway, obstruction events and waiting times.
- **DEVSJAVA / historical DEVS-Suite:** `CyclistGenerator`,
  `ObstructionController`, `LaneBottleneck` and `CyclisticsCoupledModel`; the
  external coordinator advances the simulation clock. The production code and
  real coordinator runner currently live on `feat/devs-atomic-models`.
- **NetLogo ABM:** cyclists travel across a single spatial lane with one-second
  ticks, heterogeneous speed draws, local following constraints and a truck.
  This implementation is on `feat/netlogo-abm`.

The implementations do not exchange live events. *Offline evidence collection
is not DEVS–NetLogo coupling.* Do not say they share the same cyclist trajectories.

## Comparison A: deterministic Python ↔ Java fixture

A small fixture lets us compare identical input events and service rules:

| Setting | Value |
| --- | --- |
| Arrival timestamps (s) | `[10, 15]` |
| Blockage interval (s) | `[12, 20)` |
| Passage service time (s) | `4` |
| Simulation observation horizon (s) | `30` |
| Obstruction affects service already underway? | No |
| First departure (s) | `14` |
| Second departure (s) | `24` |
| Peak *waiting* queue | `1` |
| Mean Python wait before service (s) | `2.5` |

At `12s`, the first cyclist is already being served, so the blockage does not
cancel their completion at `14s`. Cyclist 2 arrives during the closure at
`15s` and begins service at `20s`, departing at `24s`. This follows the existing
Python `Scenario`/`simulate` and the Java `CyclisticsRunner` deterministic case.

We can verify exact departure timestamps **only after the actual Java
coordinator has run with the external JAR** and its stdout is captured. Unit
tests containing demonstration log text are not evidence of real execution.
A single matching fixture checks one scheduling case; it does not prove broad
cross-language equivalence, simultaneous-event handling or NYC validity.

## Comparison B: NetLogo blocked versus clear

Use the existing `netlogo_paired_results.csv` from `run-paired-experiment`.
Compare clear versus blocked **within the same NetLogo model**, checking
matching seed, rate, simulated duration, requested arrivals and cyclist
conservation. The exporter records mean queue, peak queue, completed-rider stop
time and departures. A prior verified sample used 99 cyclists/hour, seed 754,
600 seconds, and an obstruction lasting 65 seconds, but it is one stochastic
replication and its underlying NYC count stream was marked `raw`/ambiguous.

**Do not compare NetLogo `mean_stop_completed_s` to Python `mean_wait_s`:** these
are different metrics. Nor should we compare the peak queue counts as if they
had identical definitions: the NetLogo queue includes stopped riders plus
pending entrants; the Python queue counts people waiting for the server.
The Bernoulli one-second arrival process in NetLogo and continuous exponential
interarrivals in Python do not replay the same arrivals simply by using the
same numeric random seed.

## What the CLI will report

`cyclistics.cross_model_comparison` will independently run the Python fixture,
optionally validate a captured Java stdout log, optionally review the NetLogo
paired CSV, and write a JSON report with SHA-256 checksums of supplied files.

Statuses distinguish: Python reference computed; Java evidence absent/matched;
NetLogo evidence absent/internally consistent. **No general three-model parity
claim**, no measured queue validation, no observed cyclist trajectory data.

## Acceptance criteria

- Python fixture yields the expected ordered event sequence and departures.
- Correctly captured Java output has 2 ordered departures at 14 and 24s,
  2 generated and departed cyclists, 2 obstruction events, queue peak 1,
  zero remaining; any mismatch fails rather than producing a passing report.
- Without a Java log, the report explicitly says real Java evidence is pending.
- NetLogo paired CSV must contain clear and blocked rows with identical
  scenario inputs and conservation true in both; report within-model deltas.
- Output includes input-file hashes and prominent model-scope limitations.
- Invalid input must not leave a newly created partial JSON report.

## Follow-up experiments

After this first comparison, investigate simultaneity and confluent events,
multiple blockage intervals, deterministic arrival-schedule exchange, and
replicated stochastic comparisons under **matched assumptions**. Consider
bringing the Java branch into the final integration branch after testing and
resolving conflicts. Keep the original feature branches for provenance.

## CSC 754 connection / presentation explanation

Python demonstrates explicit event-list ordering; Java uses atomic DEVS
`delta_int`, `delta_ext`, `delta_con`, `lambda`, `ta` within a coupled network;
NetLogo demonstrates spatial patches and local agent rules. **Verification**
asks whether each implementation follows its rules. **Validation** asks whether
those rules describe observed city behavior. This milestone primarily verifies
an agreed deterministic case and documents the difference.
