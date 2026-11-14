# Cyclistics — Milestone 3.2B: replicated NetLogo sensitivity experiments

## Research question

**Under a fixed synthetic bicycle arrival process, how do demand intensity and obstruction duration change waiting queues and cyclist completions?** This milestone uses the existing NetLogo ABM without changing its movement or queue-counting logic. The results are for a **hypothetical one-lane model**, not measured NYC congestion or safety risk.

## Design (160 paired scenario rows)

| Design variable | Values |
| --- | --- |
| Cyclist arrival rate | **150, 300, 600, 900** cyclists/hour |
| Truck obstruction duration | **0, 30, 60, 120** seconds |
| Truck arrival time | **45** seconds |
| Replicate seeds | **101–110**, ten per rate-duration combination |
| Simulation horizon | **600** ticks (1 tick = 1 second) |
| Traffic geometry | One eastbound lane; same position, following, entry, and exit rules as 3.2A |

For each **rate × seed** pair, the script executes one clear-lane baseline and then 30-, 60-, and 120-second obstructed scenarios. Duration **0** reuses the same baseline values as a paired zero-effect control; it is also rerun to assert exact agreement. In total: **40 baseline executions + 160 treatment/zero-duration executions = 200 NetLogo executions**, producing **160 paired CSV rows**. The underlying arrival and speed draws are checked for equality in each pair. This is *paired randomness*, not paired observed riders in real traffic.

Every run checks **requested = departed + on_lane + pending**. Zero-duration treatment results must exactly equal clear-lane baseline results. The model's `mean_queue` is the average of its end-of-tick waiting/pending count, not full vehicle travel delay. `mean_stop_completed_s` measures stopped seconds among **completed** riders only and is susceptible to endpoint selection differences; do not call it mean journey delay.

## Step A — run in NetLogo desktop

1. Keep working on Git branch `feat/netlogo-abm`. Extract the milestone ZIP at the repository root **with the model closed**, then reopen `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
2. From VS Code PowerShell, ensure the output directory exists: `New-Item -ItemType Directory -Force .\outputs | Out-Null`.
3. Stop the forever **go** button if it is active.
4. Click **Run sensitivity study** in the NetLogo interface, or run `run-sensitivity-study` from NetLogo's Command Center. It temporarily suppresses view updates; the model interface may appear unchanged during the batch. Follow progress messages in the Command Center.
5. Expect `PASS: wrote 160 paired sensitivity rows to ../outputs/netlogo_sensitivity_raw.csv`. The six original interface sliders are restored and the model reset afterward.

**Important:** The CSV is created by NetLogo itself. The Python Docker tests check the source structure and Python analysis code, **not** the NetLogo compiler/runtime. If NetLogo reports a compile/runtime error, stop and report the message before committing.

NetLogo uses the model's containing `netlogo/` folder for relative filenames in typical desktop use. If you changed the current NetLogo working directory, return to the model directory before running the procedure. The repository's `outputs/` directory is ignored by Git.

## Step B — aggregate, calculate 95% intervals, and plot

From the repository root, no local Python installation required:

```powershell
# Inspect raw NetLogo results:
Import-Csv .\outputs\netlogo_sensitivity_raw.csv | Select-Object -First 5 | Format-Table

# Analyze inside the existing Python Docker image (outputs volume is mounted):
docker compose run --build --rm simulation python -m cyclistics.netlogo_sensitivity --input /app/outputs/netlogo_sensitivity_raw.csv --output-dir /app/outputs

# Inspect mean paired effects (16 aggregated scenarios):
Import-Csv .\outputs\netlogo_sensitivity_summary.csv | Format-Table arrival_rate_per_hour,blockage_duration_s,avg_delta_mean_queue,ci95_low_delta_mean_queue,ci95_high_delta_mean_queue,avg_delta_peak_queue

# Open publication-friendly vector figures:
Start-Process .\outputs\netlogo_delta_mean_queue.svg
Start-Process .\outputs\netlogo_delta_peak_queue.svg
```

Local Python alternative (with the package installed, or `PYTHONPATH=src`):

```powershell
python -m cyclistics.netlogo_sensitivity --input outputs/netlogo_sensitivity_raw.csv --output-dir outputs
```

Outputs, all under `outputs/` and not committed:

- `netlogo_sensitivity_raw.csv` — **160 paired records** (one for each rate-duration-seed combination).
- `netlogo_sensitivity_summary.csv` — **16 grouped results**, means and sample standard deviations of *paired differences* plus **approximate**, two-sided **95% t intervals**.
- `netlogo_delta_mean_queue.svg` — vector chart: increase in average queue vs. obstruction duration, lines for all four rates, 95% intervals.
- `netlogo_delta_peak_queue.svg` — same for increase in maximum queue.

The Python analyzer rejects missing/duplicate combinations, non-finite numbers, mismatched deltas, failed conservation, unequal zero-duration baselines, inconsistent reused clear baselines, and false matched-input checks. Confidence intervals use a *t* critical value for **9 degrees of freedom** (`n=10` seeds, `2.262157`), and assume independent replicate seeds within each rate-duration scenario. These intervals are approximate (normality of replicate differences is not guaranteed) and describe stochastic simulation variability conditional on model assumptions; they do not quantify NYC observational uncertainty or general model validity.

## Interpret carefully

A positive delta in mean or peak queue means the blocked model produced more congestion than its clear-lane baseline for those same random draws. A negative delta in `departed` means fewer riders completed within the **fixed 600-second window**; it is not automatically a reduction in long-run capacity. A temporary queue can disappear by the end of the run while riders experienced significant intermediate delays.

**Not yet validated:** physical scaling (patches to meters, tick speed to observed cyclist velocity), lane geometry, distribution of arrivals, blockage behavior, and time-step convergence. DEVS-Suite operates as a single-server discrete-event queue; this NetLogo version models spatial interactions, so numerical agreement is not a requirement until we align their assumptions. No observations of individual NYC cyclists, collisions, or risk estimates are used here.

## CSC 754 connections / presentation defense

- **ABM:** cyclists are heterogeneous turtles with local following rules; moving space comprises NetLogo patches and continuous turtle coordinates.
- **Sensitivity:** change two independent parameters (demand rate and duration), plus 10 independent stochastic replications to assess robustness.
- **Controlled experiments:** same draws in treated/control pairs, zero-obstruction negative control, and equal-duration reproducibility checks.
- **Verification:** conservation, paired input equivalence, 160-row grid validation; these do not replace independent real-world validation.
- **Simulation time:** NetLogo uses fixed one-second global ticks, whereas the DEVS coordinator jumps between scheduled events.

Suggested paper caption: **“Synthetic NetLogo sensitivity study of queue response to temporary bicycle-lane obstruction (paired runs, 10 seeds per configuration; bars show 95% t intervals). Results represent simulated scenarios, not measured NYC effects.”**

### Recovery if NetLogo stops mid-batch

If a NetLogo runtime error interrupts the batch while view refresh is disabled, type `display` into the Command Center to restore it; then click **setup**. Do not analyze or commit a partially written CSV. Fix the model error and rerun the study.
