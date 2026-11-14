# Cyclistics milestone 3.3B — NYC-informed NetLogo arrivals

## What changes

This adds a **reproducible bridge**, not a new traffic prediction model. It takes the repository's existing `cyclistics.arrival-rate.v1` JSON, preserves the selected sensor/flow/direction, and exports one numeric CSV cell for the current NetLogo model's `arrival-rate-per-hour` slider. The existing NetLogo model already has the `csv` extension, so it needs **no code changes**. The bridge verifies the two-row ABM experimental export used the selected rate and retains provenance in a separate JSON report.

**Important:** This calibrates a *mean cyclist demand input*. Arrivals, speeds, queueing and effects of lane obstructions are still simulated, not observed NYC outcomes. Verify the chosen flow, counter status, timezone and interval semantics using the official data dictionary. This does not establish predictive validation.

## Step 1 — Tests and sample data (no network required)

From the repo root in VS Code PowerShell:

```powershell
git branch --show-current
Expand-Archive -LiteralPath "$HOME\Downloads\cyclistics-milestone-3-3b-nyc-netlogo-calibration.zip" -DestinationPath . -Force
docker compose run --build --rm tests
```

The repo already contains an explicitly **synthetic** fixture. To test the bridge without pretending it is observed city data:

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_calibration calibrate --input /app/tests/fixtures/synthetic_hourly_counts.json --sensor-id demo-sensor --mode Bicycle --granularity Hour --interval-minutes 60 --output /app/outputs/demo_rate.json

docker compose run --rm simulation python -m cyclistics.netlogo_calibration_bridge prepare --calibration /app/outputs/demo_rate.json --output-dir /app/outputs --allow-synthetic

Get-Content .\outputs\netlogo_calibration_commands.txt
```

Smoke-test expected rate: **300 cyclists/hour**. The metadata explicitly labels it `synthetic_fixture`.

## Step 2 — Run an actual NYC bicycle-count calibration

Our existing data pipeline has the live-fetch commands. You need to choose a *specific* bicycle counter, one measurement stream, and a contiguous period with actual records. Do not invent a sensor ID.

```powershell
# Request a bounded list of official counter metadata (requires Docker internet access).
docker compose run --rm simulation python -m cyclistics.nyc_open_data --dataset sensors --limit 1000 --output /app/outputs/nyc_sensors_sample.json

docker compose run --rm simulation python -m cyclistics.nyc_calibration sensors --input /app/outputs/nyc_sensors_sample.json
```

Choose one listed counter ID (for example, the output of the `sensors` command; **no hardcoded sensor is supplied**). Pick a time window with available counts, and retrieve that exact sensor's records. Edit the PowerShell variables using your selection:

```powershell
$sensor = '<ID_SHOWN_BY_SENSORS_COMMAND>'
$start = '2026-10-15T00:00:00'
$end = '2026-10-17T00:00:00'

docker compose run --rm simulation python -m cyclistics.nyc_calibration fetch --sensor-id $sensor --start $start --end $end --max-records 3000 --output /app/outputs/nyc_bike_snapshot.json

docker compose run --rm simulation python -m cyclistics.nyc_calibration inspect --input /app/outputs/nyc_bike_snapshot.json
```

Only continue if the snapshot includes **at least two contiguous bicycle-count observations from one clearly selected stream**. The example dates are just a query window, **not an assertion of data availability**. If the sensor's records have another granularity or don't cover the example dates, choose a matching interval.

With the exact `travelmode`, `granularity`, `direction`, `flowid`, and `status` observed in the inspect output (below examples are placeholders), run:

```powershell
docker compose run --rm simulation python -m cyclistics.nyc_calibration calibrate --input /app/outputs/nyc_bike_snapshot.json --sensor-id $sensor --mode '<EXACT_BICYCLE_MODE>' --granularity '<EXACT_GRANULARITY>' --direction '<EXACT_DIRECTION>' --flow-id '<EXACT_FLOW_ID>' --status '<EXACT_STATUS>' --interval-minutes 60 --output /app/outputs/nyc_rate.json
```

**Change `--interval-minutes`** to the observed interval duration, not automatically 60. The existing calibration code refuses mixed/duplicated/gapped streams. It does not automatically verify whether a counter's status represents approved data, so you must inspect the official data dictionary.

Now prepare the rate for NetLogo:

```powershell
docker compose run --rm simulation python -m cyclistics.netlogo_calibration_bridge prepare --calibration /app/outputs/nyc_rate.json --output-dir /app/outputs

Get-Content .\outputs\netlogo_calibration_commands.txt
```

If a real measured rate exceeds the NetLogo slider maximum (**1,800/hour**), the bridge deliberately rejects it instead of silently truncating. Choose a different sensor/window, or update the ABM slider thoughtfully and document the model change.

## Step 3 — Load the rate in NetLogo and run the A/B comparison

1. Open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` from the repository, with **Go stopped**.
2. In the **Command Center** execute the commands printed in `outputs/netlogo_calibration_commands.txt` **one at a time**. The key NetLogo import is:

```netlogo
set arrival-rate-per-hour (first (first (csv:from-file "../outputs/netlogo_arrival_rate.csv")))
```

3. Verify the GUI slider shows the rate you just imported.
4. Run `run-paired-experiment` in NetLogo, which exports `outputs/netlogo_paired_results.csv`.
5. In PowerShell, validate the observed-input *selection* and simulated A/B results:

```powershell
docker compose run --rm simulation python -m cyclistics.netlogo_calibration_bridge verify --calibration /app/outputs/nyc_rate.json --paired-results /app/outputs/netlogo_paired_results.csv --output-dir /app/outputs

Get-Content .\outputs\netlogo_calibrated_pair_report.json
```

For the **synthetic smoke test only**, substitute `/app/outputs/demo_rate.json` and add `--allow-synthetic` to the verify command. This keeps the developmental fixture clearly labeled.

## Output files (all generated in gitignored `outputs/`)

- `netlogo_arrival_rate.csv` — one numeric CSV field for NetLogo.
- `netlogo_rate_provenance.json` — sensor, stream, assumed intervals, observed mean, snapshot/calibration hashes, and limitations.
- `netlogo_calibration_commands.txt` — exact NetLogo Command Center lines.
- `netlogo_calibrated_pair_report.json` — verifies paired scenario settings/rates/conservation and summarizes synthetic queue effects.

## CSC 754 explanation

**Data-informed modeling:** Real count observations can be converted into mean arrival demand for the independent NetLogo ABM. **ABM:** Riders are still virtual agents with local decisions. **Controlled experiments:** Clear and blocked scenarios use matched seeded arrival/speed draws. **Verification:** Input rate equality, conservation, reproducibility and provenance. **Validation (not achieved):** Observed demand rate does not prove accuracy of modeled queues, delays or conflicts; that needs independent field evidence.

## Git workflow

After actual tests and NetLogo runtime checks pass, stage only source/docs/tests (not raw downloaded counts or outputs):

```powershell
git add src/cyclistics/netlogo_calibration_bridge.py tests/test_netlogo_calibration_bridge.py docs/netlogo_nyc_data_calibration.md
git diff --cached --check
git commit -m "feat(data): bridge NYC cyclist counts to NetLogo demand"
git push origin feat/netlogo-abm
```
