"""Surrogate conflict analysis on synthetic v2 cyclist/car trajectories.

A closing-gap time-to-collision (TTC) proxy and same-point temporal headway
are computed in model patches/seconds. Neither estimates actual crashes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

FIELDS = (
    "tick_s", "type", "agent_id", "x_patch", "lane_y",
    "desired_speed_patches_per_tick", "merged",
)


def _num(text: str, name: str, minimum: float | None = None) -> float:
    try:
        val = float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric {name}") from exc
    if not math.isfinite(val) or (minimum is not None and val < minimum):
        raise ValueError(f"Invalid numeric {name}")
    return val


def _parse_row(row: dict) -> dict:
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise ValueError("Missing/unexpected trajectory fields")
    t = _num(row["tick_s"], "tick_s", 0)
    ident = _num(row["agent_id"], "agent_id", 0)
    if not t.is_integer() or not ident.is_integer():
        raise ValueError("Tick and agent ID must be integers")
    kind = row["type"]
    if kind not in ("car", "cyclist"):
        raise ValueError("Unknown agent type")
    lane = _num(row["lane_y"], "lane_y")
    if lane not in (0, 2):
        raise ValueError("Only experimental lanes 0 and 2 are supported")
    merged = row["merged"]
    if merged not in ("true", "false"):
        raise ValueError("Merged flag must be true or false")
    is_merged = merged == "true"
    if kind == "car" and (lane != 2 or is_merged):
        raise ValueError("Cars must remain on lane 2")
    if kind == "cyclist" and (is_merged != (lane == 2)):
        raise ValueError("Cyclist lane does not match merged flag")
    speed = _num(row["desired_speed_patches_per_tick"], "speed")
    if speed <= 0:
        raise ValueError("Desired speed must be positive")
    return {
        "t": int(t), "kind": kind, "id": int(ident),
        "x": _num(row["x_patch"], "x_patch"),
        "lane": lane, "speed": speed, "merged": is_merged,
    }


def analyze_trajectories(
    rows: list[dict], *, ttc_threshold_s: float = 3.0,
    crossing_gap_threshold_s: float = 2.0, crossing_x: float = 6.5,
) -> dict:
    for value, name in (
        (ttc_threshold_s, "ttc_threshold_s"),
        (crossing_gap_threshold_s, "crossing_gap_threshold_s"),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be positive and finite")
    if not math.isfinite(crossing_x):
        raise ValueError("crossing_x must be finite")

    parsed = [_parse_row(row) for row in rows]
    seen = set()
    by_agent = defaultdict(list)
    by_tick = defaultdict(list)
    for row in parsed:
        key = (row["t"], row["kind"], row["id"])
        if key in seen:
            raise ValueError("Duplicate trajectory agent/tick")
        seen.add(key)
        by_agent[(row["kind"], row["id"])].append(row)
        by_tick[row["t"]].append(row)

    # Input CSV ordering is not trusted; use each agent's time history instead.
    crossings = []
    for (kind, ident), states in sorted(by_agent.items()):
        states.sort(key=lambda s: s["t"])
        for previous, current in zip(states, states[1:]):
            if current["x"] + 1e-9 < previous["x"]:
                raise ValueError("A simulated agent traveled backwards")
            if current["t"] <= previous["t"]:
                raise ValueError("Non-increasing agent timestamp")
            if previous["lane"] == current["lane"] == 2 and (
                previous["x"] < crossing_x <= current["x"]
            ):
                fraction = (crossing_x - previous["x"]) / (current["x"] - previous["x"])
                crossings.append({
                    "kind": kind, "id": ident,
                    "time_s": previous["t"] + fraction * (current["t"] - previous["t"]),
                })

    ttc_values = []
    for t, states in sorted(by_tick.items()):
        cars = [r for r in states if r["kind"] == "car"]
        riders = [r for r in states if r["kind"] == "cyclist" and r["merged"]]
        for rider in riders:
            behind = [car for car in cars if car["x"] < rider["x"]]
            if not behind:
                continue
            car = max(behind, key=lambda c: c["x"])
            closing = car["speed"] - rider["speed"]
            if closing <= 0:
                continue
            # 1.1 patches is the schematic following headway of the model.
            # A zero or negative remaining space is a proxy warning, not a collision.
            gap = max(0.0, rider["x"] - car["x"] - 1.1)
            ttc_values.append(gap / closing)

    cyclists_cross = [x["time_s"] for x in crossings if x["kind"] == "cyclist"]
    cars_cross = [x["time_s"] for x in crossings if x["kind"] == "car"]
    gap_values = [abs(a - b) for a in cyclists_cross for b in cars_cross]
    return {
        "schema": "cyclistics.conflict-proxies.v1",
        "trajectory_rows": len(parsed),
        "modeled_agents": len(by_agent),
        "crossing_x_patch": crossing_x,
        "ttc_threshold_s": ttc_threshold_s,
        "crossing_gap_threshold_s": crossing_gap_threshold_s,
        "ttc_proxy_events": sum(v < ttc_threshold_s for v in ttc_values),
        "min_ttc_s": min(ttc_values) if ttc_values else None,
        "crossing_gap_proxy_events": sum(v < crossing_gap_threshold_s for v in gap_values),
        "min_crossing_gap_s": min(gap_values) if gap_values else None,
        "crossing_gap_description": "same-direction passage-time separation, not validated PET",
        "field_validated": False,
        "crash_probability_estimated": False,
        "unit_note": "patches and 1-second ticks; not calibrated physical meters",
    }


def analyze_csv(input_csv: Path, output_dir: Path) -> dict:
    input_csv = Path(input_csv)
    output_dir = Path(output_dir)
    with input_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Unexpected v2 trajectory header")
        summary = analyze_trajectories(list(reader))
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "summary.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", "utf-8")
    manifest = {
        "schema": "cyclistics.conflict-evidence.v1",
        "rows": summary["trajectory_rows"],
        "field_validated": False,
        "input_sha256": hashlib.sha256(input_csv.read_bytes()).hexdigest(),
        "output_sha256": {
            "summary.json": hashlib.sha256(target.read_bytes()).hexdigest()
        },
        "caveat": "simulated TTC and same-point crossing gaps, not predicted crashes",
    }
    (output_dir / "conflict_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", "utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("outputs/v2_conflicts"))
    args = parser.parse_args()
    result = analyze_csv(args.input, args.outdir)
    print(f"Analyzed {result['rows']} simulated trajectory rows")
    print(f"Saved surrogates and SHA-256 evidence to {args.outdir}")
    print("No real-world crash probabilities or field validation are implied.")


if __name__ == "__main__":
    main()
