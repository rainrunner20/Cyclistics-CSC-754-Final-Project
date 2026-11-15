# Cyclistics — delivered scope and research questions

## Research aim

Cyclistics explores how temporary bicycle-lane obstructions affect queues **inside an idealized, single-lane simulation**. It compares multiple simulation formalisms as a teaching and engineering exercise, not as a verified road-safety forecast for a specific NYC street.

The developed system reports **synthetic** model responses, internal verification results, and a hardware-specific computational runtime study. Some official NYC cyclist counts are used to construct **provisional arrival-rate inputs**, but the queue and delay outputs have not been externally validated.

## Implemented questions

1. **Demand and obstruction duration:** how do 150/300/600/900 attempted cyclists per hour and 0/30/60/120-second blockages affect NetLogo's *average waiting count* and *peak waiting count*? Answered in [160 paired records and 16 summaries](research_sensitivity_findings.md).
2. **Clearance policies:** how do different obstruction intervals affect the Python FIFO bottleneck under the **same** synthetic arrival schedule? See reproducible scenarios in [README](../README.md).
3. **Correctness of a shared event schedule:** do the Python reference and a real historical Java DEVS-Suite coordinator report departures at 14 and 24 seconds for the two-cyclist fixture? [Yes, for this fixture](cross_model_comparison_results.md).
4. **Computational cost:** how long do 600- and 1,200-tick NetLogo runs take under three demand settings with/without obstruction on a specific GitHub-hosted Linux runner? [36 actual runtime measurements](performance_evidence_results.md), with strong caveats about millisecond-level jitter.

## What the three models represent

**Python DES** represents discrete arrivals, obstruction transitions and a single FIFO server using an event queue. It reports wait and completion metrics. Its fixed passage times and stochastic arrival assumptions are not reconstructed cyclist trajectories.

**Java DEVS-Suite** includes a `CyclistGenerator`, `ObstructionController`, and `LaneBottleneck` connected by `CyclisticsCoupledModel`. The historical external coordinator manages discrete-event timing. A formal atomic model can be written as `M = (X, S, Y, δint, δext, λ, ta)` plus `δcon` for coincident internal/external events. See [bottleneck design](devs_bottleneck_design.md), [generator design](devs_generator_design.md), [obstruction design](devs_obstruction_design.md), and [coupled port diagram](devs_coupled_model.md).

**NetLogo ABM** places cyclist agents on a spatially schematized single lane and updates movement, obstruction and waiting every second. The adjacent asphalt and sidewalk are visualization only; modeled riders do not overtake or change lanes, and there is no simulation of motor traffic or crashes.

The systems are run and verified **separately**. The Java atomic models are coupled *within* Java using DEVS ports; NetLogo is not synchronously coupled to Java.

## Data and measurement boundaries

- NYC DOT bicycle/pedestrian count snapshots and sensor metadata are accessed with read-only tooling. The [Prospect Park West experiment](nyc_prospect_park_west_calibration.md) used an explicitly selected **raw** count stream to construct a provisional 99 cyclists/hour input.
- Multiple directional flow records at the same sensor cannot be assumed independent or summed. Device mapping, raw status, time-zone/granularity interpretation and segment correspondence require review.
- An observed counter volume can support a candidate mean arrival rate. It cannot, without further data, validate modeled cyclist waiting, obstruction durations, lane-changing, collisions or safety improvements.
- In the NetLogo sensitivity study, *mean queue* is the time-average **count of waiting/pending cyclists**. It is not mean travel delay; peak-queue difference is averaged across matched replicates.
- Replicate uncertainty quantifies variation **under the simulation's rules**, not the uncertainty of real NYC street predictions.
- The NetLogo performance study measures **wall-clock computation** on GitHub's runner, not cyclists' simulated waiting time.

## Verification versus validation

- **Verification implemented:** deterministic replay, absence of spontaneous cyclists under zero demand, cyclist conservation, obstruction active during its scheduled interval, paired random-input checks, Python tests, one Java/Python event-time fixture and real NetLogo headless execution.
- **Validation not established:** independently measured queues, waiting-time trajectories, blocked-lane durations or collision outcomes on the modeled NYC segment.

## Deferred features

The earlier proposal considered Roboflow camera detection, ArcGIS, event-trace interoperability, lane-changing behavior, traffic conflict exposure and real-time digital-twin feedback. These remain **future work**; neither their integration nor the related safety metrics are present in the verified core implementation.

For the final report, use this delivered scope and the [final submission status](final_submission_status.md). Earlier milestone files record the team's evolving ideas and should not be mistaken for claims of completed features.
