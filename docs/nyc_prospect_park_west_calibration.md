# NYC Bicycle Counter — Prospect Park West

## Data discovery

Source: NYC DOT / NYC Open Data
Sensor ID: 100009425
Location: Prospect Park West, Brooklyn
Date: 2026-10-15
Time window: 08:00–12:00, NYC local time
Measurement interval: PT15M (15 minutes)

## Retrieved observations

64 records across four measurement streams.

- Inbound: flow IDs 101009425 and 353237827
- Outbound: flow IDs 102009425 and 353237830
- Each stream contains 16 observations.
- Reported status: raw

## Calibration considerations

The streams must not be summed without checking for overlapping measurements.

The provisional calibration stream is inbound flow 101009425.

The meaning and quality of raw-status observations require further verification.

Observed bicycle counts may inform the simulation arrival rate, but simulated queues and delays remain hypothetical.

Raw downloaded observations and generated outputs are stored locally and excluded from Git.

## NYC-informed NetLogo experiment — November 13, 2026

### Selected calibration input

We tested a northbound bicycle-count stream from Prospect Park West.

- Sensor: 100009425
- Flow: 353237827
- Direction: in / northbound
- Observation period: October 15, 2026, 08:00–12:00
- Measurement interval: 15 minutes
- Observations: 16
- Recorded cyclists: 396
- Estimated mean demand: 99 cyclists/hour
- Reported data status: raw

The source data contain multiple streams with overlapping directional
names. We selected one stream explicitly rather than combining their
counts. The relationship between these flows and the physical counter
devices still needs investigation.

### Controlled NetLogo comparison

We imported the estimated hourly demand into NetLogo and ran the clear
and blocked scenarios using random seed 754.

Both scenarios generated the same 13 requested cyclists during the
600-second simulation.

| Metric | Clear | Blocked |
| --- | ---: | ---: |
| Requested cyclists | 13 | 13 |
| Departed cyclists | 12 | 12 |
| Peak queue | 0 | 3 |
| Mean queue | 0.000 | 0.158 |
| Mean stopped time among departed riders (s) | 0.000 | 7.917 |

The obstruction increased queueing and stopped time without changing
the number of departures within this particular simulation horizon.

### Verification and limitations

The calibration bridge verified the selected demand rate, matching
scenario inputs, and cyclist conservation. The generated report retains
the source snapshot hash and experiment settings.

The observations inform only the simulation's mean arrival rate.
Cyclist speeds, arrival times, queues, and obstruction effects remain
synthetic.

This single experiment is not sufficient to estimate uncertainty.
We should repeat the calibrated comparison across multiple seeds.

We also need to investigate duplicate directional streams and the
meaning of the raw status before treating the selected count stream
as a reliable representation of local bicycle demand.
