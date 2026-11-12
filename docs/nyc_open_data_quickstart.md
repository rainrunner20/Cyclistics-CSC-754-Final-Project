# NYC Open Data — API ingestion, first milestone

## Goal

Retrieve **small, read-only samples** from NYC DOT's public Socrata API and store
raw source metadata along with the observations. This is **not calibration yet**.

Datasets:

- Bicycle and Pedestrian Counts: `ct66-47at` (large, includes different travel modes and granularities)
- Bicycle and Pedestrian Count Sensors: `6up2-gnw8` (sensor metadata)

## Run from the repository root

The existing Docker Compose `simulation` service mounts `./outputs` to `/app/outputs`.
The following command uses the **same Docker image** but runs the new ingestion module:

```powershell
# Sensor metadata sample
docker compose run --build --rm simulation python -m cyclistics.nyc_open_data --dataset sensors --limit 5 --output /app/outputs/nyc_sensors_sample.json

# Observation sample (may contain pedestrian records too)
docker compose run --rm simulation python -m cyclistics.nyc_open_data --dataset counts --limit 5 --output /app/outputs/nyc_counts_sample.json

# Offline tests — no internet required
docker compose run --rm tests

# See downloaded results on Windows
Get-Content .\outputs\nyc_sensors_sample.json | Select-Object -First 40
```

If the two `.json` files appear under `outputs/`, the API ingestion proof-of-concept worked.
`outputs/` is gitignored: do not commit downloaded records to Git.

## API and implementation

- HTTP GET over HTTPS; JSON serialization
- dataset-ID allowlist; bounded limits (`1..1000` rows)
- optional `SOCRATA_APP_TOKEN` environment variable, sent as an `X-App-Token` header
- 20-second request timeout; up to two retries on transient errors
- minimal response-shape and count validation
- provenance: dataset ID, retrieval timestamp (UTC), request URL
- standard-library-only implementation, deterministic offline unit tests

## Caveats before calibration

The counts dataset contains multiple travel modes, directions, flow IDs, time
resolutions, and status values. It is **not safe** to sum arbitrary sample rows
or infer a bicycle arrival rate from the latest five observations. A later
milestone must select a specific bicycle-capable sensor and a single compatible
flow and granularity, handle quality/status flags, account for measurement
gaps, document units, and average over a justified time window. Timestamp
metadata describes EST; time zones/DST need explicit attention.

This milestone is independently valuable: we have a testable external-data
connector without pretending the simulator is already field-calibrated.

Sources:
- https://data.cityofnewyork.us/d/ct66-47at
- https://data.cityofnewyork.us/d/6up2-gnw8
- https://dev.socrata.com/docs/queries/limit
