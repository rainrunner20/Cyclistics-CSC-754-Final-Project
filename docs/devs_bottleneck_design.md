# Milestone 2.1C — LaneBottleneck (atomic model)

**Branch:** `feat/devs-atomic-models`  
**Status:** Java atomic-model logic and isolated adapter tests. Actual course DEVSJAVA coordinator integration is **not verified yet**.

## What problem does it solve?

Imagine cyclists entering a narrow bicycle passage. Only one cyclist passes at
once, and each passage takes a fixed number of seconds. If a truck blocks the
lane, new cyclists wait in line. A cyclist who began passing before the truck
arrived finishes that passage; the truck stops only the *next* cyclist.

**Simple flow:** `CyclistGenerator --arrival--> LaneBottleneck <--block/clear-- ObstructionController`.
Later, a coupled DEVS model will make these connections and drive the shared
simulation clock; the atomic smoke tests do **not** simulate a coupled network.

## DEVS specification

An atomic DEVS model is `M = <X, S, Y, delta_int, delta_ext, lambda, ta>`.

- **Inputs X:** bags on `arrival`, `block`, and `clear`.
- **State S:** `blocked` flag, FIFO waiting queue, currently served cyclist,
  number departed, maximum waiting queue, and remaining service time (`sigma`).
- **Outputs Y:** `departed` with cyclist ID when passage finishes.
- **Time advance ta:** `passageSeconds` when serving (minus time elapsed);
  infinity while idle/blocked with no cyclist currently passing.
- **Internal transition delta_int (`deltint`):** finish the in-service cyclist;
  increment departed; if unblocked, start the first waiting cyclist.
- **External transition delta_ext (`deltext`):** subtract elapsed time from
  remaining passage time; process control signals; queue arriving cyclists;
  start passage only if unblocked and idle.
- **Output lambda (`out`):** announce the cyclist who finishes **before** the
  internal state changes. Passive models emit nothing.
- **Confluent transition (`deltcon`):** when a scheduled departure coincides
  with external inputs, complete the departure first, then apply the new inputs.

## Important policy decisions (good for a presentation/Q&A)

1. **First-in, first-out:** waiting cyclists leave in arrival order. Simultaneous
   arrivals use the order in the DEVS message bag (no overtaking yet).
2. **A blockage does not interrupt an active passage.** It only prevents the
   next cyclist from starting. This matches the current Python reference model.
3. **BLOCK beats CLEAR on a tie.** If conflicting control signals arrive at the
   same simulation timestamp, the lane remains blocked, avoiding an illegal
   passage during the new obstruction.
4. **Peak queue counts *waiting* cyclists only**, not the cyclist currently
   being served. This should be stated explicitly in all comparisons.
5. **Fixed service headway is an assumption**, not an empirical observation
   from NYC bicycle counters. The calibration dataset estimates arrival rate,
   not the bicycle passage time.

## Run the isolated tests in VS Code PowerShell

From the Cyclistics project root:

```powershell
docker build -f devsjava/Dockerfile.bottleneck-tests -t cyclistics-bottleneck-tests devsjava
docker run --rm cyclistics-bottleneck-tests
```

Then regression-test prior features:

```powershell
docker run --rm cyclistics-generator-tests
docker run --rm cyclistics-obstruction-tests
docker compose run --build --rm tests
```

The `test_support` package intentionally mimics only a few DEVSJAVA method
signatures. A pass means the model's transition logic works against that test
adapter; it does **not** prove compatibility with Dr. Gu's official DEVSJAVA
library or the real atomic/coupled coordinators.

## Next milestone

Compile all three atomic models with the **actual course DEVSJAVA library**,
then connect their ports in a coupled DEVS model and compare scenarios against
the Python reference simulation. Define matching input schedules and event-tie
rules before claiming cross-implementation agreement.
