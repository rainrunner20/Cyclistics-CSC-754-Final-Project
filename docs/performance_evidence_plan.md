# Milestone 3.8B — Computational performance and cross-model verification

**Branch:** `feat/performance-evidence` (starts from merged `main` at `9b3c514`).  
**PR dependency:** Research sensitivity PR #6 remains separate and open. This branch is based on `main` to avoid disturbing the validated research work.

## Research questions

1. How does measured NetLogo computation time change with *simulated* cyclist demand, obstruction on/off, and run length?
2. Do the Python discrete-event reference and the external DEVS-Suite coordinator agree on a shared, tiny deterministic event fixture?
3. Which of these claims are *verification*, and which would require real-world *validation*?

## NetLogo performance design (already implemented)

The NetLogo model exports `outputs/netlogo_verification_checks.csv` and `outputs/netlogo_runtime_benchmarks.csv`. The first has **five named verification cases**, and the second must contain **36 real measured runs**:

| Design variable | Values |
| --- | --- |
| Attempted cyclist demand | 150, 600, 900 per hour |
| Obstruction | Disabled or enabled (start 45 s, duration 65 s) |
| Simulation horizon | 600 or 1,200 ticks |
| Independent benchmark seeds | 201, 202, 203 |
| Computational measure | Elapsed wall-clock seconds, milliseconds per simulation tick |

A 100-tick *unmeasured* warmup precedes each timed run. The timer begins after `setup`; view updates are suppressed during tests. Runtime will vary by host hardware, operating system, NetLogo and Java versions, background processes, and JIT behavior. Three seeds per configuration are a **small descriptive benchmark**, not enough for general scalability or statistical performance claims.

The existing `cyclistics.netlogo_benchmarks` validator rejects incomplete/duplicate configurations, nonfinite runtimes, bad timing arithmetic, and cyclist conservation violations. For Milestone 3.8B, a **new evidence wrapper** will reuse those validators rather than alter the model or synthesize wall-clock measurements.

## Expected performance evidence outputs

Only from the *actual user-generated* NetLogo exports, produce:

- `performance_table.csv`: 12 summarized configurations, timing per tick, elapsed time and descriptive variability.
- `performance_table.md`: compact presentation-oriented table with explicitly labeled units and caveats.
- `netlogo_runtime_600s.svg` and `netlogo_runtime_1200s.svg`: model runtime curves for both horizons.
- `performance_manifest.json`: hashes of both raw NetLogo CSV files, the .nlogo model source, the analysis code, and each generated result, plus assumptions and `field_validated: false`.

These files stay in ignored `outputs/performance_evidence/`. If the two raw CSV inputs do not exist, or fail checks, **no research evidence is generated**. Python test fixtures may exercise the workflow but **cannot** become paper results.

## Separate Python / DEVS-Suite verification

The shared deterministic case has:

- Cyclist arrivals **10 s and 15 s**.
- Obstruction active from **12 s until 20 s**.
- Fixed passage headway **4 s**.
- Predicted departures at **14 s and 24 s** and maximum waiting queue **1**.

The real historical DEVS-Suite coordinator produced the expected departures on November 14, 2026; the Python reference independently reproduced the same fixture. This is evidence of **matching event order/times on one controlled case**, not broad cross-implementation equivalence. NetLogo's spatial ABM is a different scenario and must **not** be plotted as matching the Java/Python event schedule.

Suggested figure: a conceptual event timeline with labeled arrivals, obstruction start/end, and departure events. This schematic is not a screenshot from the actual Java coordinator and should be labeled an explanatory diagram.

## CSC 754 connections

- **Simulation clocks:** NetLogo advances one-second global ticks; DEVS-Suite advances to the next scheduled event time.
- **Atomic/coupled DEVS:** CyclistGenerator, ObstructionController, and LaneBottleneck exchange port messages under a real coordinator. The bottleneck maintains a FIFO queue and scheduled internal transitions.
- **ABM:** individual cyclist turtles interact via local following and obstruction rules; queues emerge from behavior instead of being directly imposed.
- **Performance:** compare the computational cost of different **model settings**, distinguish simulated seconds from wall-clock seconds.
- **Verification vs. validation:** checking event timestamps and conservation tests implementation consistency. Accuracy against NYC observations would require independent measurements.

## Delivery sequence

1. Record experimental protocol and explicit claim boundaries (this document).
2. Add focused tests for performance report generation, input rejection, source hashes, and reproducible output.
3. Add standard-library-only evidence CLI that calls the existing validated benchmark reader and SVG generator.
4. Run Python/Docker CI; obtain real desktop NetLogo benchmark CSVs and export the paper table.
5. Review measured values and plots before claiming any quantitative runtime results.
6. Add or improve the separate deterministic Python/DEVS-Java comparison explanation and integrate findings into the final CSC 754 paper.

**Release rule:** Leave this feature branch and PR #6 untouched until their independent evidence checks pass; do not delete feature branches or merge without review.
