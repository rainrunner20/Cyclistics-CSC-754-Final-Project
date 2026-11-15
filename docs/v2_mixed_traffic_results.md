# Cyclistics v2 — experimental mixed traffic and cyclist lane changes

**Implemented:** A separate runnable NetLogo 6.3.0 model at netlogo/Cyclistics_Mixed_Traffic_v2.nlogo. The original verified one-lane model, its 160 paired sensitivity records, and its source hash are unchanged.

## What is actually modeled

- **Two lanes:** green bicycle lane y=0 and adjacent motor lane y=2, in schematic NetLogo patches rather than georeferenced meters.
- **Two agent types:** cyclist and car arrivals are independently sampled at the corresponding hourly sliders, and separate counters track generated, queued, present and departed agents.
- **Obstruction:** a truck blocks new bicycle-lane entry past x=5 during the selected interval. Riders that passed the stop line before the blockage may finish.
- **Merge/return:** a cyclist near x=2..5 may enter the car lane if its longitudinal gap to nearby traffic exceeds 3 patches. After passing x=9, it may return to the bike lane if there is enough space.
- **Car following:** cars in the motor lane follow one another and any merged cyclist with a 1.1-patch model headway.
- **Measurement:** both populations are checked for conservation at every tick, same-lane separation for at least 0.75 patches, deterministic seeded draws, queue lengths, merge/return events and simulated trajectory CSV.
- **Surrogate conflicts:** the model computes a closing-gap TTC-like estimate for a car behind a merged cyclist. A 'potential conflict tick' only means that this model-specific value fell below 3 simulated seconds. It is **not a measured near miss, an actual car crash or a validated TTC predictor**.

## Actual GitHub-hosted NetLogo execution

GitHub Actions run [43670733798](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43670733798) passed with **official NetLogo 6.3.0 headless**. The resulting artifact contains two traffic scenarios, a replay verification case, the original NetLogo trajectory export and model metrics. These numbers are **simulation outputs**, not NYC observations.

| Scenario (seed 754, 300 ticks) | Bike arrivals | Car arrivals | Bike departures | Car departures | Merges | TTC proxy ticks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Merge disabled | 94 | 61 | 73 | 57 | 0 | 0 |
| Merge enabled | 94 | 61 | 84 | 57 | 23 | 17 |

The two cases set 900 attempted cyclists/hour, 600 attempted cars/hour, truck start 45 s, duration 120 s and identical random seed 754. Twenty of the 23 merges had returned to the bicycle lane within the run; the remaining riders were still active or had reached the model boundary. The merging-enabled case's minimum model TTC proxy was about **0.805 s**; this is a small schematic gap under assumed speeds, not an empirical collision probability.

**Verification:** Cyclist and car conservation, non-overlapping same-lane spacing, source compilation, experimental export and full headless execution passed. The separate replay fixture imported `time_s,event_type` rows from netlogo/fixtures/v2_synthetic_obstruction.csv and observed the obstruction active for exactly **8 simulated ticks** (t=12 through t=19). This is an offline replay, not synchronized real-time Java coordination.

## Reproduce on Windows (PowerShell)

~~~powershell
git status
git fetch origin
git switch --track -c feat/experimental-mixed-traffic origin/feat/experimental-mixed-traffic
docker compose run --build --rm tests
~~~

Open netlogo/Cyclistics_Mixed_Traffic_v2.nlogo in NetLogo 6.3.0, set the car rate and merging-enabled sliders, and click setup/go to watch individual movement. Click Verify mixed traffic to check the full run, or Run v2 experiment to export:

- outputs/v2_metrics.csv — scenario controls and counts, merges, queue and TTC proxy summaries
- outputs/v2_trajectories.csv — per-tick positions in schematic patches, lane IDs, agent IDs and desired speeds

From the NetLogo Command Center, the CSV bridge can be replayed using a file path relative to the netlogo directory:

~~~text
run-v2-replay "fixtures/v2_synthetic_obstruction.csv"
~~~

Run v2 experiments *on this separate model*. Don't use the old v1 sensitivity/paper intervals to characterize this multi-lane behavior: adding a motor lane and merges changes the assumptions.

## Limits and future work

Vehicle speed and gaps are rule-based and schematic; there is no verified NYC driver calibration, true geometric bike-lane width, collision dynamics, traffic light, motor-vehicle trajectory ground truth, emergency braking, or empirically estimated crash probability. The geographic ArcGIS viewer needs explicitly supplied WGS84 coordinates, and a live camera event must be reviewed before it affects a scenario. Better validation and broader parameter sweeps are necessary before any safety conclusions.

**CSC 754:** NetLogo ABM, two coupled-looking but locally interacting agent populations, fixed-tick simulation clock, experimental control, seeded replay, collision-free state constraints and internal verification. It is *not* a DEVS coupled model; Java DEVS-Suite atomic components remain separate.
