# Changelog

## Unreleased — November 14, 2026: CSC 754 integrated research prototype

- Merged the Java DEVS-Suite atomic/coupled models, NetLogo single-lane ABM, NYC bicycle-count quality tooling, and Python reference through PR #5.
- Ran the historical external DEVS-Suite 2.1 coordinator and verified a deterministic two-cyclist case with departures at simulated **14 s and 24 s**; this does **not** prove broad engine parity or field validation.
- Added reproducible NetLogo sensitivity research packaging through PR #6: 160 paired records, 16 summary conditions, two SVG figures, paired t intervals and source/result SHA-256 hashes.
- Added actual NetLogo 6.3.0 headless performance execution and evidence export through PR #7: five verification cases, 36 timed GitHub-hosted runs, twelve runtime summaries and archived original CSVs.
- The merged `main` CI passed 151 Python/source-level tests and four GitHub Actions checks ([run](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43667009570)).
- Began an evidence-led final CSC 754 paper and presentation package, updating source scope, architecture, reproducibility and limitations.

**Software version:** The published Python package metadata remains `0.2.0` until a separate, deliberate release/tag. The above is a project milestone log, **not** a claim that a `0.3.0` release was published. Simulated NYC queues and crashes have not been externally validated.

## 0.2.0 — 2026-11-12
- Converted Python reference simulation to an installable package.
- Added Docker/Compose, CI workflow configuration, GitHub templates, and documentation.
- Added portfolio-oriented visualization of synthetic sample outputs.

## 0.1.0 — 2026-11-12
- Implemented a single-bottleneck discrete-event simulator.
- Added deterministic tests, scenarios, and CSV exports.
