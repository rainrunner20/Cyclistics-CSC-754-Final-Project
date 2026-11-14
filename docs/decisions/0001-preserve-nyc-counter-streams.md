# ADR 0001: Preserve NYC bicycle-count streams until their identity is understood

- **Status:** Accepted for the Cyclistics prototype
- **Context:** CSC 754 — Cyclistics data-informed bicycle-lane simulation

## Decision

Keep counts keyed by sensor, mode, granularity, direction, flow ID, and status.
If two flow IDs refer to the same sensor and direction, show both in a report
and require explicit human selection before calibration. We will not sum,
deduplicate, discard, or privilege either one automatically.

The simulation may use a provisional explicitly chosen stream, but the paper
must describe the assumption and unresolved quality/status questions.

## Why

A real Prospect Park West snapshot showed simultaneously reported northbound
flows of 19 and 396 cyclists over the same four hours. The metadata also listed
a historical counter replacement, but did not link flow IDs to the devices.
Treating any of these records as a confirmed duplicate would be speculation.

An easy shortcut would be to pick the highest count or add both counts. That
could silently double-count demand and lead to misleading simulations.

## Consequences and follow-up

This approach is conservative and may require manual work. The benefit is that
the calibration decision is inspectable and reversible. The new diagnostic
reports issues and candidate rates, but **does not certify observed data**.

Before making a real-world inference, check official counter metadata, raw
status meanings, and (where possible) independent reference measurements.
NetLogo results remain synthetic even when arrival demand is NYC-informed.
