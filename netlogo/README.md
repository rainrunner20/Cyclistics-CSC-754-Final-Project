# Cyclistics — NetLogo ABM (Milestone 3.1A)

**A visual, stand-alone NetLogo model of bicycle-lane obstructions.** It adds agent-based modeling to the existing Python and DEVS-Suite work without replacing or changing them.

## Open it on Windows

1. Download NetLogo from https://www.netlogo.org/downloads/ (NetLogo 7.x is fine).
2. Open NetLogo, choose **File → Open**, and select `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
3. If NetLogo 7 offers to convert the older `.nlogo` file into `.nlogox`, accept and **save the converted model under `netlogo/`**. NetLogo 6.4 can open the `.nlogo` directly.
4. Click **setup** then **go** (the go button repeats until you click it again or the `run-length` limit is reached).
5. To compare the same synthetic demand stream, keep **seed-value** fixed and change `blockage-enabled` between 0 (clear) and 1 (truck present). Click setup between runs. A rate of 600 cyclists/hour creates an average of 1 attempted arrival per 6 seconds. Arrival draws are sampled at setup, so demand remains the same across the two settings; individual speeds may still differ after a queue changes when agents enter.

**Colors:** blue bicycle = moving, yellow bicycle = stopped, red truck and orange patches = obstructed segment. Dark grey = off-lane patches; cyan = lane.

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

**Do not compare the numerical results with Java DEVS yet.** NetLogo models 1D spatial motion, speed heterogeneity, and entrance backlogs. Java DEVS currently models a single bottleneck with a fixed service headway. These are **different assumptions**. We will align scenarios for validation in a later milestone.

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
- `tests/test_netlogo_model_structure.py` — repository integrity tests **only**. They do not execute or compile NetLogo code.
- `Dockerfile` + `.dockerignore` — copy the NetLogo source into our existing **Python test image** so those six static tests run with `docker compose run --build --rm tests`. This does not install NetLogo in Docker.

**Known test limitation:** This package was statically checked locally, but it has **not been executed in the NetLogo desktop runtime**. Please open it and check the setup/go buttons before committing. If NetLogo reports a compile error, share the error message and we will correct it.
