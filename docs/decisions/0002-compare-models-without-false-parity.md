# ADR 0002 — Separate deterministic parity from ABM comparison

- **Status:** Accepted for prototype comparison
- **Context:** Cyclistics CSC 754, milestone 3.5

## Decision

Treat the Python event-queue reference and Java coupled-DEVS implementation as
candidates for **exact deterministic comparison** on one shared event schedule.
Treat NetLogo as a distinct spatial behavioral model and compare its clear and
blocked scenarios **within NetLogo**, reporting differences in assumptions
rather than asserting numerical equivalence with the event-driven models.

## Alternatives considered

- **Compare every numerical metric directly:** rejected. A Python FIFO waiting
  queue is not the same as NetLogo's stopped-rider-plus-pending queue. A
  completed rider's stop time is not the Python server waiting time.
- **Reuse random seed 754 in every model and claim matched arrivals:** rejected.
  Python's continuous Poisson event sampler is not NetLogo's one-second
  Bernoulli sampler. Java's deterministic runner uses explicit timestamps.
- **Wait until all models are coupled:** unnecessary for a limited, accurately
  labeled comparison. A true combined co-simulation is future work.

## Consequences

The resulting report can explain differences in event clocks, movement rules,
state, event scheduling and observable quantities. It cannot claim that a
single fixture validates NYC predictions or that all three engines replay the
same cyclists. Explicit status flags are preferable to a misleading green pass.
