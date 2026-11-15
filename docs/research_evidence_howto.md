# Run the Milestone 3.8A NetLogo evidence export

This is a **repeatable research workflow** for the existing Cyclistics model. Do not copy numbers from automated test fixtures into the final paper. The summary values and figures are created only from the CSV that NetLogo actually writes.

## 1. Check your working branch and local data

Run these commands in VS Code PowerShell at the root of the Cyclistics repository:

```powershell
git branch --show-current
git status
Test-Path .\outputs\netlogo_sensitivity_raw.csv
```

The branch should be `feat/research-evidence`. Git should report a clean working tree, excluding generated files. If `Test-Path` is `True`, inspect the actual export:

```powershell
$raw = ".\outputs\netlogo_sensitivity_raw.csv"
$records = Import-Csv $raw
$records.Count
$records | Select-Object -First 3 | Format-List
```

The designed sensitivity study produces **160 paired CSV records**. The Python validator also checks the **full** 4×4×10 combination grid, paired equality, conservation, replicate seeds, and numerical consistency. A 160-row count alone is not sufficient to prove that the experiment is valid or that the data came from the NetLogo runtime.

If the CSV is missing, first create it in **NetLogo 6.3.0**:

1. Open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo`.
2. Stop the forever **go** button if it is running.
3. Click **Run sensitivity study**, or enter `run-sensitivity-study` in NetLogo's Command Center.
4. Confirm the console reports that **160 paired sensitivity rows** were written.
5. Check that `outputs/netlogo_sensitivity_raw.csv` exists and retains the original exported bytes. If the run fails, do not substitute any test fixture.

This procedure runs 200 model executions (including baseline runs) and records 160 paired scenario rows. It temporarily disables view updates while running. If a NetLogo error leaves the view frozen, use the NetLogo Command Center `display` command.

## 2. Run the Python tests (these do not run NetLogo)

```powershell
docker compose run --build --rm tests
```

The prior integrated repository had **139 tests**. Milestone 3.8A adds six evidence-package unit tests; the expected complete test count after these commits is **145**, if all pass. These tests use in-memory synthetic fixtures **only to check the analysis program**.

## 3. Export actual research table and plots

From the same repository root, with Docker Desktop running:

```powershell
docker compose run --build --rm simulation python -m cyclistics.research_evidence --input /app/outputs/netlogo_sensitivity_raw.csv --model /app/netlogo/Cyclistics_Bike_Lane_ABM.nlogo --output-dir /app/outputs/research_evidence
```

If input is absent or invalid, the command fails before making the output directory. **Do not manually fill in fake rows to make it pass.**

On success, inspect the results:

```powershell
Import-Csv .\outputs\research_evidence\paper_sensitivity_table.csv |
    Format-Table arrival_rate_per_hour,blockage_duration_s,avg_delta_mean_queue,ci95_low_delta_mean_queue,ci95_high_delta_mean_queue

Get-Content .\outputs\research_evidence\paper_sensitivity_table.md

Start-Process .\outputs\research_evidence\netlogo_delta_mean_queue.svg
Start-Process .\outputs\research_evidence\netlogo_delta_peak_queue.svg

Get-Content .\outputs\research_evidence\evidence_manifest.json
```

The raw CSV, result table, charts and manifest stay under the Git-ignored `outputs/` directory. To recreate the same outputs, reuse the same raw CSV, unchanged NetLogo/analyzer code, and same exporter version. The manifest records SHA-256 hashes of those files.

## 4. What can be written in the paper?

Safe statement **after the real CSV passes validation**:

> We varied synthetic cyclist demand and lane obstruction duration in NetLogo, used ten seeds per condition, and calculated blocked-minus-clear changes with approximate 95% intervals across paired simulated runs.

Report observed *values* only after examining the generated table. Positive change in mean queue means more agents queued **in the simulation**. Negative completed-count change means fewer simulated cyclists exited within 600 ticks. Mean completed-rider stop time must not be described as population average journey delay.

**Not justified:** precise NYC delay savings, real-world accident/crash-risk reductions, calibration of cyclist speeds to meters/second, or direct numeric equivalence with DEVSJAVA. The real DEVS-Suite run verified a different, deterministic two-cyclist case.

## 5. Figure to capture manually

The repository already contains a genuine NetLogo runtime screenshot from tick 600. Because the modeled truck clears at 110 seconds, capture a **second genuine screenshot at tick 85–100** if you want an illustration with the truck actively obstructing the green lane and the queue accumulating. Do not claim an image is a runtime screenshot unless it was captured in NetLogo.

Keep original local CSV outputs safe: Git does not back up files under `outputs/`.
