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
| 7 | Advanced CV, ArcGIS, co-simulation, motor traffic, cyclist lane changes and surrogate safety | **Approved experimental v2 backlog**; design and observation-contract foundation only, **not** a functioning integrated extension |
| 8 | Final individual paper, presentation and packaged evidence | **In preparation**; [final report blueprint](final_report_presentation_plan.md) |

## Experimental v2 roadmap (separate from verified v1)

The user chose to pursue **all five** advanced extensions after the initial CSC 754 core was completed. They are tracked in [the advanced extensions plan](advanced_extensions_plan.md) and [ADR 0003](decisions/0003-protect-v1-while-extending.md). Start with an observation contract and regression tests; then build and test each of the following as independent deliverables:

1. Optional Roboflow computer-vision inference with an actual image/video and reviewed lane-overlap decision.
2. An ArcGIS scenario map using grounded NYC geometry and labeled synthetic simulation results.
3. Python/DEVS-Suite/NetLogo deterministic event replay, followed by true live orchestration only if clocks and message delivery are verified.
4. A separately named mixed-traffic NetLogo model containing a motor-vehicle lane, seeded car agents and traffic interaction logic.
5. Realistic-for-the-model cyclist lane-choice rules and computed conflict proxies (e.g. TTC/PET), **not** unvalidated crash probability.

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
