# Cyclistics v2 — offline replay, optional Roboflow and ArcGIS viewer

**Status:** The replay package, Roboflow response adapter and browser viewer are implemented separately; true live DEVS–NetLogo coupling and image-based proof of a blocked lane are not.

## 1. Test and export synthetic event fixture

From a VS Code PowerShell terminal in the repository root, after fetching and switching to the feature branch:

~~~powershell
git fetch origin
git status
git switch --track -c feat/v2-event-replay-and-vision origin/feat/v2-event-replay-and-vision
docker compose run --build --rm tests
docker compose run --build --rm simulation python -m cyclistics.v2_event_bridge --events /app/examples/v2_synthetic_replay_events.json --outdir /app/outputs/v2_replay
Get-Content .\outputs\v2_replay\netlogo_obstruction_events.csv
Get-Content .\outputs\v2_replay\replay_manifest.json
~~~

Use git switch on an existing local branch instead of attempting to create the same branch again. Check status before switching; preserve uncommitted work. The fixture is **synthetic**: block at simulated t=12, clear at t=20. The exporter records ordered, balanced events and hashes; the completed original NetLogo v1 is not overwritten.

## 2. Connect real optional Roboflow inference

Install the provider's optional inference SDK and configure your own API key outside GitHub:

~~~powershell
python -m pip install -e .
python -m pip install inference-sdk
$env:ROBOFLOW_API_KEY = '<your-own-private-key>'
python -m cyclistics.roboflow_adapter --image 'C:\path\to\your\frame.jpg' --model-id 'your-model/1' --observed-at-utc '2026-11-14T16:30:00Z' --frame-id 'actual-frame-01' --output outputs\v2_candidates.json
~~~

Replace the example timestamp, image path, and model ID with real values. The adapter accepts pixel-center bounding boxes plus image dimensions and emits normalized candidate observations. It **does not** confirm lane overlap. True observation-to-scenario conversion requires a manually reviewed segment, a confirmed lane-overlap flag, explicit human approval and a separately chosen simulation tick. Never commit frames or API secrets.

Reference: [Roboflow Inference SDK documentation](https://inference.roboflow.com/quickstart/roboflow_ecosystem/). Hosted inference depends on model availability, account access and API pricing.

## 3. Generate georeferenced scenario GeoJSON

The ArcGIS viewer accepts explicit WGS84 points only; it cannot infer NYC map coordinates from a NetLogo patch or synthetic example.

~~~powershell
docker compose run --rm simulation python -m cyclistics.v2_geojson --input /app/outputs/my_checked_locations.json --output /app/outputs/v2_map_scenarios.geojson
~~~

Each input record needs longitude, latitude, location_source, scenario_id, event_type, simulated_time_s, data_status, and mean_queue_cyclists. Data statuses are simulated or provisional_nyc_count; neither means a validated queue observation.

## 4. Open ArcGIS browser scenario viewer

~~~powershell
python -m http.server 8000 --directory web
~~~

Navigate to http://localhost:8000 and use Choose GeoJSON file to select the exported file. Filter by scenario and simulated time. ArcGIS Maps SDK 5.1 and an OpenStreetMap basemap load over the internet; hosted ArcGIS resources may require Esri authentication. The browser viewer consumes imported GeoJSON locally and does not create false street pins. GitHub CI checks JavaScript syntax and HTML wiring, **not** full cross-browser map rendering.

## 5. What is still separate

No real provided image/model was run during the software unit tests. The event bridge exports a deterministic **offline** schedule, not live inter-engine synchronization. Mixed motor traffic, cyclist merges, trajectory conflict measurement and Java/NetLogo event-consumption need separate implementation and verification. The verified v1 model and results remain intact.

**Course connection:** Source timestamps differ from simulation ticks; event schemas, deterministic replay, model interfaces and verification vs validation are explicit engineering choices.
