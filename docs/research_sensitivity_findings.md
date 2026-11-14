# Milestone 3.8A — NetLogo sensitivity findings (reported local run)

**Status:** Validated 160-row NetLogo sensitivity export and reported research summary. The original raw CSV and generated SVG files remain local and have not been independently inspected in this repository. These are simulation results, **not** observed NYC traffic outcomes.

## Reproduction and verification — November 14, 2026

A submitted Windows PowerShell transcript from `feat/research-evidence` showed:

- `docker compose run --build --rm tests` — **145 Python/source-level tests passed**.
- `outputs/netlogo_sensitivity_raw.csv` existed with **160 paired rows**.
- `python -m cyclistics.research_evidence` reported **PASS: validated 160 paired NetLogo rows** and **PASS: generated 16 research table rows**.
- `paper_sensitivity_table.csv` exposed per-configuration means and the lower and upper bounds of approximate 95% paired-difference t intervals.
- `evidence_manifest.json` reported source and result SHA-256 values. These hashes are **recorded from the user's generated manifest**, not independently recomputed from the local CSV bytes by this report.
- The two SVG result files were opened locally but their visual presentation has **not** yet been inspected here.

## Experiment design

The one-lane NetLogo agent-based model uses **four attempted cyclist rates** (150, 300, 600, 900 cyclists/hour), **four obstruction durations** (0, 30, 60, 120 seconds), **ten random seeds** (101–110), an obstruction starting at **t = 45 seconds**, and a **600-tick** horizon (one tick per simulated second).

Each of the 160 records represents a matched clear-versus-obstructed scenario. Clear runs are reused across obstruction durations for the same demand/seed, so results across durations are correlated, rather than 160 independent observations.

The outcome `delta_mean_queue` is the difference in **average end-of-tick waiting cyclist count**; `delta_peak_queue` is the difference in each run's maximum waiting count. Neither is travel time, physical street length, measured crash risk, or observed NYC queueing.

## Results

**Blocked minus clear** effect on mean queue; brackets are approximate, individual **95% Student t intervals** of the mean paired differences (10 seeds, 9 degrees of freedom). The final column is the average of paired **peak queue differences**, not a single-run maximum.

| Attempted cyclists/hour | Blockage duration (s) | Mean queue change (cyclists) | Approximate 95% CI | Average peak queue change (cyclists) |
| ---: | ---: | ---: | ---: | ---: |
| 150 | 0 | 0.000000 | [0.000000, 0.000000] | 0.0 |
| 150 | 30 | 0.031167 | [0.017736, 0.044597] | 0.9 |
| 150 | 60 | 0.134167 | [0.091053, 0.177280] | 2.9 |
| 150 | 120 | 0.605500 | [0.473131, 0.737869] | 5.5 |
| 300 | 0 | 0.000000 | [0.000000, 0.000000] | 0.0 |
| 300 | 30 | 0.070500 | [0.029776, 0.111224] | 1.8 |
| 300 | 60 | 0.243000 | [0.138262, 0.347738] | 3.9 |
| 300 | 120 | 1.020833 | [0.770321, 1.271345] | 9.6 |
| 600 | 0 | 0.000000 | [0.000000, 0.000000] | 0.0 |
| 600 | 30 | 0.107000 | [0.052544, 0.161456] | 3.3 |
| 600 | 60 | 0.413167 | [0.280292, 0.546041] | 7.4 |
| 600 | 120 | 1.889667 | [1.558067, 2.221267] | 19.7 |
| 900 | 0 | 0.000000 | [0.000000, 0.000000] | 0.0 |
| 900 | 30 | 0.172833 | [0.124813, 0.220854] | 5.6 |
| 900 | 60 | 0.706167 | [0.586987, 0.825347] | 12.9 |
| 900 | 120 | 3.368833 | [2.939551, 3.798115] | 31.7 |

## Interpretation and limits

1. **Dose response within the model:** Every tested nonzero blockage duration has a positive estimated queue effect. For a fixed arrival rate, longer blockage durations increase both the mean queue and peak queue differences. For a fixed nonzero duration, higher demand also increases both effects.
2. **Largest tested response:** At 900 attempted cyclists/hour and 120 seconds of obstruction, the mean queue difference is **3.368833** cyclists (approximate 95% interval **2.939551–3.798115**) and the average of paired peak queue differences is **31.7** cyclists.
3. **Control behavior:** Every zero-duration condition yields exactly zero mean/peak queue difference, consistent with the negative-control design.
4. **Uncertainty:** Every nonzero condition's **individual** approximate t interval for mean queue is above zero. These are **not** simultaneous confidence bands, and multiple comparisons have not been adjusted. Interval validity is also conditional on the model and its replicate assumptions; ten seeds provide a limited sample.
5. **Scope:** The blocked simulation has fixed, schematic single-lane rules. No cyclist trajectories, actual traffic delays, NYC queueing outcomes, crash probabilities, field-calibrated velocities, or interventions have been validated. The Python/DEVS-Suite deterministic two-rider fixture is **separate** and does not demonstrate numeric parity among the three engines.

**Key distinction:** The value 31.7 is *an average across seeds of integer-valued peak-queue changes*, not a queue containing a fractional cyclist. The value 3.368833 is the time-averaged **count difference**, not 3.368833 seconds of rider delay.

## Provenance recorded from the local manifest

`schema: cyclistics.research-evidence.v1` · `paired_rows: 160` · `summary_rows: 16` · `field_validated: false` · `same_scenario_as_devsjava: false`.

SHA-256 digests reported:

| Local file | SHA-256 |
| --- | --- |
| `outputs/netlogo_sensitivity_raw.csv` | `658df9a1d1fc4dd3b0f6bd400593b1d8b8b4c9009fadb0fadec2878ee0923f44` |
| `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` | `35ad451c4847ac056c5d76844fdcd0ca105a469bfa1107d7f13d8004e7465c67` |
| `paper_sensitivity_table.csv` | `cf0933bbac70561d56af762cbfa75109a50899cba7ed89cc652432f329e403e0` |
| `paper_sensitivity_table.md` | `9769d6d8fd6f1b70c38ec2e3b7c9a48f7afca2a2b4e473449464d6142d232aab` |
| `netlogo_delta_mean_queue.svg` | `eed50b09e83bbb53c9e659c5add4b293e55c9f2422016eb0e7ee2e6ba86e9194` |
| `netlogo_delta_peak_queue.svg` | `230248af5e69b118855b25b26ddfd9b42e7bc26d45a3f60534def7c4e3ff91f0` |

The user's manifest also records hashes for the Python evidence builder and sensitivity analyzer; the full manifest is retained locally under `outputs/research_evidence/evidence_manifest.json`. Hashes alone do not prove a file was generated by the NetLogo runtime; the original experiment and file origin remain part of the research record.

## Recommended paper visuals and caption

**Figure A — Primary:** `netlogo_delta_mean_queue.svg`, changes in average waiting queue across all demand and blockage settings, with approximate paired-difference 95% t intervals.

**Figure B — Supporting:** `netlogo_delta_peak_queue.svg`, average change in maximum queue across replicates.

**Suggested concise caption:**

> Effect of simulated bicycle-lane obstructions on mean waiting queue in NetLogo (4 demand levels × 4 durations; 10 paired seeds per configuration). Error bars represent approximate 95% t intervals of blocked-minus-clear differences; results are synthetic, not observed NYC outcomes.

Before treating either chart as a final figure, visually inspect labels, interval bars, scaling and readability, and independently check local source/output hashes against the reported manifest. Generated data and plots remain Git-ignored under `outputs/`.

**CSC 754 defense:** ABM represents individual cyclists and emergent queues; replicated paired trials are controlled simulation experiments; per-tick conservation and negative controls provide *verification*, not external *validation*. The DEVS model uses an event-driven coordinator rather than NetLogo's global ticks.
