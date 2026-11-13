# Cyclistics — Milestone 3.2A: controlled NetLogo experiments

## Goal

Run two comparable, synthetic agent-based scenarios **without manually copying monitor values**:

- **Clear**: no delivery-truck obstruction.
- **Blocked**: the same arrival demand and individual desired-speed draws, with a truck present from `blockage-start` for `blockage-duration` seconds.

The scenario pair uses the exact same `seed-value`, `arrival-rate-per-hour`, and `run-length`. Desired speeds are drawn in `setup` and assigned in arrival/admission order, removing a confound caused by scenario-specific random-number consumption. This is **paired simulation input**, not empirical validation of urban behavior.

## Run in NetLogo GUI

1. Open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
2. Keep defaults initially: arrival rate **600 cyclists/hour**, start **45 s**, duration **65 s**, seed **754**, horizon **600 s**.
3. **Stop** the forever `go` button if running.
4. Click **Compare clear vs blocked**, or enter `run-paired-experiment` in the Command Center.
5. The command automatically runs clear then blocked, prints both summaries, and saves a two-row CSV at `outputs/netlogo_paired_results.csv` from the repository root. It restores the `blockage-enabled` slider setting afterward. The final picture and queue plot show the blocked case because it runs last.
6. Inspect the result in Windows PowerShell, from the repository root:

   ```powershell
   Import-Csv .\outputs\netlogo_paired_results.csv | Format-Table scenario,requested,departed,peak_queue,mean_queue,mean_stop_completed_s
   ```

**Prerequisite:** the repository's `outputs/` directory must exist (`New-Item -ItemType Directory -Force .\outputs | Out-Null` if needed). By default, NetLogo uses the model's `netlogo/` directory as the working directory; the relative `../outputs/` path therefore targets the repository root. If you have deliberately changed NetLogo's current directory, restore it before running the export.

## CSV columns

- `scenario`, `blockage_enabled`: control or treatment indicator.
- `seed`, `arrival_rate_per_hour`, `blockage_start_s`, `blockage_duration_s`, `run_length_s`: reproduction settings.
- `requested`, `departed`, `on_lane`, `pending`: cyclist accounting. Each row must satisfy `requested = departed + on_lane + pending`.
- `peak_queue`: largest end-of-tick number of fully stopped cyclists plus cyclists waiting to enter.
- `mean_queue`: average end-of-tick queue count across all simulated seconds, the cumulative queue count divided by ticks.
- `mean_stop_completed_s`: average whole stopped seconds **among riders who have departed**, not all riders; interpret cautiously when end-of-horizon active rider counts differ.
- `conservation_ok`: per-run bookkeeping identity.

Both rows must have identical requested demand. The code also directly asserts equality of the full underlying arrival draw list and pre-sampled desired speed list. Cyclists are still heterogeneous; each arrival is assigned its own target speed, but the same individual gets the same assigned speed across the two scenarios.

## CSC 754 relationship

**ABM:** NetLogo turtles with independent desired speeds and local following rules. **Experiment design:** controlled independent-variable intervention (obstruction on/off) while holding random inputs constant. **Verification:** pre-specified invariants, matched inputs, and conservation checks. **Metrics:** throughput, instantaneous/peak/mean congestion, stopped time. **Validation (not done):** compare patterns and calibration against observed NYC data. **DEVS comparison (not done):** current NetLogo continuous movement at one-second ticks is not yet behaviorally equivalent to the Java single-server DEVS lane.

## Follow-up

Run the A/B experiment across several seeds, rates and blockage durations; compute variability and confidence intervals before claiming robust effects. Record NetLogo version and commit hash for reproducibility. Do not interpret the two-row test as causal evidence from NYC streets.

The Python Docker tests are **structural**, not a NetLogo engine execution. Opening the `.nlogo` model and running the button are still required to verify NetLogo runtime behavior and file export.
