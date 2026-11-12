# Contributing

Cyclistics is an academic research prototype. Changes should improve reproducibility and make modeling assumptions explicit.

1. Create a focused branch and describe your change in a pull request.
2. Install with `python -m pip install -e .` or use Docker.
3. Run `python -m unittest discover -s tests -v`.
4. Add tests when changing event ordering, timestamps, state transitions, or metrics.
5. Distinguish synthetic results from calibrated/observed results.

Don't commit private data, credentials, raw downloaded datasets, or generated files in `outputs/`. Small fixtures in `examples/results/` may be committed.
