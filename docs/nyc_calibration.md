# NYC bicycle counts -> simulation inputs (Milestone 1.2)

This is a **calibration of an arrival-rate parameter**, not validation of Cyclistics as a traffic predictor. We take measurements from **one** counter and **one** measurement stream, calculate a mean rate, and use that rate to create **synthetic Poisson arrivals** in the Python reference simulation.

Why one stream? A counter can report directional flows, totals, different travel modes, and different time resolutions. Adding them together without inspecting their meaning may double-count cyclists.

## Quick offline demo (no API access required)

Run these commands from the repository root. The fixture is explicitly **synthetic** and is committed under `tests/fixtures/` for reproducible learning.

```powershell
docker compose run --build --rm tests

docker compose run --rm simulation python -m cyclistics.nyc_calibration inspect --input /app/tests/fixtures/synthetic_hourly_counts.json

docker compose run --rm simulation python -m cyclistics.nyc_calibration calibrate --input /app/tests/fixtures/synthetic_hourly_counts.json --sensor-id demo-sensor --mode Bicycle --granularity Hour --interval-minutes 60 --output /app/outputs/demo_calibration.json

docker compose run --rm simulation python -m cyclistics --calibration /app/outputs/demo_calibration.json --output-dir /app/outputs --seed 754
```

Expected in this demo: `(240 + 360 + 300 + 300) / 4 hours = 300 cyclists/hour`. **The fixture is not NYC field data.** The simulation still generates individual cyclist arrivals at random from this mean.

## Live NYC workflow

### 1. List sensor IDs

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_open_data --dataset sensors --limit 100 --output /app/outputs/nyc_sensors.json
docker compose run --rm simulation python -m cyclistics.nyc_calibration sensors --input /app/outputs/nyc_sensors.json
```

Select a sensor that actually measures bicycles and has observations for the chosen time window. Copy the exact ID printed by the tool.

### 2. Fetch a *bounded* window for that sensor

Replace `REPLACE_WITH_SENSOR_ID` with the sensor ID you selected. These timestamps are examples to modify after inspecting the sensor's available dates.

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_calibration fetch --sensor-id "REPLACE_WITH_SENSOR_ID" --start "2026-10-15T08:00:00" --end "2026-10-15T12:00:00" --output /app/outputs/nyc_count_window.json
```

The API request filters by sensor and time, uses bounded pagination, and stops rather than silently truncating records. Increase `--max-records` if necessary (maximum 10000) or use a shorter time window.

The dataset uses local floating timestamps. Start with a single day **away from daylight-saving-time clock changes** so the time intervals aren't ambiguous.

### 3. Inspect before calibrating

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_calibration inspect --input /app/outputs/nyc_count_window.json
```

The printed groups contain `sensor_id | travelmode | granularity | direction | flowid | status`. Copy the **exact** mode and granularity value shown. The code does not assume they will literally be `Bicycle` and `Hour`.

Cross-check what the chosen `granularity` and `status` values mean in the official NYC data dictionary. **Do not treat every status code as verified quality data.** The calibration script intentionally refuses to mix stream/status combinations.

### 4. Calibrate one stream

Use your selected ID and the *actual* group values from the previous step. The values below (`Bicycle`, `Hour`) are placeholders until confirmed by `inspect`. Change `--interval-minutes` to the correct duration (for example, `15` for 15-minute intervals). Optionally add `--direction`, `--flow-id` and/or `--status` when there are multiple groups.

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_calibration calibrate --input /app/outputs/nyc_count_window.json --sensor-id "REPLACE_WITH_SENSOR_ID" --mode "Bicycle" --granularity "Hour" --interval-minutes 60 --output /app/outputs/nyc_calibration.json
```

If the tool complains about multiple streams, use the inspection output and select exactly one stream, e.g. add `--direction "..." --flow-id "..." --status "..."` using the actual values.

If it complains about missing intervals, select a shorter consecutive window. Do not simply assume the gaps represent zero cyclists. Sensor downtime and gaps are possible.

### 5. Run data-informed scenarios

```powershell
docker compose run --rm simulation python -m cyclistics --calibration /app/outputs/nyc_calibration.json --seed 754 --output-dir /app/outputs
```

Inspect `outputs/nyc_calibration.json`, `outputs/simulation_inputs.json` and `outputs/scenario_metrics.csv`. The calibration JSON includes a source-file SHA-256 fingerprint so experiments can be linked to the exact input snapshot. Those generated files are intentionally gitignored. Record the sensor ID, time range, status interpretation, interval assumption, seed, and any exclusions in your development journal.

## Why this matters academically

- **Data-informed parameterization:** set the mean cyclist arrival rate from measurements rather than guessing `300/hour`.
- **Stochastic simulation:** the arrival generator still samples exponential inter-arrival times using the fitted mean rate.
- **Verification:** unit tests check no mixed flows, missing intervals, duplicate timestamps, bad count values, and bad metadata.
- **Validation still pending:** we have not shown that observed queue lengths, behaviors, or delays match real NYC conditions. This would need independent field observations.
- **Sensitivity analysis:** use multiple representative observation windows and compare results at different arrival rates; a single four-hour sample is not an uncertainty analysis.

## ELI5 code tour

1. `build_window_url()`: asks NYC for records belonging to one sensor within a time range. Like requesting a few relevant pages of a very large library catalog.
2. `fetch_window()`: retrieves those pages while refusing to quietly omit records. Like checking that you collected all the pages you asked for.
3. `inspect_counts()`: lists measurement streams so you can make an informed selection rather than mixing things together.
4. `calibrate()`: sums counts from a contiguous set of equally-sized measurement intervals and divides by total observed hours.
5. `--calibration`: passes the estimated mean into the existing simulator without mixing API code into the simulation engine.

### Small exercise (do this yourself)

Change the **synthetic** fixture's second count from `360` to `240`, rerun the offline calibration and compute the new expected rate yourself. Don't change the fixture permanently unless you intend to update its unit test; use a temporary copy in `outputs/` to experiment.

## Sources and limitations

- Dataset: <https://data.cityofnewyork.us/Transportation/Bicycle-and-Pedestrian-Counts/ct66-47at>
- Counter metadata: <https://data.cityofnewyork.us/Transportation/Bicycle-and-Pedestrian-Count-Sensors/6up2-gnw8>
- NYC API overview: <https://www.nyc.gov/opendata/get-started/user-guides/open-data-apis>

The count data may have gaps due to transmission or equipment issues. The dataset's timestamp is published as local floating time. This first implementation is intentionally strict: a single contiguous stream with an explicit interval duration. Broader seasonal/weekday modeling, data-quality filtering, and uncertainty analysis belong in later milestones.
