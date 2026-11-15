# Milestone 3.8A — Reproducible research evidence from NetLogo sensitivity data

**Branch:** `feat/research-evidence` (based on merged `main` at `9b3c514`)
**Scope:** Evidence packaging; **no changes to ABM movement rules or original observations**

## Research question

Under the model's synthetic arrival process, how do attempted cyclist demand (150, 300, 600, 900 per hour) and temporary lane obstruction duration (0, 30, 60, 120 seconds) affect queue length and completion outcomes?

We will use the **existing** NetLogo `run-sensitivity-study`, not fabricate results. The design is 4 arrival rates × 4 durations × 10 seeds (101–110): **160 paired records**, with 45-second obstruction start and 600-tick horizon. The validated experiment contains 40 independent clear-lane baseline runs reused across duration treatments. Zero-duration controls must reproduce the clear condition.

## Scientific contract

1. Require the **actual** `outputs/netlogo_sensitivity_raw.csv` exported by NetLogo. If it does not exist, fail with a clear message and generate **no research results**. Never substitute Python test fixtures or invented measurements.
2. Reuse `cyclistics.netlogo_sensitivity.read_and_validate()` and `summarize()`; reject missing/duplicated rate-duration-seed combinations, false conservation, failed paired-draw flags, and invalid differences.
3. Generate **16 rows** in a paper-oriented results table. Show average clear/blocked mean queues, blocked-minus-clear queue changes and paired-difference 95% t intervals, changes in peak queue, and average completed-cyclist stop time **only if explicitly labeled as a completed-rider endpoint metric**.
4. Generate two existing SVG figure types from the validated summaries. Do not relabel model values as observations or compare NetLogo queue estimates numerically with the Java/Python shared event fixture.
5. Generate a machine-readable provenance JSON file with SHA-256 hashes of the real raw CSV, the NetLogo model, the sensitivity analyzer, and generated outputs; include experiment dimensions, interval assumptions, and `field_validated: false`.
6. Put all generated files in `outputs/research_evidence/` (**gitignored**); commit only source, tests, design, and reproduction instructions. Generated figures can be selectively promoted to paper materials **after** the underlying raw CSV is inspected and retained privately.

## Deliverables (only after a real NetLogo CSV is provided)

| File | Role |
| --- | --- |
| `paper_sensitivity_table.csv` | Machine-readable rows for paper tables |
| `paper_sensitivity_table.md` | Human-readable 16-row Markdown table and interpretation notes |
| `netlogo_delta_mean_queue.svg` | Change in mean queue with paired-difference 95% intervals |
| `netlogo_delta_peak_queue.svg` | Change in peak queue with paired-difference 95% intervals |
| `evidence_manifest.json` | SHA-256 source/output provenance and caveats |

We **will not** state particular sensitivity effects before running against the user's exported 160-row dataset. Existing screenshot at tick 600 is evidence of GUI operation, not of an active obstruction. An optional photo at tick 85–100 should be a real capture, not rendered as simulated evidence.

## Work sequence

- **3.8A.1 (this commit):** Design and accepted evidence contract, including avoidance of fake measurements.
- **3.8A.2:** Add focused tests for manifest and table creation, corrupt/missing inputs, and provenance.
- **3.8A.3:** Implement the evidence-packaging CLI using existing validated analysis utilities; keep external dependencies at zero.
- **3.8A.4:** Document copy-paste commands; run Python/Docker CI and real desktop NetLogo export, then review the actual generated table before quoting any results.
- **3.8B:** Present verified Python/Java event-time agreement separately (two riders at 14/24 s), runtime benchmark figures, and limits of real-world calibration.
- **3.8C:** Final paper/presentation evidence checklist, accurate citations, screenshot, and README cleanup.

## CSC 754 connection / explanation

NetLogo ABM is the *microscopic* model: autonomous cyclist turtles interacting over a patch-based environment and advancing in global ticks. The paired sensitivity design is a controlled simulation experiment, where replicates use the same arrival/speed draws between obstructed and clear conditions. The output analyzer computes confidence intervals across synthetic random seeds; the intervals quantify run-to-run variation **under the model**, not uncertainty about NYC traffic. The DEVS-Suite coordinator uses discrete events instead of one-second NetLogo ticks and should be described as a separate, limited verification experiment.

**For presentation:** "We repeated each simulated demand-and-blockage combination with 10 seeds and compared each blocked run to its matching clear run. That isolates the obstruction's effect inside the model. We still need observed queues or delays to say how accurately it predicts NYC conditions."
