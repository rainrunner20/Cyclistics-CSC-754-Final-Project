"""Deterministic, versioned obstruction-event replay for experimental Cyclistics v2.

Nothing here reads a camera, advances DEVS-Suite, or claims live co-simulation.
An approved observation only becomes a *hypothetical scenario input*.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .observation_contract import validate_observation

EVENT_SCHEMA = "cyclistics.simulation-event.v1"
EVENT_FIELDS = frozenset({
    "schema", "event_id", "scenario_id", "source", "source_observation_id",
    "simulated_time_s", "event_type", "segment_id",
})
EVENT_KINDS = ("obstruction_start", "obstruction_end")
ALLOWED_SOURCES = frozenset({"synthetic_fixture", "manual_review", "roboflow"})


def _label(obj: Any, field: str, optional: bool = False) -> str | None:
    if optional and obj is None:
        return None
    if not isinstance(obj, str) or not obj.strip() or len(obj) > 128:
        raise ValueError(f"{field} requires a nonempty string (up to 128 characters)")
    return obj.strip()


def _tick(obj: Any, field: str) -> int:
    if type(obj) is not int or obj < 0 or obj > 10_000_000:
        raise ValueError(f"{field} must be a nonnegative integer simulated second")
    return obj


def _event(row: Mapping[str, Any]) -> dict:
    if not isinstance(row, Mapping):
        raise ValueError("Event must be a JSON mapping")
    if set(row) != EVENT_FIELDS:
        raise ValueError(
            f"Missing/Unexpected event fields: missing={sorted(EVENT_FIELDS-set(row))}, "
            f"unexpected={sorted(set(row)-EVENT_FIELDS)}"
        )
    if row["schema"] != EVENT_SCHEMA:
        raise ValueError("Unsupported event schema")
    kind = row["event_type"]
    if kind not in EVENT_KINDS:
        raise ValueError("Unrecognized event type")
    source = _label(row["source"], "source")
    if source not in ALLOWED_SOURCES:
        raise ValueError("Unrecognized source")
    return {
        "schema": EVENT_SCHEMA,
        "event_id": _label(row["event_id"], "event_id"),
        "scenario_id": _label(row["scenario_id"], "scenario_id"),
        "source": source,
        "source_observation_id": _label(row["source_observation_id"],
                                        "source_observation_id", optional=True),
        "simulated_time_s": _tick(row["simulated_time_s"], "simulated_time_s"),
        "event_type": kind,
        "segment_id": _label(row["segment_id"], "segment_id"),
    }


def validate_events(rows: list[dict]) -> list[dict]:
    """Deduplicate identical messages, order by tick, and reject invalid block windows."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("A nonempty list of events is required")
    by_id = {}
    for row in rows:
        item = _event(row)
        existing = by_id.get(item["event_id"])
        if existing is not None and existing != item:
            raise ValueError(f"Conflicting duplicate event ID: {item['event_id']}")
        by_id[item["event_id"]] = item
    unique = list(by_id.values())
    scenarios = {item["scenario_id"] for item in unique}
    segments = {item["segment_id"] for item in unique}
    if len(scenarios) != 1:
        raise ValueError("Single scenario required per replay package")
    if len(segments) != 1:
        raise ValueError("Single segment required in the first v2 model")
    unique.sort(key=lambda v: (v["simulated_time_s"],
                               EVENT_KINDS.index(v["event_type"]), v["event_id"]))
    blocked = False
    last_start = None
    for row in unique:
        if row["event_type"] == "obstruction_start":
            if blocked:
                raise ValueError("Overlapping obstruction start")
            blocked = True
            last_start = row["simulated_time_s"]
        else:
            if not blocked:
                raise ValueError("Unmatched obstruction end")
            if row["simulated_time_s"] <= last_start:
                raise ValueError("obstruction end must follow its start")
            blocked = False
    if blocked:
        raise ValueError("Unclosed obstruction at end of event sequence")
    return unique


def event_from_reviewed_observation(
    observation: Mapping[str, Any], *, approved: bool,
    start_tick: int, duration_s: int, scenario_id: str,
) -> tuple[dict, dict]:
    """Make *scenario* events only after explicit human review.

    start_tick is selected by the experimenter; camera wall time must not be
    silently converted to a NetLogo tick.
    """
    item = validate_observation(observation)
    if item["lane_overlap"] is not True or item["segment_id"] is None:
        raise ValueError("An independent lane-overlap review and segment ID are required")
    if approved is not True:
        raise ValueError("Explicit approval is required before scenario creation")
    start = _tick(start_tick, "start_tick")
    duration = _tick(duration_s, "duration_s")
    if duration == 0 or start + duration > 10_000_000:
        raise ValueError("duration_s must be positive within the clock range")
    scenario = _label(scenario_id, "scenario_id")
    base = {
        "schema": EVENT_SCHEMA,
        "scenario_id": scenario,
        "source": item["source"],
        "source_observation_id": item["observation_id"],
        "segment_id": item["segment_id"],
    }
    return (
        dict(base, event_id=f"{item['observation_id']}:block-start",
             simulated_time_s=start, event_type="obstruction_start"),
        dict(base, event_id=f"{item['observation_id']}:block-end",
             simulated_time_s=start + duration, event_type="obstruction_end"),
    )


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_replay_package(rows: list[dict], output_dir: Path) -> dict:
    ordered = validate_events(rows)  # Do not create outputs for malformed inputs.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log = output_dir / "simulation_events.json"
    log.write_text(json.dumps(ordered, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = output_dir / "netlogo_obstruction_events.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["time_s", "event_type"])
        for row in ordered:
            writer.writerow([row["simulated_time_s"], row["event_type"]])
    output_names = ["simulation_events.json", "netlogo_obstruction_events.csv"]
    manifest = {
        "schema": "cyclistics.replay-package.v1",
        "scenario_id": ordered[0]["scenario_id"],
        "segment_id": ordered[0]["segment_id"],
        "event_count": len(ordered),
        "field_validated": False,
        "live_coupled": False,
        "replay_status": "validated_deterministic_schedule_only",
        "clock": "integer simulated seconds; no wall-clock mapping",
        "output_sha256": {name: _digest(output_dir / name) for name in output_names},
    }
    (output_dir / "replay_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True, type=Path,
                        help="JSON list of explicitly authorized simulation events")
    parser.add_argument("--outdir", default=Path("outputs/v2_replay"), type=Path)
    args = parser.parse_args()
    rows = json.loads(args.events.read_text(encoding="utf-8"))
    result = build_replay_package(rows, args.outdir)
    print(f"PASS: archived {result['event_count']} deterministic scenario events")
    print(f"Outputs: {args.outdir}")
    print("NOTE: this is offline replay, not live NetLogo/DEVS co-simulation.")


if __name__ == "__main__":
    main()
