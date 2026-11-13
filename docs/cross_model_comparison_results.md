# Cyclistics — Cross-model comparison results (Milestone 3.5)

## Question

Do the Python discrete-event reference and the DEVS-Suite coupled model agree on the same small, deterministic bicycle-lane obstruction scenario? Separately, does the NetLogo experiment preserve the inputs and cyclist accounting used in its clear/blocked comparison?

These are verification checks. They do **not** establish accuracy against observed cyclist delays or queues in New York City.

## Shared Python / DEVS-Suite test case

| Setting | Value |
| --- | --- |
| Cyclist arrival times | 10 s and 15 s |
| Obstruction interval | [12 s, 20 s) |
| Bottleneck passage time | 4 s per cyclist |
| Expected departures | Cyclist 1 at 14 s; cyclist 2 at 24 s |
| Expected maximum waiting queue | 1 cyclist |

The first cyclist is already being served when the obstruction begins, so that passage completes at 14 s. The second cyclist arrives during the obstruction, waits until clearance at 20 s, and completes its passage at 24 s. The Python reference's mean waiting time for the two completed cyclists is 2.5 s (0 s and 5 s).

## Observed verification results — November 13, 2026

The Python reference scenario executed through `cyclistics.cross_model_comparison`. The DEVS-Suite coupled runner compiled production Java classes against the locally available `DEVS-Suite-2.1.0-20090428.jar` and ran the actual external coordinator, not the test adapter. The saved console output contained:

```text
Compiling real production classes against DEVS-Suite...
Starting DEVS-Suite coordinator (headless)...
port: departed value: cyclist-1
port: departed value: cyclist-2
Terminated Normally at ITERATION 7 ,time: Infinity
DEPARTURE,14.000,cyclist-1
DEPARTURE,24.000,cyclist-2
Cyclistics coupled-DEVS summary:
  generated=2
  obstruction events=2
  departed=2
  max waiting=1
  remaining=0
PASS: real coordinator departure timestamps match 14s and 24s.
```

The comparison command subsequently reported:

```text
Python: reference_executed
Java: matches_python_deterministic_fixture
NetLogo: within_netlogo_consistent_only
```

**Conclusion:** The Python reference and the real DEVS-Suite runner agreed on departure order and timestamps, generated/departed counts, and the maximum waiting queue **for this one deterministic fixture**. The Java event log was parsed and checked rather than substituting an expected result for an actual execution. The comparison tool's automated checks also passed as part of the 131-test Python suite.

## Separate NetLogo evidence

The NetLogo input to the comparison tool was `outputs/netlogo_paired_results.csv`, produced earlier from the single-lane agent-based model. The parser checked that the clear and blocked experiments used matching seed, demand, scenario timing, and run length; it also checked cyclist conservation and numeric outputs.

The result `within_netlogo_consistent_only` is **not** a numerical agreement claim between NetLogo and Java/Python. NetLogo uses spatial cyclist agents and a different arrival/movement mechanism. Comparing wait times or departure counts across the three models as though their scenarios were identical would be misleading.

## Reproduction and provenance

The Java implementation currently lives on the separate `feat/devs-atomic-models` branch. It was executed from a Git worktree using:

```powershell
.\devsjava\scripts\run-real-coupled.ps1
```

The real Java stdout was saved in the original repository's ignored `outputs/devsjava_coordinator.log` file. The original repository's `feat/cross-model-comparison` branch then produced the ignored report `outputs/cross_model_report.json` via:

```powershell
docker compose run --rm simulation python -m cyclistics.cross_model_comparison --java-log /app/outputs/devsjava_coordinator.log --netlogo-paired /app/outputs/netlogo_paired_results.csv --output /app/outputs/cross_model_report.json
```

The report stores SHA-256 hashes for the Java log and NetLogo input. Both complete local outputs remain ignored and are not part of this commit. The class-library file is also local and must not be committed.

## Limits and follow-up

- The historical DEVS-Suite 2.1.0 JAR was used successfully, but it has **not** been established as Dr. Gu's exact class distribution.
- Agreement on this two-cyclist example is limited verification, not broad cross-implementation equivalence. Simultaneous events, larger arrival sets, repeated obstructions, and more complex schedules still need comparison.
- No cyclist trajectories, delays, queues, or collision risks were validated against field observations. NYC counter counts inform demand rates elsewhere in Cyclistics; they do not validate these outputs.
- The DEVSJAVA implementation still needs repository-integration review because the Java code is on a separate feature branch.
