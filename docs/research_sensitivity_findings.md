# Milestone 3.8A — NetLogo sensitivity findings (reported local run)

**Status:** Provisional descriptive results; source CSV and manifest are on the researcher's local machine and were not uploaded with this record.

On November 14, 2026, a Windows PowerShell transcript of `feat/research-evidence` showed:

- `docker compose run --build --rm tests` — **145 tests passed**.
- `Test-Path .\outputs\netlogo_sensitivity_raw.csv` — **True**.
- `Import-Csv ... | Measure` / `$rows.Count` — **160 paired CSV rows**.
- `python -m cyclistics.research_evidence` — **PASS: validated 160 paired NetLogo rows** and **PASS: generated 16 research table rows**.
- Two SVG outputs were opened locally. Their visual appearance has not been inspected as part of this record.

## Descriptive results

Each result below is **blocked minus clear**, averaged across **ten matched random seeds (101–110)** per demand/duration combination. The model has a 600-tick horizon, 45-second obstruction start, four demand intensities and four blockage durations.

| Demand (attempted cyclists/hour) | Blockage (s) | Change in mean waiting queue (cyclists) | Change in peak waiting queue (cyclists) |
| ---: | ---: | ---: | ---: |
| 150 | 0 | 0.000000 | 0.0 |
| 150 | 30 | 0.031167 | 0.9 |
| 150 | 60 | 0.134167 | 2.9 |
| 150 | 120 | 0.605500 | 5.5 |
| 300 | 0 | 0.000000 | 0.0 |
| 300 | 30 | 0.070500 | 1.8 |
| 300 | 60 | 0.243000 | 3.9 |
| 300 | 120 | 1.020833 | 9.6 |
| 600 | 0 | 0.000000 | 0.0 |
| 600 | 30 | 0.107000 | 3.3 |
| 600 | 60 | 0.413167 | 7.4 |
| 600 | 120 | 1.889667 | 19.7 |
| 900 | 0 | 0.000000 | 0.0 |
| 900 | 30 | 0.172833 | 5.6 |
| 900 | 60 | 0.706167 | 12.9 |
| 900 | 120 | 3.368833 | 31.7 |

**Interpretation:** In this particular synthetic model experiment, both the average end-of-tick queue and maximum queue increased as blockage duration or attempted demand increased, at the tested grid points. The zero-duration control had no observed effect. At 900 cyclists/hour and 120 seconds of blockage, the mean queue difference was 3.368833 riders and the mean across replicates of the *peak-queue difference* was 31.7 riders.

**Important precision:** The 31.7 value is the **average of paired peak-queue differences**, not the maximum count of cyclists observed in any single run and not a queue of fractional real cyclists. Similarly, 3.368833 is a **mean simulated waiting-count difference**, not extra seconds of individual travel delay.

## Evidence not yet copied to Git

This transcript included the four-decimal/six-decimal mean effects above, but did **not** include the full unrounded per-seed records or the confidence-interval columns. Therefore this document **does not assert interval widths, statistical significance, or predictive accuracy**. The existing exporter generated an `evidence_manifest.json`; its SHA-256 values must be copied or independently checked before reproducibility claims go further.

Local output files (intentionally Git-ignored):

- `outputs/netlogo_sensitivity_raw.csv`
- `outputs/research_evidence/paper_sensitivity_table.csv`
- `outputs/research_evidence/paper_sensitivity_table.md`
- `outputs/research_evidence/netlogo_delta_mean_queue.svg`
- `outputs/research_evidence/netlogo_delta_peak_queue.svg`
- `outputs/research_evidence/evidence_manifest.json`

## Next evidence checkpoint

Review the full exported `paper_sensitivity_table.csv` confidence intervals, inspect SVG legibility, and inspect the source/output hashes in `evidence_manifest.json`. Only then select final values and captions for the paper. The original NetLogo export stays local and unmodified.

**Scientific limit:** These are simulation outputs under assumed bicycle demand, speeds, spatial geometry, and blockage behavior—not measured NYC cyclist queues or delay reductions. The separate Python/DEVS-Suite two-cyclist fixture verifies a different deterministic event case, not numerical agreement across all three engines.
