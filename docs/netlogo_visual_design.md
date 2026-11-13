# Cyclistics — Milestone 3.6A: NYC-inspired NetLogo visualization

**Status:** Implemented, desktop-tested and verified on one controlled paired experiment (November 13, 2026)
**CSC 754:** NetLogo agent-based modeling, patch-based environments, experimental control, verification
**Starting point:** `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` on `feat/netlogo-abm` after PR #3

## Goal

Make the single-lane bicycle obstruction experiment easy to understand during a live demo, using the clear environment layout and visual feedback of a well-designed NetLogo simulation. This is **not** a geographically accurate reconstruction of Prospect Park West.

## What already works

- A single eastbound bicycle path uses `pycor = 0`; all cyclist agents remain on that row.
- Blue cyclists move normally; yellow cyclists have stopped; a red truck occupies the obstruction zone.
- Orange patches show the active obstruction at `pxcor = 6` and `7`.
- Sliders control arrivals, blockage, seed, and run length; monitors show demand, queues, departures, mean stop time, and conservation.
- The Interface already includes a **Queue length over time** plot. Do not add a duplicate.
- `run-paired-experiment`, sensitivity analysis, verification checks, and benchmarks are already implemented.

## Design decision: change presentation without changing the model

The first visual milestone is **cosmetic only**. Keep the existing agent motion, patch-world dimensions (`pxcor = -16..16`, `pycor = -4..4`), obstruction timing, arrival draws, and experiment CSV format unchanged.

Suggested stylized visual layers (final palette to be checked in NetLogo):

| NetLogo row | Visual role | Modeling role |
| --- | --- | --- |
| `pycor = 0` | High-contrast NYC-style green bicycle lane | **Only row used for cyclist motion** |
| `abs pycor = 1` | Painted separation/buffer or curb edge | Visual boundary, not passable space |
| `pycor = 2..4` | Gray adjacent roadway, dashed marking accent | Background illustration, **not modeled vehicle traffic** |
| `pycor = -2..-4` | Sidewalk / streetscape tones | Background illustration, **not modeled pedestrians** |
| `pxcor = 6..7, pycor = 0` | Orange obstruction highlight while truck is present | Existing blockage state; restore green on clearance |

Maintain a consistent layering order: **street patches → obstruction highlight → truck/cyclists**. Restoring the obstruction zone must restore the new lane color, not the old sky-blue color.

## Interface enhancements

1. Keep the current queue-length plot; consider renaming its axis/legend for readability if that does not change data collection.
2. Add a compact legend explaining blue = moving, yellow = stopped, red = truck, orange = blocked zone.
3. Give the plot and controls some breathing room; ensure the full world remains visible.
4. Consider adding a separate cumulative-departures plot *later*, with no change to the existing experiment files.
5. Capture a genuine NetLogo screenshot only after visually inspecting the running model; do not create a mock-up and present it as a runtime screenshot.

## Explicit non-goals (3.6A/3.6B)

- No second passable lane, lane changing, overtaking, traffic signals, pedestrians, or vehicle AI yet.
- No claims that the diagram matches a measured NYC lane width, curb configuration, or sensor location.
- No changes to cyclist speed distributions, collision rules, queue definitions, or random sequences.
- No GIS, live computer vision, or real-time DEVS–NetLogo coupling.

Those could be separately designed and tested in future behavioral milestones, while preserving the original single-lane baseline.

**Verification record:** [NetLogo visual regression results](netlogo_visual_regression_results.md) documents the 138 passing tests, real NetLogo desktop run and byte-identical baseline/enhanced CSV export for the tested scenario. An active-obstruction screenshot is an optional follow-up.

## Implementation sequence

- **3.6A design:** document existing behavior, visual palette, and scientific boundaries (this file).
- **3.6B tests:** add checks that the street renderer preserves `pycor = 0`, the blockage switches/restores the correct color, and `.nls` matches the embedded `.nlogo` source; do not treat source inspection as a substitute for running NetLogo.
- **3.6C visuals:** refactor static patch painting into an explicit helper, change background colors, make the obstruction highlight reversible, and add a simple UI legend. Keep model outputs identical for identical inputs.
- **3.6D manual verification:** open NetLogo, run clear and blocked demonstrations, compare CSV results against the previous baseline, capture an actual screenshot, and document any GUI limitations.

## Acceptance criteria

1. The model still loads in the supported NetLogo 6.3.0 environment and runs `setup`, `go`, and `run-paired-experiment`.
2. The world geometry and all agent movement rules remain unchanged; cyclists still use `ycor = 0`.
3. Blockage begins and ends at the same ticks as before; the highlight clears to the lane's **new** background color.
4. Seeded clear/blocked scenario metrics and exported CSV schema remain unchanged (regression check).
5. All existing Python-side tests pass; the NetLogo desktop is also checked manually, since these tests do not fully execute its GUI.
6. Updated documentation accurately says this is an **NYC-inspired schematic**, not a field-validated street digital twin.

## Presentation explanation (ELI5)

> The green corridor represents a bicycle lane. Each bicycle is an agent following simple local movement rules. A truck obstructs the corridor at a scheduled time, which can create a queue. The surrounding road and sidewalk make the model easier to read, but the first version still simulates movement in only one lane. We're changing how it looks without changing how its experiments work.

**CSC 754 concept:** The patches define the agent environment; the turtles implement agent state and local rules; ticks provide the simulation clock. Separating visualization from transition logic helps verify that presentation changes do not change scientific results.
