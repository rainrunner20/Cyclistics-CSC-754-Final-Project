# Milestone 3.8B — Reproduce computational performance evidence

This is a measured benchmark workflow. It **does not** fabricate runtime numbers or infer NYC traffic outcomes.

## Step 1 — Open the performance branch (Windows PowerShell)

From your Cyclistics repository root, ensure the current worktree is clean before switching:

```powershell
git branch --show-current
git status
git fetch origin
git switch --track -c feat/performance-evidence origin/feat/performance-evidence
git status
```

This branch starts from the last released `main` while sensitivity-results PR #6 remains separate. **Do not delete PR #6 or any existing feature branch.**

## Step 2 — Run code tests

```powershell
docker compose run --build --rm tests
```

The released `main` had 139 tests. This performance branch adds six unit tests (145 total). The new test fixtures **are invented solely to test software arithmetic and rejection rules**; never put their numbers in a course report.

## Step 3 — Check whether desktop NetLogo already exported the measurements

```powershell
Test-Path .\outputs\netlogo_verification_checks.csv
Test-Path .\outputs\netlogo_runtime_benchmarks.csv
```

Both should return `True`. If either is missing, open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` in **NetLogo 6.3.0**, make sure **Go** is stopped, and click:

1. **Run verification checks** (must export five verification cases).
2. **Benchmark runtime** (must export 36 measurements).

The 36 trials cover 150/600/900 attempted cyclists/hour, obstruction disabled/enabled, horizons 600/1,200 ticks, and seeds 201–203. NetLogo wall-clock runtime excludes setup, uses suppressed display updates, and includes a separate unmeasured warmup before the benchmark grid.

Do not use fake CSV rows. Before analysis, inspect the exports:

```powershell
(Import-Csv .\outputs\netlogo_verification_checks.csv).Count
(Import-Csv .\outputs\netlogo_runtime_benchmarks.csv).Count

Import-Csv .\outputs\netlogo_runtime_benchmarks.csv |
    Select-Object -First 3 |
    Format-Table
```

## Step 4 — Generate the paper table and both figures

```powershell
docker compose run --build --rm simulation python -m cyclistics.performance_evidence --verification /app/outputs/netlogo_verification_checks.csv --benchmarks /app/outputs/netlogo_runtime_benchmarks.csv --model /app/netlogo/Cyclistics_Bike_Lane_ABM.nlogo --output-dir /app/outputs/performance_evidence
```

The CLI validates both files before producing a report. Expected counts: **five verification cases**, **36 measured benchmark rows**, **12 summary groups**.

The generated outputs remain Git-ignored at `outputs/performance_evidence/`:

| File | Meaning |
| --- | --- |
| `performance_table.csv` | 12 rows of measured elapsed seconds, milliseconds per tick and descriptive statistics |
| `performance_table.md` | Readable table and caveats for the CSC 754 paper |
| `netlogo_runtime_600s.svg` | Runtime versus attempted cyclist demand for 600 simulated ticks |
| `netlogo_runtime_1200s.svg` | Same plot for 1,200 simulated ticks |
| `performance_manifest.json` | Source and output SHA-256 hashes; computational units and caveats |

Inspect the files in PowerShell:

```powershell
Import-Csv .\outputs\performance_evidence\performance_table.csv |
    Format-Table arrival_rate_per_hour,blockage_enabled,run_length_s,mean_elapsed_real_s,mean_ms_per_sim_tick

Get-Content .\outputs\performance_evidence\performance_manifest.json
Start-Process .\outputs\performance_evidence\netlogo_runtime_600s.svg
Start-Process .\outputs\performance_evidence\netlogo_runtime_1200s.svg
```

Please retain the **original** local CSV exports; Git deliberately ignores generated observations.

## Step 5 — Separately reproduce the deterministic Python / DEVS-Suite comparison

The external DEVS-Suite JAR is not checked into Git. If you have the compatible local JAR in `devsjava/vendor/`, run:

```powershell
.\devsjava\scripts\run-real-coupled.ps1
```

Expected two-cyclist fixture departures: **14 s and 24 s**. This is the real coordinator executing a controlled event schedule, **not** NetLogo wall-clock benchmarking, Java-versus-NetLogo performance, or real NYC validation.

For fuller evidence, supply a saved coordinator log to the existing `cyclistics.cross_model_comparison` command as described in [cross-model comparison results](cross_model_comparison_results.md). The output log must be real, not fabricated.

## What to write in the paper

The NetLogo benchmark provides a **descriptive, hardware-dependent computation-time study**. Keep simulated time (model ticks) separate from wall-clock time (how many seconds the computer spent calculating). Three seeds per setting do not support strong claims about scalability or superiority of one engine over another.

Do not quote any numerical runtime means until the actual NetLogo CSV passes validation and the resulting table is reviewed. Python tests alone never execute the NetLogo desktop model.

The DEVSJAVA comparison separately shows that the Python reference and the historical DEVS-Suite coordinator agree on departure times for **one** deterministic scenario. It verifies that case, not comprehensive model equivalence or predictions of crashes.
