# Cyclistics — scope, design, and experiments

## Scope and core hypothesis
An idealized NYC bicycle-lane segment is the case study. The target outcomes are *simulation estimates* of delay, queue length, passage throughput, and lane-change exposure when an obstruction occurs. No inference about actual crash probability is justified.

**Questions**
1. How does blockage duration change average/p95 cyclist delay and maximum queue?
2. Does shorter obstruction-clearance time reduce delay?
3. How do cyclist demand and behavioral differences affect queueing and lane-change exposure?
4. Which model assumptions materially change the results (sensitivity analysis)?

## Dataflow

```
NYC bicycle counts + bike routes (+ 311 descriptive indicators)
                 | parameter extraction, quality checks
                 v
         Python inputs/scenarios
                 | event list reference + CSV export
                 v
      DEVSJAVA event model (planned)
         | atomic generator, obstruction controller, bottleneck service
         | coupled wiring + clocks + simultaneous-event semantics
                 v
      event CSV (timestamps and blockage state)
                 v
        NetLogo ABM (planned)
         | cyclist turtles, lane patches, heterogenous behavior
         | measures queue, passing, stopping, merge exposure
                 v
      repeated runs, comparison, uncertainty, plots
                 v
        optional ArcGIS visual/report (not core)
```

**Important integration nuance:** Java DEVS models may be *coupled to each other* using DEVSJAVA ports. Transferring DEVSJAVA event traces into NetLogo via CSV is an **offline sequential pipeline**, not a single tightly coupled DEVS-NetLogo co-simulation. Do not call the latter a coupled DEVS model.

## Planned DEVSJAVA atomic models
- `CyclistGenerator`: internal events schedule cyclist-arrival outputs at event times.
- `ObstructionController`: emits blocked/cleared control events (scheduled exogenous windows), including a clearance-policy parameter.
- `LaneBottleneck`: state = `(phase, queue, server_state, next_service_time)`; external inputs = cyclist arrival or obstruction state; internal transition = service completion; outputs = cyclist departure/queue samples.
- `CyclisticsCoupled`: EIC/EOC/IC wiring generator/controller/bottleneck; deterministic confluence policy for simultaneous event arrivals.

Formalism to include in report: `M = <X, S, Y, δint, δext, λ, ta>` and elapsed time `e` on external transitions. Explicitly document whether the framework requires a confluent transition `δcon` at same-time internal and external events; do not assume any generic priority order is the DEVSJAVA default.

## Planned NetLogo ABM
- Patches represent segment locations / bike lane and adjacent traffic-exposure area.
- Turtles represent cyclists; parameters = desired speed, patience, cautious/aggressive merge preference.
- At each tick (e.g., 1 simulated second), rider moves, slows/stops, waits, or merges to pass a blocked segment according to local rules.
- Obstruction state changes imported using event CSV timestamps from the reference/DEVS model. A tick-based ABM approximates time by rounding or interpolating event times; document that the models use different time advancement rules.
- If adjacent motor traffic is not explicitly simulated, label outcomes *merge exposure* rather than measured collisions or crash risk.

## NYC data
- NYC DOT `Bicycle and Pedestrian Counts` dataset (`ct66-47at`) for empirical arrival-rate/time-of-day inputs where coverage exists.
- Sensor locations (`6up2-gnw8`) to associate counts with geography.
- NYC `New York City Bike Routes` (`mzxg-pwib`) for lane geometry / type.
- NYC 311 `Blocked Bike Lane` under Illegal Parking as a complaint indicator, not as actual blockade duration / incidence ground truth.
- **Start with synthetic rates** until a sensor/segment match is vetted. A counter may not be located on the exact segment modeled.

## Experimental plan
- At least 4 scenarios: clear, blocked 5 min, cleared after 1 min, repeated obstruction.
- Parameter sweeps: demand 150/300/450 per hour; blockage 1/3/5 minutes; behavior mixes; service headway / max density.
- Repeated seeds (at least 10 per condition for final analysis; e.g., 30 if time permits).
- Report mean/p95 delay, max queue, throughput; in ABM: stopping events and merge exposure.
- Compare clear-vs-blocked under identical arrival seeds; report uncertainty (mean and spread).

## Verification and validation
- Verification: zero-demand test, deterministic-seed test, block increases delay under test inputs, correct event-time tie handling, conservation of cyclists, no negative queue lengths, obstruction end unblocks service.
- Sensitivity: vary assumptions, show which patterns remain stable.
- Validation: if feasible, compare simulated *unobstructed cyclist counts* aggregated to observed counter intervals; where no matched ground truth exists, state results demonstrate **scenario behavior** not predictive accuracy. Counts cannot independently validate queue lengths, blockage durations, or individual delays.
- Runtime: benchmark number of events/agents vs wall-clock time; distinguish Python, DEVSJAVA, NetLogo setups.

## Implementation milestones
1. Python reference and deterministic tests (this starter).
2. Formal DEVS model specification and DEVSJAVA atomic/coupled implementation.
3. NetLogo animation, agents, patches and event ingestion.
4. NYC data selection, observed-demand calibration, experiments and multiple random seeds.
5. Validation limits, charts, paper/demo; CV/ArcGIS only if time remains.
