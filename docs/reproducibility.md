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

## Troubleshooting

- Windows: install and start Docker Desktop, then use a PowerShell or VS Code terminal from the extracted folder.
- Linux bind mounts: the container runs as UID 10001; ensure `outputs/` is writable or adjust its host-side permissions / container user appropriately.
- Only the Python reference engine is currently containerized. NetLogo GUI and the professor's DEVSJAVA distribution require separate setup.
