# Changelog

## Unreleased — November 14, 2026: CSC 754 integrated research prototype

- Merged the Java DEVS-Suite atomic/coupled models, NetLogo single-lane ABM, NYC bicycle-count quality tooling, and Python reference through PR #5.
- Ran the historical external DEVS-Suite 2.1 coordinator and verified a deterministic two-cyclist case with departures at simulated **14 s and 24 s**; this does **not** prove broad engine parity or field validation.
- Added reproducible NetLogo sensitivity research packaging through PR #6: 160 paired records, 16 summary conditions, two SVG figures, paired t intervals and source/result SHA-256 hashes.
- Added actual NetLogo 6.3.0 headless performance execution and evidence export through PR #7: five verification cases, 36 timed GitHub-hosted runs, twelve runtime summaries and archived original CSVs.
- The merged `main` CI passed 151 Python/source-level tests and four GitHub Actions checks ([run](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43667009570)).
- Began an evidence-led final CSC 754 paper and presentation package, updating source scope, architecture, reproducibility and limitations.

**Software version:** The published Python package metadata remains `0.2.0` until a separate, deliberate release/tag. The above is a project milestone log, **not** a claim that a `0.3.0` release was published. Simulated NYC queues and crashes have not been externally validated.

### Experimental v2 extensions — November 14, 2026

- Squash-merged PRs #9–#14 with all original feature branches retained. Original v1 NetLogo model and source-backed scientific findings were not rewritten.
- Added a strict camera-observation contract and optional Roboflow response adapter. **Actual hosted inference requires the user's model, credentials and footage.**
- Added an ArcGIS Maps SDK browser scenario viewer with user-provided WGS84 GeoJSON, simulation/provisional status, scenario and simulated-time filters; static checks passed but no hosted browser/deployment run is claimed.
- Added a separately testable NetLogo 6.3.0 two-lane cyclist/car model with gap-accepted merges, car following, conservation/spacing tests, and actual CSV trajectory export.
- Analyzed **6,217 simulated NetLogo trajectory rows** for **17 TTC-like closing-gap snapshots** and **4 same-point passage-gap pairs**; these are surrogate exposures, not field measurements or predicted crashes.
- Added a versioned offline Python replay bridge and Java 17 obstruction-schedule parser, plus a configurable Java DEVS-Suite runner requiring the external local JAR.
- [Integrated GitHub test run 43671793377](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671793377): Python generated reviewed *synthetic* events, the real Java parser read the CSV, headless NetLogo replayed exactly 8 blocked ticks, and Python analyzed 4,820 exported trajectory rows. **Not live multi-engine synchronization.**
- Python CI reached **186 passing tests** in the end-to-end feature PR. External image inference, direct browser testing, local real DEVS-Suite replay and field calibration remain separate work.

## 0.2.0 — 2026-11-12
- Converted Python reference simulation to an installable package.
- Added Docker/Compose, CI workflow configuration, GitHub templates, and documentation.
- Added portfolio-oriented visualization of synthetic sample outputs.

## 0.1.0 — 2026-11-12
- Implemented a single-bottleneck discrete-event simulator.
- Added deterministic tests, scenarios, and CSV exports.
