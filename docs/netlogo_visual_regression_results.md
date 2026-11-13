# Cyclistics — NetLogo visual regression results (Milestone 3.6D–E)

## Goal

Improve the readability of the existing NetLogo single-lane obstruction simulation without changing the behavior being studied. This milestone is a **visualization update**, not a new movement model or a geographically measured NYC digital twin.

## Implementation

- The cyclist lane remains the center row (`pycor = 0`) with an eastbound, single-file following rule. Sidewalk and road patches are context only.
- `paint-street-background` paints a green bicycle lane, road separators, gray roadway, and sidewalk.
- `bike-lane-color` is reused during setup and when an obstruction clears so the highlighted patches return to green.
- Moving cyclists remain blue, stopped cyclists yellow, the blocking truck red, and the obstructed patch area orange.
- The original queue-over-time plot, sliders, experiment actions, seeded arrivals, speed draws, and CSV schema remain in place.

The NetLogo implementation is in `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`; its matching editable source is `netlogo/Cyclistics_Bike_Lane_ABM.nls`.

## Manual desktop verification — November 13, 2026

The updated model was opened in NetLogo and run to tick **600**. The displayed monitor values were:

| Monitor | Value |
| --- | ---: |
| Requested cyclists | 107 |
| Departed cyclists | 96 |
| Cyclists still on lane | 11 |
| Current waiting queue | 0 |
| Peak waiting queue | 21 |
| Mean stop time of departed cyclists | 8.09 s |
| Conservation check | true |

The screenshot supplied from the real NetLogo runtime shows the updated green lane and control interface at tick 600. **The truck is absent at tick 600 by design**: with a blockage starting at 45 s and lasting 65 s, the truck clears at 110 s. An additional active-obstruction screenshot can be captured later at a tick between 45 and 109.

## Baseline versus enhanced paired experiment

The original model was opened from a dedicated worktree on `feat/netlogo-abm`; the enhanced model ran from `feat/netlogo-visuals`.

Both used these input settings:

| Parameter | Value |
| --- | ---: |
| Arrival rate | 600 cyclists/hour |
| Blockage start | 45 s |
| Blockage duration | 65 s |
| Seed | 754 |
| Run length | 600 s |

Both executed the NetLogo `run-paired-experiment` action, which includes a clear control and a blocked treatment with matched arrival and individual desired-speed draws.

The recorded experiment output included:

| Metric | Clear | Blocked |
| --- | ---: | ---: |
| Requested cyclists | 107 | 107 |
| Departed | 96 | 96 |
| Peak queue | 1 | 21 |
| Mean queue | 0.022 | 1.317 |
| Mean completed-rider stop time | 0 s | 8.094 s |

The exported CSV files from the baseline and enhanced models were independently saved and compared using **SHA-256** in PowerShell. The hashes **matched exactly**. This confirms that the saved experiment results are byte-for-byte identical **for this tested scenario**.

The conservation monitor was also true: **107 requested = 96 departed + 11 still on lane + 0 pending** in the displayed run.

## Automated regression tests

After applying the street-rendering update, the user ran:

```powershell
docker compose run --build --rm tests
```

Result: **138 tests passed**. Seven visualization-specific source checks cover: source/model synchronization, original world geometry, centralized lane-color handling, reversible obstruction highlighting, the interface legend and existing plot, and unchanged experiment controls. These static tests are not a substitute for the manually executed desktop comparison above.

## Scope and limitations

- A passing single-seed regression and static checks do **not** prove all possible seeds, durations, or future NetLogo configurations are identical.
- NetLogo is an agent-based spatial model. Its completed-rider stop time is not interchangeable with Python DES waiting time.
- The screenshot and street layout are **NYC-inspired**, not geospatial measurements or a claim of validated traffic operations.
- No overtaking, second passable lane, vehicle behavior, pedestrians, traffic signals, crash prediction, or real-time sensor-to-simulation linkage was introduced.

## Reproduce

1. From the enhanced project root, run `docker compose run --build --rm tests`.
2. Open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` in NetLogo 6.3.0, set the parameters in the table above, and choose **Compare clear vs blocked** while the continuous **go** button is stopped.
3. Open the pre-visual baseline model from a worktree on `feat/netlogo-abm` and run the same paired experiment.
4. Check that each model writes `outputs/netlogo_paired_results.csv` in its own worktree; compare hashes using PowerShell `Get-FileHash -Algorithm SHA256`.
5. Keep the output files, external JARs, and locally generated benchmark results out of Git. Commit only source, tests, research documentation, and genuine screenshots.

**CSC 754 relevance:** NetLogo patches define the spatial environment, cyclists are autonomous agents with local movement rules, and ticks implement a simulation clock. The before/after paired experiment is a verification regression demonstrating that a presentation-only change did not alter the observed model outputs for a controlled case. It does not validate simulated delays against observed NYC traffic.
