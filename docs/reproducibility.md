# Reproducibility

## Reference experiment

Local Python:

```bash
cyclistics --rate 300 --horizon 1800 --seed 754 --output-dir outputs
```

Docker:

```bash
docker compose run --build --rm simulation
```

These should produce identical synthetic scenario metrics. Committed example values are in `examples/results/scenario_metrics.csv`. Newly generated CSV files are ignored under `outputs/`.

## Assumptions

- Seeded Poisson arrivals, with synthetic intensity 300 cyclists/hour.
- One idealized bottleneck, not a city street network.
- Deterministic 3-second service headway; FIFO waiting.
- Existing service may finish after obstruction begins; blockage prevents *new* service.
- One set of arrivals reused across scenarios for matched comparisons.
- Default 1,800-second arrival horizon, with eventual service completion after the horizon when necessary.
- Travel-time estimate adds a 20-second assumed free-flow time to modeled queueing delay.

These experiments are **not** observed NYC queueing delays, validated crash predictions, or verified real-world intervention effects.

## Verify

```bash
python -m unittest discover -s tests -v
```

## Integrated Java and NetLogo verification (November 2026)

The integrated repository includes Python DES, NetLogo ABM source, and DEVSJAVA atomic/coupled models. These implementations run **separately**, not as a live-coupled digital twin.

From a Windows PowerShell terminal at the repository root, use Docker Desktop for the Python checks:

```powershell
docker compose run --build --rm tests
```

The integrated run reported **139 passing Python/source-level tests** on November 14, 2026.

For the real Java coordinator, first put the separately obtained DEVS-Suite JAR in `devsjava/vendor/` (the JAR is not shipped in Git). Then run:

```powershell
.\devsjava\scripts\verify-real-devsjava.ps1
.\devsjava\scripts\run-real-coupled.ps1
```

The production Java code compiled against a historical DEVS-Suite 2.1 JAR and completed one deterministic coupled-model case, departing two cyclists at **14 and 24 seconds**. This does not prove compatibility with every CSC 754 course DEVSJAVA distribution.

The five standalone Java adapter smoke suites use local test doubles, **not** the external DEVS-Suite coordinator. They should be run separately before release; instructions are recorded in [final integration verification](final_integration_verification.md).

For the visual model, open `netlogo/Cyclistics_Bike_Lane_ABM.nlogo` in NetLogo **6.3.0**, set the parameters, and run the paired clear/blocked experiment. The source-level Python tests do not launch the NetLogo GUI. A desktop execution and visual-only regression were recorded separately in [NetLogo visualization results](netlogo_visual_regression_results.md).

**Scientific limitation:** The verified event-time comparison is one deterministic Python/DEVS-Suite fixture. NetLogo uses different agent movement assumptions. None of these outputs have been validated against measured NYC queueing delays or trajectories.

## Troubleshooting

- Windows: install and start Docker Desktop, then use a PowerShell or VS Code terminal from the extracted folder.
- Linux bind mounts: the container runs as UID 10001; ensure `outputs/` is writable or adjust its host-side permissions / container user appropriately.
- The Python application/test image does not contain the NetLogo GUI or the external DEVS-Suite JAR. The Java scripts use dedicated Java Docker containers and require that JAR in the local vendor folder.
