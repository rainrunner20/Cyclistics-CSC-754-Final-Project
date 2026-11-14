# CyclistGenerator: Atomic DEVS design (Milestone 2.1A)

## The problem

Cyclists need to enter our simulated lane at known times. The generator's job is to schedule and emit arrivals; it does not move cyclists or decide what happens at the obstruction.

## DEVS specification

- **Input port (X):** `stop`, an external signal that cancels future cyclist arrivals.
- **Output port (Y):** `arrival`, carrying identifiers such as `cyclist-1`.
- **State (S):** the ordered list of arrival timestamps, index of the next arrival, phase (`scheduled` or `passive`), and time until the next internal event (sigma).
- **Time advance `ta`:** seconds until next scheduled arrival; infinity when passive.
- **Output function `lambda`:** emit the cyclist currently due on the `arrival` port immediately before the corresponding internal transition.
- **Internal transition `delta_int`:** advance the schedule index and set sigma to the next interarrival interval, or passivate when finished.
- **External transition `delta_ext`:** on `stop`, passivate; otherwise preserve the remaining wait.
- **Confluent transition `delta_con`:** when an arrival and stop occur together, emit that due arrival, update the schedule, then apply the stop to prevent future arrivals.

## Why deterministic first?

We already have a Python reference model using a seeded Poisson process and a NYC-data-derived hourly rate. For this first Java atomic model we use *explicit timestamps* so event-ordering bugs are easier to detect. Later, Python can produce a seeded schedule for the Java generator. `evenlySpaced()` is for predictable smoke tests, **not** a Poisson process.

## What this does not establish yet

- The test-support classes imitate just enough of common DEVSJAVA method names for unit tests. They are not Dr. Gu's DEVSJAVA library or event coordinator.
- We have not tested compilation or execution with the professor's DEVSJAVA distribution.
- We have not connected other atomic models or implemented NetLogo.

## What to observe and write in your development journal

Record the actual command used, the assertions passed, and one thing that initially confused you (if any). Try explaining why `ta` becomes 5 after arrival at second 10 when the next arrival is second 15.
