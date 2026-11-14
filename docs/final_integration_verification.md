# Final integration verification — CSC 754 Cyclistics

## Integration checkpoint — November 14, 2026

The working integration branch `feat/final-integration` combines the previously separate Python discrete-event reference, NetLogo bicycle-lane ABM, NYC data preparation/quality checks, and DEVS-Suite Java atomic/coupled models. It is not yet the final released `main` branch.

Commits observed in the local integration run:

- `9ca924d` — NetLogo street visualization merged into `feat/netlogo-abm`.
- `1b8def4` — removed the external DEVS-Suite JAR from *tracked* Git files, keeping the local dependency available for execution.
- `175e471` — merged `feat/devs-atomic-models` into `feat/final-integration`.

The merge was conflict-free and the resulting working tree was clean after pushing. The original development branches are preserved.

## Observed checks

| Check | Evidence | Outcome |
| --- | --- | --- |
| Python tests | `docker compose run --build --rm tests`, repeated twice after merging Java sources | **139 / 139 passed**, both runs |
| External Java API compatibility | `devsjava/scripts/verify-real-devsjava.ps1` | Required external classes found; **5 production models compiled** |
| Real DEVS-Suite coupled run | `devsjava/scripts/run-real-coupled.ps1` | Coordinator ran normally, departures at **14.000 s** and **24.000 s** |
| Coordinator accounting | Java run summary | 2 generated, 2 departed, 2 obstruction events, maximum waiting queue 1, remaining 0 |
| Desktop NetLogo visualization | Prior Milestone 3.6 desktop execution | Model executed to tick 600; cyclist conservation true |
| NetLogo visual regression | Prior pre-visual versus green-lane experiment (seed 754) | Baseline/enhanced paired CSV exports had matching SHA-256 hashes |
| Standalone Java adapter smoke suites | Five Docker builds and runs from the integrated branch | **All five passed**, 199 total assertions (24 generator, 58 obstruction, 87 bottleneck, 11 coupled-structure, 19 timestamp) |
| GitHub Actions on PR #5 | [Run 43610161737](https://github.com/rainrunner20/Cyclistics-CSC-754-Final-Project/actions/runs/43610161737) on `a819a04` | **All four jobs passed**: Python 3.11, 3.12, 3.13 and Docker smoke test |

The coordinator output from the integration run:

```text
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

The shared deterministic fixture has arrivals at 10 s and 15 s, obstruction from 12 s to 20 s, and a 4-second service headway. Agreement is limited to this case; NetLogo runs a separate spatial, stochastic experiment.

## Reproduction (Windows PowerShell)

From a clean checkout of the integration branch, with Docker Desktop running:

```powershell
docker compose run --build --rm tests
```

The external library is not distributed in Git. Place a compatible DEVS-Suite JAR in `devsjava/vendor/` locally, then run:

```powershell
.\devsjava\scripts\verify-real-devsjava.ps1
.\devsjava\scripts\run-real-coupled.ps1
```

Run the Java *adapter-level* smoke tests separately. They do **not** use the external library or prove real-coordinator correctness:

```powershell
$suites = @('generator', 'obstruction', 'bottleneck', 'coupled-structure', 'timestamp')
foreach ($suite in $suites) {
    $image = "cyclistics-devs-$suite-tests"
    docker build --file "devsjava/Dockerfile.$suite-tests" --tag $image devsjava
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $suite" }
    docker run --rm $image
    if ($LASTEXITCODE -ne 0) { throw "Smoke test failed: $suite" }
}
```

Keep generated logs and `outputs/` untracked. Do not commit third-party JARs.

## Verification versus validation

These checks demonstrate internal consistency, test coverage, and a successful run of the real historical DEVS-Suite coordinator. They do **not** establish equivalence to the exact CSC 754 course-distributed Java library, statistical equivalence among three simulation formalisms, or validated real-world NYC cyclist waiting times. NYC bicycle-counter data can inform a demand-rate input without validating queue or safety predictions.

The current street view is a schematic, single-lane NetLogo demonstration, not a measured NYC road network or live sensor-linked digital twin.

## Remaining release checks

1. **Completed:** five Java adapter smoke suites passed (199 assertions).
2. **Completed:** GitHub Actions passed for PR #5 (`a819a04`): three Python versions and Docker.
3. **Completed:** project documentation, model scope, and local dependency guidance reviewed and updated; PowerShell diff whitespace check passed and working tree was clean.
4. **Pending:** final review and squash merge PR #5 into `main`, preserving all original feature branches and worktrees. Recheck the exact PR head and CI status if any further commits are made.
