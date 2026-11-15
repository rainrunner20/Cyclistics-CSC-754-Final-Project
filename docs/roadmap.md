# Cyclistics — roadmap and delivery checkpoints

**Status as of November 14, 2026 (NY time):** Core implementation and both research-evidence PRs are merged. Refer to [final submission status](final_submission_status.md) for authoritative evidence; original milestone design docs may retain historical language.

| Phase | Deliverable | Status and evidence |
| --- | --- | --- |
| 0 | Python discrete-event reference, CSV, seeded scenarios | **Complete**; [reproducibility](reproducibility.md) |
| 1 | GitHub structure, Docker, CI | **Complete**; 151 Python tests and 4 GitHub CI jobs passed on `main` commit `cef4aa7` |
| 2 | Formal DEVS tuples, atomic/confluent policies | **Complete for specified models**; [atomic design](devs_bottleneck_design.md) |
| 3 | Java DEVS-Suite atomic and coupled models | **Implemented and executed** against historical 2.1 JAR; deterministic 14/24-second fixture; no field validation |
| 4 | Single-lane NetLogo cyclist ABM and verification | **Complete for the scoped one-lane model**; real desktop and headless tests |
| 5 | NYC count ingestion, stream quality and candidate rate | **Implemented**, but real count stream remains provisional and unverified |
| 6A | Paired NetLogo sensitivity study and paper figures | **Complete**; 160 paired rows, 16 summaries, 95% within-model intervals ([findings](research_sensitivity_findings.md)) |
| 6B | NetLogo computational performance evidence | **Complete**; 36 measured GitHub-hosted trials, 12 summaries ([performance](performance_evidence_results.md)) |
| 7 | Experimental v2 CV, ArcGIS, event replay, motor traffic, merging, conflict proxies | **Prototype components implemented and offline replay verified**; no actual hosted camera inference, live synchronization, or field validation |
| 8 | Final individual paper, presentation and packaged evidence | **In preparation**; [final report blueprint](final_report_presentation_plan.md) |

## Experimental v2 roadmap (separate from verified v1)

The user chose to pursue **all five** advanced extensions after the initial CSC 754 core was completed. They were implemented as **experimental v2 prototype components** and documented in [the extension status and evidence ledger](v2_extension_release_status.md), [the advanced extensions plan](advanced_extensions_plan.md), and [ADR 0003](decisions/0003-protect-v1-while-extending.md). The remaining *live/deployed* requirements are separate from the working offline prototypes:

1. **Roboflow adapter implemented, provider execution pending:** the optional image-inference SDK interface is coded/tested, but actual footage, model ID, credentials and an independently reviewed lane-overlap decision remain external.
2. **ArcGIS viewer implemented, browser/location verification pending:** JavaScript and GeoJSON source validation passed, but no deployed/fully user-tested map or verified segment coordinate is supplied.
3. **Offline Python → Java parser → real NetLogo replay verified:** 8 simulated blocked ticks, conservation, 4,820 exported trajectory rows and analysis in GitHub. Actual new Java external-coordinator runner and real-time synchronization still require additional tests/engineering.
4. **Mixed-traffic NetLogo v2 executed:** two seeded lanes, car agents, cyclist merges and replay were run in genuine NetLogo 6.3.0. Kinematics remain idealized; real-world validation is absent.
5. **Cyclist merging and proxy analysis executed:** per-tick conservation/gaps, 17 TTC-like snapshots and four same-point separation pairs from 6,217 model-produced trajectory rows; no claim of validated PET/crash probabilities.

The experimental work must not overwrite the 160-pair v1 sensitivity measurements or source digests, and **does not replace completion of the individual paper and presentation**.

## Remaining submission checklist

- Draft and verify final 10–12-page paper from the repository's evidence, with correct figure captions, methods and bibliography.
- Make a short presentation explaining the model architecture, DEVS equations and ports, NetLogo behavior, experimental design, observed simulation results and limitations.
- Archive original NetLogo sensitivity CSV, locally generated figures and SHA-256 manifest. Keep the GitHub-hosted runtime ZIP (Action artifacts expire).
- Re-run the Java coordinator locally if the course environment changes; do not commit the third-party JAR.
- Ensure the professor's current submission instructions, demo requirements and AI policy are followed.

## Portfolio demonstration ideas

1. Execute a Python scenario reproducibly from one command and inspect its CSV.
2. Show the actual NetLogo model in the GUI with a truck obstruction and visible waiting cyclists.
3. Display the NetLogo 160-pair sensitivity chart and explain its uncertainty.
4. Walk through the three Java atomic components and the 14/24-second coordinator event fixture.
5. Show the GitHub Actions headless NetLogo benchmark artifact and explain simulated time versus wall-clock time.

**Scientific integrity:** Internal test success does not prove real-world queue, delay, or safety prediction accuracy.
