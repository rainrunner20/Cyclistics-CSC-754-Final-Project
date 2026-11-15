# Cyclistics v2 — verified experimental extension checkpoint

**Date:** November 14, 2026 New York time (GitHub Actions logs show November 15 UTC).  
**Status:** Five requested extension tracks have implemented **prototype components**. The reproducible offline demonstration is verified; **real cloud camera inference, deployed ArcGIS browser behavior, and live multi-engine synchronization have not yet been verified**.

The published v1 single-lane NetLogo model, the 160-pair sensitivity study, and the 36-run performance evidence remain unchanged. This project does **not** predict real bicycle crashes or validate queues against field observations.

## What was actually built

| Advanced feature | Implemented code and experiment | What remains unproven |
| --- | --- | --- |
| Roboflow detection | Optional `cyclistics.roboflow_adapter` using the official provider inference SDK interface, validated boxes/confidence/source, seven-adapter-style software test cases plus observation-contract tests | No actual Roboflow project/model, private API key or user-supplied video frame was run here; object detection **does not** confirm a bike-lane blockage |
| ArcGIS dashboard | `web/` JavaScript map viewer with ArcGIS Maps SDK 5.1, GeoJSON import, filters by scenario/simulated time and simulation/provisional status; Python WGS84 GeoJSON exporter | Static JS and HTML checks passed, **not a cross-browser live viewer test**; no deployed hosted URL or fabricated NYC pins; real coordinates/hosting may require user account |
| Java/Python/NetLogo event interoperability | Python versioned candidate and event schemas, deterministic de-duplication, approved synthetic replay, real Java 17 parser consuming Python's output, real NetLogo 6.3.0 importing the same CSV, Java configurable real-coordinator adapter | This is **verified offline batch interoperability**, not live bidirectional clock synchronization; new Java coupled runner has not been executed against user's private historical DEVS-Suite JAR |
| Car traffic and cyclist lane changes | Separate `Cyclistics_Mixed_Traffic_v2.nlogo`, cyclist and car agents, two schematic lanes, gap-based merges/returns, seeded replay, trajectory exports, per-tick conservation and separation tests | No validated real vehicle speeds, human gap acceptance, meters-to-patch scale or actual car/bike interaction footage |
| Conflict analysis | Model-level TTC-like closing gaps and same-x PET-like passage time gaps derived from **real simulation-generated** NetLogo trajectory CSVs | These are surrogate *exposure counters* only, **not observed crashes, true crossing PET, or calibrated real crash probabilities** |

## Real headless NetLogo 6.3.0 mixed-traffic evidence

[Mixed-traffic workflow run 43670977203](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43670977203) produced the test comparison below (seed 754, 300 simulated ticks, 900 attempted cyclists/hour, 600 attempted cars/hour, 120-second synthetic blockage at t=45):

| Result | Merge disabled | Merge enabled |
| --- | ---: | ---: |
| Cyclist arrivals | 94 | 94 |
| Car arrivals | 61 | 61 |
| Cyclist departures | 73 | 84 |
| Car departures | 57 | 57 |
| Cyclist merges | 0 | 23 |
| Cyclist returns | 0 | 20 |
| TTC-like exposure snapshots under 3 seconds | 0 | 17 |

All runs passed cyclist/car accounting and same-lane spacing checks. The **number of departures** is not a field-measured travel-time improvement, and the TTC proxy is not crash probability.

A separate run [43671124239](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671124239) processed **6,217 actual v2 simulation trajectory rows** (155 simulated agents), reporting **17 TTC-like exposure snapshots** and **4 same-x passage-gap pairs**, with minimum model proxy values 0.805 s and 1.534 s respectively. See [full conflict report](v2_conflict_proxy_methods.md) for thresholds and SHA-256 hashes.

## Verified Python → Java parser → NetLogo → Python analysis demonstration

[End-to-end workflow run 43671793377](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671793377), commit `82f57e7`, completed every step with real software execution:

1. `cyclistics.v2_demo` accepted **an explicitly approved synthetic fixture** (not camera footage) and exported a two-row blockage schedule, t=12 start, t=20 clear, with a replay SHA manifest.
2. A real Java 17 compiler/parser read that exact Python-exported CSV and verified the single [12,20) window. **The external DEVS-Suite coordinator was not invoked in this step.**
3. A genuine headless NetLogo 6.3.0 experiment imported the CSV, ran experimental motor/cyclist agents for 300 ticks, passed separate conservation and spacing checks, and verified exactly **8 active obstruction ticks**.
4. NetLogo exported **4,820 real model-generated trajectory rows**, which the Python conflict analyzer parsed; this brief early obstruction produced **zero** TTC-like or same-x passage-gap events. This is distinct from the longer t=45–165 study above.
5. The browser GeoJSON tool produced an **empty** FeatureCollection because no actual NYC WGS84 point was supplied. It did **not** guess a physical address from a NetLogo model patch.
6. All outputs and SHA-256 manifests are in [GitHub artifact 14144551660](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43671793377/artifacts/14144551660). GitHub artifacts are temporary; download the ZIP before its retention period ends.

GitHub CI for the integration PR reported **186 passing Python tests** on Python 3.12, with the same tests and Docker smoke job passing on all configured CI platforms. GitHub PRs #9–#14 were genuinely committed and squash-merged into `main`, preserving every source feature branch.

## What is needed for a true live, deployed end-to-end digital twin

- **Actual detection:** an authorized street image or video, the correct Roboflow trained vehicle/obstruction model and credentials; manual or algorithmically validated lane geometry and detector precision/recall.
- **Actual mapping:** verified NYC segment coordinates (not schema fixtures) and a browser test; deploy or host web files if a public URL is desired.
- **Actual external Java integration:** a compatible local DEVS-Suite JAR and real run of `devsjava/scripts/run-v2-replay.ps1`; it is intentionally excluded from the repository.
- **Live coordination:** a new event transport layer with delivery acknowledgement, mapped wall/simulation clocks, late and duplicate event behavior, fault recovery and actual measured end-to-end latency. **Passing offline replay is not the same as live synchronized co-simulation.**
- **External validation:** measured real lane-blockage durations, bicycle/car trajectories and observed delays/conflicts before any real-world predictive or safety claims.

## Where to start

- [Advanced work plan](advanced_extensions_plan.md)
- [Vision, map and replay quickstart](v2_integrations_quickstart.md)
- [Mixed traffic results and reproduction](v2_mixed_traffic_results.md)
- [Conflict proxy methods](v2_conflict_proxy_methods.md)
- [Java DEVS offline replay](v2_devs_replay.md)
- [Integrated offline demo](v2_end_to_end_offline_demo.md)
- [Preserved v1 research evidence](research_sensitivity_findings.md)

**Submission boundary:** The original v1 study remains the scientifically defensible CSC 754 baseline. V2 is a separate experimental research prototype and should be presented with its own assumptions, controls, tests and explicitly synthetic labels.
