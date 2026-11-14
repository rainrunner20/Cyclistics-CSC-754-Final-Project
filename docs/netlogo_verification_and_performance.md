# Cyclistics — Milestone 3.3A: NetLogo verification and performance

## Goal

We already have a working visual cyclist agent-based model and a 160-row sensitivity study. This step makes two further claims **testable**:

1. **Internal verification:** The implemented NetLogo model follows its own bookkeeping, timing, and reproducibility rules.
2. **Computational performance:** The runtime required for a fixed number of simulated seconds can be measured when demand and simulation horizon increase.

Neither type of test establishes accuracy against observed NYC traffic. Field validation requires independent observed queue, passage, or delay measurements that the current project does not possess.

## Run from NetLogo desktop

1. From the project root, ensure `outputs/` exists: `New-Item -ItemType Directory -Force .\outputs | Out-Null`.
2. Close the old model window **without saving**, then open the updated `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
3. Ensure **Go** is not running. Click **Run verification checks** (or run `run-verification-suite` from Command Center).
4. Confirm `PASS: 5 verification scenarios with per-tick invariants.` and that `outputs/netlogo_verification_checks.csv` exists.
5. Click **Benchmark runtime** (or execute `run-runtime-benchmarks`). Confirm `PASS: wrote 36 benchmark runs.` and `outputs/netlogo_runtime_benchmarks.csv` exists.
6. On error, stop the run, copy the error and the highlighted NetLogo line, and do not commit the patch. If graphics stay frozen after an error, issue `display` in the Command Center.

The batch procedures temporarily suppress view refreshes and then restore the original slider values and reset the visualization. They **do not** change your previously generated sensitivity-study CSV.

## What the five verification cases check

| Case | Settings | Expected invariant |
|---|---|---|
| `zero_demand` | 0 cyclists/hour, no truck | No riders, queues, or departures |
| `clear` | 600/hour, seed 754, no truck | Baseline accounting and tick checks |
| `clear_repeat` | Same settings as `clear` | Exactly the same simulated results and draws |
| `zero_duration` | Truck enabled but duration 0 | Exactly the same results as `clear` |
| `blocked` | Truck from 45s through 109s | Exactly 65 active model ticks and paired demand/speeds |

**Every tick** of every case checks: cyclist conservation; requested = admitted + pending; admitted = departed + active; queue accounting; cumulative queue area; valid cyclist position and speed; actual truck count and half-open obstruction schedule. The fixed blocked fixture also checks that the queue effect does not disappear relative to the control. These checks are **code-level verification**, not proof that the traffic representation is realistic.

## How the runtime experiment is designed

We use a modest **3 × 2 × 2 × 3 = 36-run** design:

- Demand: 150, 600, 900 attempted cyclists/hour.
- Obstruction: disabled or enabled (truck starts at t=45 and lasts 65 seconds).
- Horizon: 600 or 1,200 simulated seconds.
- Random seeds: 201, 202, 203 (matched across blocked/clear conditions).

The model first performs one *unmeasured* 100-tick warmup. Each measured trial calls `setup`, then `reset-timer`, then advances `go` for the exact horizon. Thus **model initialization is excluded from measured wall time**. After each trial, it checks conservation and stores elapsed real seconds and milliseconds per simulation tick.

`timer` records actual elapsed wall-clock time, whereas `ticks` is simulated time. `no-display` turns off view updates; note that NetLogo plots can still be updated. Runtime also depends on the computer, Java/NetLogo version, background processes, thermal conditions, and JVM optimization. Three runs per configuration are a small **benchmark sample**, not a reliable population-level performance estimate. Run on the same machine using consistent settings; record machine specs in the final report.

## Python validation and charts

After both NetLogo CSVs exist, run from the repository root using Docker Desktop:

```powershell
# Structural/in-memory tests do not execute the NetLogo engine.
docker compose run --build --rm tests

# Analyze the *actual* NetLogo exports; no synthetic research values are created here.
docker compose run --build --rm simulation python -m cyclistics.netlogo_benchmarks --verification /app/outputs/netlogo_verification_checks.csv --benchmarks /app/outputs/netlogo_runtime_benchmarks.csv --output-dir /app/outputs
```

The analysis program validates the **five verification cases**, **all 36 benchmark runs**, matching baseline demand, finite positive timings, and cyclist conservation. On success it writes:

| Generated output | Meaning |
|---|---|
| `outputs/netlogo_verification_report.json` | Internal-verification summary and boundaries |
| `outputs/netlogo_runtime_summary.csv` | 12 configuration means, ranges and sample SDs |
| `outputs/netlogo_runtime_600s.svg` | Measured time per tick at a 600-second simulation horizon |
| `outputs/netlogo_runtime_1200s.svg` | Same comparison for a 1,200-second simulation horizon |

To inspect:

```powershell
Import-Csv .\outputs\netlogo_runtime_summary.csv | Format-Table arrival_rate_per_hour,blockage_enabled,run_length_s,mean_ms_per_sim_tick
Start-Process .\outputs\netlogo_runtime_600s.svg
Start-Process .\outputs\netlogo_runtime_1200s.svg
```

If the analysis rejects the exported data, **do not alter measurements to make the test pass**. Investigate the NetLogo run and fix the underlying discrepancy. The Python unit tests exercise intentionally fabricated test fixtures only; those are never substituted for exported results.

## Research discussion for CSC 754

- **ABM:** Local collision-avoidance and truck stop-line rules yield emergent queues.
- **Verification:** Per-tick invariants, deterministic replay, zero-demand/zero-duration controls, and obstruction timing test implementation correctness.
- **Performance:** NetLogo advances a global fixed clock one second at a time. We quantify computational cost as wall-clock milliseconds per simulation tick under rising demand and horizon.
- **DEVS distinction:** Our Java DEVS-Suite model jumps between scheduled events using its coordinator. NetLogo's independent moving agents are **not yet equivalent** to the single-server DEVS bottleneck, so compare the architectures and assumptions instead of claiming matched congestion measurements.
- **Validation (later):** NYC bicycle-count data can inform arrivals, but independently observed queues or travel times are still needed to validate real-world outcome predictions.

### Reproducibility record to include in the paper

Save the Git commit hash (`git rev-parse --short HEAD`), NetLogo version (**Help → About NetLogo**), CPU/RAM, OS, model parameters, and the generated raw CSVs. The raw files are gitignored because they are generated local results; retain the real run outputs for paper preparation without adding fabricated values to the repository.

**Test status when this patch was packaged:** 92 repository Python/static tests passed in local reconstruction, including 20 new ones. This is not proof of successful execution in the actual NetLogo engine. Desktop verification and real benchmark exports are required before a milestone-completion claim.
