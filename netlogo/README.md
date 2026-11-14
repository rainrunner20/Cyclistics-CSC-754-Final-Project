# Cyclistics — NetLogo ABM (Milestone 3.1A)

**A visual, stand-alone NetLogo model of bicycle-lane obstructions.** It adds agent-based modeling to the existing Python and DEVS-Suite work without replacing or changing them.

## Open it on Windows

1. Install **NetLogo 6.3.0**, the desktop version used for the verified GUI run. Other versions may require compatibility checks.
2. Open NetLogo, choose **File → Open**, and select `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
3. Open the existing `.nlogo` model directly; do not overwrite the tracked source with a converted format during the reproducibility run.
4. Click **setup** then **go** (the go button repeats until you click it again or the `run-length` limit is reached).
5. For a controlled paired comparison, set the arrival rate, seed and obstruction timing, stop the forever **go** button, then click **Compare clear vs blocked**. The model pre-samples both arrival draws and individual desired-speed draws, keeping them matched between runs. At 600 cyclists/hour, expected arrivals average one every 6 seconds.

**Colors:** blue bicycle = moving, yellow bicycle = stopped, red truck = blocking vehicle, orange patches = active obstruction. The **green** row is the only simulated bicycle lane; gray roadway and sidewalk patches are decorative.

## Main controls and metrics

| Parameter | Default | Meaning |
| --- | ---: | --- |
| `arrival-rate-per-hour` | 600 | Bernoulli arrival demand; synthetic, not automatically NYC data |
| `blockage-enabled` | 1 | 0 for no truck; 1 for blockage |
| `blockage-start` | 45 | Truck arrival in simulated seconds |
| `blockage-duration` | 65 | Number of seconds occupied |
| `seed-value` | 754 | Fixes NetLogo random sequence for reproducibility |
| `run-length` | 600 | Stop after this many 1-second ticks |

The monitors show demand, riders on lane, queue, completions, peak queue, mean *fully stopped seconds per departed rider*, and a cyclist-conservation check. Queue includes riders stalled at the entry.

**Do not interpret NetLogo metrics as numerically interchangeable with Java/Python.** NetLogo models spatial motion, speed heterogeneity and entrance backlogs; Java DEVS models a scheduled service bottleneck with a fixed service headway. Python and Java agree for a separate two-cyclist deterministic fixture, whereas NetLogo has its own paired clear/blocked consistency checks. These do not constitute field validation.

## CSC 754 explanation (simple)

- **ABM:** Every bicycle is a *turtle agent* with its own speed, stop time, and local interaction rule.
- **Space / cellular representation:** The street background consists of *patches*; cyclists move in continuous NetLogo turtle coordinates along a one-dimensional lane.
- **Time step vs DEVS:** NetLogo advances one global tick each second. The DEVS simulation schedules jumps to the next event time.
- **Emergence:** No rule tells cyclists to make a queue. Queues arise because each rider follows the rider ahead and respects the stop line when a truck blocks the lane.
- **Verification:** `conservation-ok?` checks demand = departed + currently cycling + waiting to enter. This is not external real-world validation.

## Scope limitations

Single lane; no passing, conflict or collision risk inference; no pedestrian or vehicle intersection; no CV model; no live NYC data feed; no Java–NetLogo synchronization. The `free-speed` is measured in model patches per second, not calibrated physical velocity. Report metrics as synthetic simulated outcomes only.

## Files in this milestone

- `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` — ready-to-open traditional NetLogo model (also opens in NetLogo 7 with conversion).
- `netlogo/Cyclistics_Bike_Lane_ABM.nls` — the NetLogo Code tab source as a fallback/reference.
- `docs/netlogo_milestone_3_1a.md` — development notes and research boundaries.
- `tests/test_netlogo_model_structure.py` and related source-level tests — repository integrity checks; they do not execute the NetLogo GUI.
- `Dockerfile` + `.dockerignore` — include NetLogo source files in the Python test image for structural checks. This does not install NetLogo itself.

**Verified desktop checkpoint (November 13, 2026):** The upgraded model executed through 600 simulated seconds in NetLogo 6.3.0. A paired baseline-versus-visualization regression with seed 754 produced byte-identical exported CSV files; see [verification results](../docs/netlogo_visual_regression_results.md). This is one controlled case, not exhaustive behavioral equivalence or NYC field validation.
