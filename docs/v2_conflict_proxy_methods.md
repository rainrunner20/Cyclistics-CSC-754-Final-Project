# Cyclistics v2 — trajectory-based conflict surrogates

**Implemented** in src/cyclistics/v2_conflicts.py, with synthetic software fixtures in tests/test_v2_conflicts.py. It accepts trajectory rows exported by the **separate experimental NetLogo v2 model**, not the verified v1 bike-only study.

## Run the analysis (from VS Code PowerShell)

~~~powershell
docker compose run --build --rm tests
docker compose run --build --rm simulation python -m cyclistics.v2_conflicts --input /app/outputs/v2_trajectories.csv --outdir /app/outputs/v2_conflicts
Get-Content .\outputs\v2_conflicts\summary.json
Get-Content .\outputs\v2_conflicts\conflict_manifest.json
~~~

The trajectory CSV must come from a **real run of netlogo/Cyclistics_Mixed_Traffic_v2.nlogo**. The table's schema is tick_s, type, agent_id, x_patch, lane_y, desired_speed_patches_per_tick, merged. Every row is validated, and backward-moving, duplicate or impossible lane/agent states are rejected.

## Two different indicators

**1. Time-to-collision-like closing-gap proxy:** For each 1-second simulated snapshot, find the nearest car behind a cyclist that has merged into motor lane y=2. If the car's *desired* speed exceeds the rider's, compute (longitudinal separation minus model following clearance) / positive speed difference. A value under 3 simulated seconds flags an **exposure snapshot**, not a physical collision or empirically measured near miss. It is vulnerable to using desired rather than actual instantaneous speed, idealized patch distances and 1-second sampling.

**2. PET-like same-point crossing gap:** For each car and merged cyclist whose consecutive positions cross the same x=6.5 model patch in lane y=2, linearly interpolate the passage times and report the absolute difference. Values below 2 simulated seconds flag small *temporal separation* at that point. This is **not a conventional post-encroachment time on real crossing trajectories**, and it should be called a PET-like or same-point passage-gap proxy only.

These indicators are intentionally distinct from collision counts and from the verified queue metrics of v1. There are no modeled injury outcomes, human observational benchmarks, or calibrated probability of a crash.

## Outputs and provenance

- summary.json: row and distinct-agent counts, thresholds, minimum defined TTC and crossing gap, events beneath the thresholds, transparent units and scientific caveats.
- conflict_manifest.json: SHA-256 of the original trajectory CSV and of the summary file; `field_validated` remains false.

## Real model execution evidence (synthetic traffic, not real observations)

[GitHub Actions run 43671124239](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671124239) executed the actual NetLogo 6.3.0 experimental model and analyzed its exported trajectory CSV, rather than calling the analyzer with unit-test fixtures. The source artifact is [v2 conflict proxy evidence](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671124239/artifacts/14144018478).

| Derived statistic | Measured in the synthetic v2 run |
| --- | ---: |
| CSV trajectory rows | 6,217 |
| Distinct simulated agents observed | 155 |
| TTC-like closing-gap snapshots under 3 s | 17 |
| Smallest modeled TTC-like value | 0.805 simulated s |
| Same-x passage gaps under 2 s | 4 |
| Minimum modeled same-x passage gap | 1.534 simulated s |

The experiment settings are a 300-tick horizon, attempted 900 cyclists/hour and 600 cars/hour, seed 754, a 120-s blockage beginning t=45, and cyclist merging enabled. **All values describe this one invented traffic model and this single seed, not observed NYC behavior.** The resulting conflict counts are *snapshot / passage-pair counts*, not distinct crashes or validated near misses. A different model calibration, threshold, movement policy or seed can change the totals.

Provenance: the GitHub manifest records input trajectory SHA-256 **44c703f4502213bb6979658459c8d7d180fb05c6217c861ef95ee5b9a8a7f50e** and summary JSON SHA-256 **4887cd80bdd1f934bc9005c453325fdfbe2cc35f391d3ae1c766530d5b3e1e1e**. These are GitHub-run-derived digests; retain the original artifact because run downloads expire.

## CSC 754 defense

The metrics demonstrate how model **state variables and agent motion** can produce secondary outcomes from trajectories; they are not DEVS event-count verification or real-world safety validation. The original v1 experiments remain the primary course evidence. An empirical traffic-safety study would need source geometry in meters, measured trajectories/velocities, ground-truth conflict labels and sensitivity to threshold definitions.
