# Cyclistics — final submission status and evidence ledger

**Checkpoint:** November 14, 2026 (America/New_York; some GitHub Actions runs are timestamped November 15 UTC).  
**Scope:** CSC 754 individual prototype, not a deployed or field-validated NYC digital twin.

This is a current-status index. Older milestone documents describe what was *planned or true at that time*. Preserve them for development history, but use this file and the linked result reports for the final paper.

## What is implemented and verified

| Component | Current evidence | Boundary |
| --- | --- | --- |
| Python DES reference | Reproducible seeded FIFO bottleneck, event scheduling, scenario CSVs, tests | Synthetic arrivals unless an explicitly selected counter rate is supplied |
| Java DEVS-Suite | CyclistGenerator, ObstructionController, LaneBottleneck, coupled model, real historical coordinator output | One shared deterministic Python/Java fixture; historical JAR not proven to match the course distribution |
| NetLogo ABM | Runnable single-lane cyclist agents, local movement, truck blockage, per-tick conservation, paired experiments | No overtaking, adjacent motor traffic or collision prediction |
| NYC data pipeline | Read-only bicycle counter/sensor ingestion, stream-level quality inspection, provisional input-rate bridge | Some source streams have raw status and ambiguous direction/flow mapping; do not combine flows or claim field validation |
| Sensitivity study (3.8A) | 160 matched results (4 demand rates × 4 blockage durations × 10 seeds), 16 summaries, two reviewed charts | Synthetic, internal model variability only |
| Runtime study (3.8B) | Actual headless NetLogo 6.3.0 on GitHub Ubuntu: 5 verification cases, 36 timed runs, 12 summaries, two plots | Very short/noisy host-specific wall-clock timings; not performance parity across engines |
| Integration & CI | GitHub PR #5, #6 and #7 squash-merged into `main`; 151 Python tests and 4/4 CI checks passed on merge commit `cef4aa7` | Docker Python tests cannot substitute for field observations or the professor's own DEVSJAVA runtime |

**Key verified references:**
- [Python–Java deterministic event comparison](cross_model_comparison_results.md): arrivals at 10 and 15 s; block 12–20 s; completions 14 and 24 s; peak waiting queue 1
- [NetLogo sensitivity findings and paired t intervals](research_sensitivity_findings.md): 900 cyclists/hour and 120 s blockage yields +3.368833 average waiting cyclists (approx. 95% t interval 2.939551–3.798115), +31.7 average paired peak-queue difference
- [GitHub NetLogo runtime results](performance_evidence_results.md): measured 36 GitHub-hosted Linux NetLogo trials, with explicit environment and SHA-256 provenance
- [Prospect Park West counter evidence](nyc_prospect_park_west_calibration.md): a selected provisional count stream (99 cyclists/hour), still unverified raw source data

## Verification is not validation

Verification asks: **Did our simulation and software follow their defined rules?** Evidence includes deterministic replay, arrival-draw matching, conservation, the DEVS event fixture, Python tests, and real NetLogo runtime checks.

External validation asks: **Do simulated queues, delays or cyclist behavior match independent real-world observations?** Cyclistics has **not** demonstrated this. NYC counts inform an input rate in selected workflows; they do not validate obstruction durations, queue lengths, individual delay or crash risk.

The Python event queue, Java DEVS coordinator and NetLogo tick-based ABM are **not live-coupled** and do **not share a general numerical-equivalence claim**.

## Course requirements and final deliverables

For the remaining individual submission, prepare:
- [ ] A **10–12-page target paper** (subject to Dr. Gu's final instructions) with cited related work, explicit formal DEVS tuple and confluence policy, NetLogo rules, data limitations, test design, findings and figures
- [ ] A concise presentation with readable figures and conversational notes; include future work because that was requested during the group-presentation feedback
- [ ] Reproducibility appendix: exact commands, software versions, source hashes, original CSVs, NetLogo output artifact, and instructions for the external Java JAR (do not redistribute the JAR)
- [ ] Actual code demonstration/screenshot of NetLogo in obstruction state (e.g., around simulated t=85–100), captured from the running model rather than an invented mockup
- [ ] Final spell-check, citation-to-reference audit, chart captions, and an explicit statement distinguishing synthetic data from NYC observations

## Deferred features (not current functionality)

Roboflow camera detection, live CV-triggered obstruction events, ArcGIS interactive operational dashboard, lane-changing/overtaking and multi-lane traffic, cyclist collision/crash probabilities, live NetLogo–Java co-simulation, and independently observed NYC queue/delay validation are **future work**, not implemented outcomes.

**Release discipline:** keep all genuine feature branches and original PR history; do not fabricate user activity, NetLogo observations or source data. Commit only source, documentation and tests to Git. Retain generated experimental CSVs, figures and outside libraries separately.
