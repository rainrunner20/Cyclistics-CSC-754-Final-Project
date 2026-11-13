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
