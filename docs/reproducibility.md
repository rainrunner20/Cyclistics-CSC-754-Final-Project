# Cyclistics — reproduce the current implementation

**Tested checkpoint:** `main` after PR #7 (commit `cef4aa7`, November 14, 2026 New York time). The code includes three separately executed simulation formalisms, not a live-coupled NYC digital twin.

## 1. Check out and test the code

From VS Code's **PowerShell** terminal in the Cyclistics repository root:

```powershell
git remote get-url origin
git status
git fetch origin
git switch main
git pull --ff-only origin main
git status

docker compose run --build --rm tests
```

The GitHub-hosted CI on this checkpoint reported **151 passing Python tests** and 4/4 checks (Python 3.11/3.12/3.13 and Docker). These tests cover Python reference behavior, source-level NetLogo structure and evidence-export tooling. They **do not** execute the desktop NetLogo GUI or the external DEVS-Suite coordinator.

[Successful merged-main CI run](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43667009570).

## 2. Run a Python DES scenario

```powershell
docker compose run --build --rm simulation
```

Or a controlled custom rate:

```powershell
docker compose run --rm simulation python -m cyclistics --rate 450 --seed 754 --output-dir /app/outputs
```

**Assumptions:** a single FIFO bottleneck, seeded Poisson arrival times, deterministic passage headways, scheduled block/clear events, and equal arrival draws across Python scenarios. The default synthetic example uses 300 attempted cyclists/hour over an 1,800-s arrival horizon. The program produces ignored CSV traces/metrics in `outputs/`. Original packaged synthetic example: `examples/results/scenario_metrics.csv`.

Python arrival times/events are simulated. Assumed free-flow travel components and queueing estimates are **not field-validated NYC observations**.

## 3. Run NetLogo desktop experiments

Open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` in **NetLogo 6.3.0**, stop the forever **go** button, then use the interface buttons:

- **Compare clear vs blocked:** a matched two-scenario experiment, exported to `outputs/netlogo_paired_results.csv`.
- **Run sensitivity study:** 4 arrival rates × 4 blockage durations × 10 seeds; exports `outputs/netlogo_sensitivity_raw.csv` with 160 paired records (200 actual model executions including reused controls).
- **Run verification checks:** 5 deterministic/structural behavior checks; exports `outputs/netlogo_verification_checks.csv`.
- **Benchmark runtime:** 36 actual timed runs and 12 groups; exports `outputs/netlogo_runtime_benchmarks.csv` (local timings depend on the Windows computer).

NetLogo's scene includes a colored one-lane roadway, waiting cyclist turtles, truck obstruction and queue plot. Asphalt/sidewalk visuals do not create an overtaking lane or motor traffic model.

## 4. Export paper figures from the original NetLogo data

**Sensitivity findings (local model output):**

```powershell
docker compose run --build --rm simulation python -m cyclistics.research_evidence --input /app/outputs/netlogo_sensitivity_raw.csv --model /app/netlogo/Cyclistics_Bike_Lane_ABM.nlogo --output-dir /app/outputs/research_evidence
explorer.exe .\outputs\research_evidence
```

Expected **160 validated rows**, 16 summary configurations, `netlogo_delta_mean_queue.svg` and `netlogo_delta_peak_queue.svg`, two paper tables and `evidence_manifest.json`. Check SHA-256 values against the original source files. Never synthesize missing experimental CSVs to make the analysis pass.

**Runtime findings (desktop CSVs, if generated locally):**

```powershell
docker compose run --build --rm simulation python -m cyclistics.performance_evidence --verification /app/outputs/netlogo_verification_checks.csv --benchmarks /app/outputs/netlogo_runtime_benchmarks.csv --model /app/netlogo/Cyclistics_Bike_Lane_ABM.nlogo --output-dir /app/outputs/performance_evidence
explorer.exe .\outputs\performance_evidence
```

Expected **5 verification cases**, **36 timed trials**, 12 summary rows, two `netlogo_runtime_*.svg` figures and the SHA-256 manifest.

The repository also has a [real GitHub-hosted headless NetLogo 6.3.0 benchmark](performance_evidence_results.md) using Ubuntu rather than the user's Windows computer. Its archived artifact contains the original raw CSVs and generated charts, but GitHub artifacts can expire. [Source GitHub Actions run](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43666376890).

**Keep the two runtime environments separate.** Their results should not be presented as though they were measured on the same hardware.

## 5. Run the historical DEVS-Suite Java coordinator

The external Java library is deliberately **not** in Git. Put a compatible historical DEVS-Suite 2.1 JAR under ignored `devsjava/vendor/`, then execute:

```powershell
.\devsjava\scripts\verify-real-devsjava.ps1
.\devsjava\scripts\run-real-coupled.ps1
```

The runner compiles production Java classes against the **real external library**, not the lightweight test adapter, and verifies two departures at simulated times **14 s and 24 s**. This demonstrates one deterministic fixture matching the independent Python reference, not equivalence across arbitrary schedules. It is also not evidence that the external JAR is Dr. Gu's exact course distribution.

Five separate Java adapter-level Docker suites were run during initial integration, with 199 assertions in total; those adapters are not the actual external coordinator. Full historical details: [integration verification](final_integration_verification.md).

## 6. NYC input source caution

Data-fetch and quality-check tooling can read NYC DOT bicycle counter snapshots, but the [Prospect Park West calibration stream](nyc_prospect_park_west_calibration.md) was marked **raw** and has ambiguities among simultaneous flow IDs. Selection of one provisional 99-riders/hour stream informs only a model **arrival-rate parameter**. It does not validate actual rider trajectories, queue durations or safety effects.

## 7. Archive the final evidence

- Preserve the original local `outputs/netlogo_sensitivity_raw.csv` and matching SHA-256 manifest.
- Save both sensitivity SVGs or lossless raster exports for the paper, retaining captions and interval descriptions.
- Download the [GitHub cloud benchmark artifact](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43666376890) before retention expiry.
- Keep screenshots from **your real NetLogo UI** with visible parameters, simulation tick and queue; don't manufacture UI evidence.
- Do not commit raw generated experiment outputs, third-party JARs or private files; the `outputs/` directory is intentionally Git-ignored.

## Troubleshooting

- Confirm Docker Desktop is running before `docker compose run`.
- If Git reports uncommitted work, review it before switching branches; avoid commands that discard changes.
- A missing local NetLogo CSV is a **data-generation step**, not permission to use a unit-test fixture as a substitute.
- NetLogo headless CI requires its own official Linux package; a Python-only Docker test success is not proof that NetLogo ran.
- Linux bind mounts may require write permissions for the container user (UID 10001).

See [final submission evidence ledger](final_submission_status.md), [project scope](project_scope.md), and [report/presentation blueprint](final_report_presentation_plan.md).
