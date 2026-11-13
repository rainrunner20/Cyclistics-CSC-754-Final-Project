# NYC bicycle-counter quality checks (Cyclistics 3.4A)

## Problem observed

The October 15, 2026, 08:00–12:00 NYC Open Data snapshot for sensor
`100009425` (Prospect Park West) contained **64 records**: four simultaneous
15-minute streams, each with 16 observations. Two northbound stream IDs
(`101009425`, `353237827`) reported 19 versus 396 cyclists; two southbound
IDs (`102009425`, `353237830`) reported 215 versus 40. All were marked `raw`.

The separate sensor-metadata request also returned **two physical counter IDs**
for this sensor: `15045` (detached in May 2022) and `33903` (installed that month).
There is no demonstrated mapping from a flow ID to a particular physical
counter. We must **not** infer that a flow is obsolete just because an earlier
counter was replaced.

## Scope

Make a reproducible, **read-only diagnostic report** from an NYC count snapshot.
It must not modify observations, choose the largest flow, label `raw` as
validated, or silently add overlapping directional streams. No attempt is
made to infer travel times, queues or conflict risk from these count records.

## Rules and severity

| Condition | Action | Why |
| --- | --- | --- |
| Missing required record fields, invalid timestamp or negative/fractional count | Reject file | Cannot trust the reported numbers |
| Duplicate timestamps within one stream | Flag; disallow rate candidate | Each sample would otherwise be counted twice |
| Missing timestamps between samples at the declared interval | Flag; disallow rate candidate | The observed duration is ambiguous |
| Unknown count granularity | Flag; disallow rate candidate | Avoid inventing interval length |
| Fewer than two observations | Flag; disallow rate candidate | Insufficient evidence for a rate |
| Multiple flow IDs with the same sensor, mode, direction and granularity | Flag for manual review | Data may overlap; no automatic summation |
| `raw` or other status values | Preserve and flag as not quality-assured | Status meanings need source documentation |
| Multiple physical counter records with the same sensor ID | Report separately | Hardware history does not resolve flow identity |
| Valid isolated bicycle stream | Compute a **candidate** hourly rate | Input calibration only; not field validation |

Streams are separated by `(sensor_id, travelmode, granularity, direction,
flowid, status)`. Comparison groups omit `flowid` and `status` to detect
ambiguous directional streams. The report preserves all groups without merging.

## Acceptance criteria

- Running the CLI against the saved Prospect Park West snapshot reports four
  streams and two ambiguous same-direction groups, not a combined volume.
- The candidate hourly rates, when no gaps/duplicates exist, are 4.75, 99,
  53.75 and 10 riders/hour for the four observed streams (order not significant).
- Results clearly state that `raw` remains unverified and that no field
  accuracy claim is established.
- Altering a test fixture to contain duplicated timestamps or missing
  quarter-hours produces a warning and no computed candidate rate.
- Malformed measurements cause a nonzero command exit; no partial report
  should be written in that case.
- Report records the SHA-256 of the input snapshot for reproducibility and
  accepts optional separate sensor metadata to report physical counter IDs.

## What comes after this increment

3.4B: write unit tests for the above acceptance criteria (red phase).
3.4C: implement and run the diagnostic CLI (green phase).
3.4D: check the actual local NYC snapshot and record findings; investigate
status codes and device/flow mapping before selecting an observation stream
for publication-quality evidence.
