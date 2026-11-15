# Cyclistics v2 — reproducible end-to-end **offline** demo

This is an integration of **actual code execution** rather than fabricated traffic observations. GitHub Actions converts an explicitly synthetic, manually pre-reviewed mock observation into a versioned obstruction schedule; Java parses that CSV; the real NetLogo 6.3.0 model imports it and simulates cars/cyclists; the Python analyzer then computes TTC and crossing-time-gap surrogate metrics from actual NetLogo-produced trajectory rows. ArcGIS receives no invented geographic pin.

## Run the same pipeline locally

~~~powershell
git status
git fetch origin
git switch --track -c feat/v2-end-to-end-replay origin/feat/v2-end-to-end-replay
docker compose run --build --rm tests
docker compose run --build --rm simulation python -m cyclistics.v2_demo --input /app/examples/v2_synthetic_reviewed_observation.json --approve-synthetic --outdir /app/outputs/v2_demo
Get-Content .\outputs\v2_demo\netlogo_obstruction_events.csv
~~~

Then open netlogo/Cyclistics_Mixed_Traffic_v2.nlogo in NetLogo 6.3.0 and enter at its Command Center:

~~~text
run-v2-replay "../outputs/v2_demo/netlogo_obstruction_events.csv"
~~~

The validation workflow additionally saves a trajectory CSV using BehaviorSpace and checks an **exact 8-tick truck obstruction** from t=12 (inclusive) to t=20 (exclusive). The incident at t=12 was not observed in any video; it is a deliberately hypothetical input approved only for the software demo.

With a saved trajectory CSV, run:

~~~powershell
docker compose run --rm simulation python -m cyclistics.v2_conflicts --input /app/outputs/v2_demo/v2_replay_trajectories.csv --outdir /app/outputs/v2_demo/conflict_analysis
Get-Content .\outputs\v2_demo\conflict_analysis\summary.json
~~~

## Actual boundaries of integration

- **Python:** writes candidate observation metadata, an explicitly approved synthetic obstruction schedule, and conflict summaries.
- **Java:** independent strict event CSV parsing is tested with actual Python output; the new real DEVS-Suite replay runner needs a locally provided external JAR to demonstrate coordinator execution.
- **NetLogo:** genuine headless v2 reads the exact Python-generated schedule and runs car/cyclist movement. It is an offline batch run, not a continuously synchronized simulation clock.
- **ArcGIS:** the map viewer can load explicitly georeferenced scenario GeoJSON, but the synthetic fixture has **no physical NYC coordinates**. Its GeoJSON export is intentionally empty. Adding a marker requires checking a real WGS84 location, not assigning a NetLogo patch to Brooklyn.
- **Computer vision:** Roboflow adapter code supports an actual model and user-supplied image, but the integrated CI uses only a transparent synthetic candidate; no cloud inference is claimed.

## What counts as successful evidence

The CI output needs: event bridge manifest, Java parser pass, real NetLogo conservation/spacing pass and exactly 8 blocked ticks, trajectory CSV, conflict-proxy summary, and SHA-256 manifest. None of these establish crash probability, city-specific queue accuracy, image detection quality or live multi-engine coordination.

This is an excellent CSC 754 discussion of **atomic versus agent-based clocks, event replay, external input schedules, state transitions, coupling boundaries, verification, sensitivity, and validation limits**.
