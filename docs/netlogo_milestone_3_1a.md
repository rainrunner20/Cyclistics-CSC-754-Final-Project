# Milestone 3.1A — first NetLogo cycling agents

## Implemented

- A stand-alone, interactive, one-lane NetLogo agent-based cyclist model.
- Heterogeneous cyclist speeds (random draw in 0.7–1.3 model units/second).
- Car-following via nearest cyclist ahead; deterministic front-to-back update order.
- Temporary truck obstruction with time-window controls, a hard stop line, and visible truck.
- Synthetic demand with pre-sampled, seeded arrival draws for fair scenario comparison, entrance backlog, queue and wait metrics, and cyclist-conservation reporter.

## CSC 754 connections

A **DEVS atomic model** defines state, input and output, internal/external transitions and time advance. Our Java coupled model advances the event clock through a coordinator. A **NetLogo agent** instead repeatedly executes a small local decision each tick. A visible queue can emerge through many agents following simple local rules.

In this first ABM, the road is painted with stationary **patches**, and bicycles are moving **turtles** with real-valued x positions. This distinction matters: we use space, but the movement dynamics are not a strict integer-cell cellular automaton.

## Verification versus validation

A conservation assertion provides an **internal bookkeeping check**: every attempted synthetic arrival must either have exited, remain on the lane, or still be waiting to enter. A successful model run says nothing by itself about the accuracy of observed NYC cycling delays. DEVS timestamp verification covers a separate deterministic fixture, not the NetLogo model.

## Next work

- Run setup and go using NetLogo 6.4 or 7 and record any runtime/compiler issues.
- Repeat clear vs blockage with matching seeds and report mean, median and variability across multiple seeds.
- Export per-tick metrics to CSV; verify conservation for all recorded ticks.
- Document parameter mapping from NYC count windows to synthetic demand rates without claiming individual trajectories are observed.
- Define a *matched conceptual experiment* for Java and NetLogo or deliberately report differences in model assumptions.
