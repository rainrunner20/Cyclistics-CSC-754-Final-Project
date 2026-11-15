"""Export only explicitly georeferenced scenario markers for the ArcGIS viewer.

No NetLogo patch is assigned a geographic coordinate by assumption.
Source coordinates have to come from a user-supplied, checked WGS84 record.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

FIELDS = frozenset({
    "longitude", "latitude", "location_source", "scenario_id", "event_type",
    "simulated_time_s", "data_status", "mean_queue_cyclists",
})
DATA_STATUSES = {"simulated", "provisional_nyc_count"}
EVENT_TYPES = {"obstruction_start", "obstruction_end", "scenario_result"}


def _number(value: object, name: str, low: float, high: float) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be numeric")
    n = float(value)
    if not math.isfinite(n) or not low <= n <= high:
        raise ValueError(f"{name} outside valid range")
    return n


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{name} must be a short non-empty string")
    return value.strip()


def build_geojson(rows: list[dict]) -> dict:
    if not isinstance(rows, list):
        raise ValueError("GeoJSON inputs must be a list")
    features = []
    for number, item in enumerate(rows):
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ValueError("Unexpected/missing GeoJSON source fields")
        longitude = _number(item["longitude"], "longitude", -180, 180)
        latitude = _number(item["latitude"], "latitude", -90, 90)
        source = _string(item["location_source"], "location_source")
        scenario = _string(item["scenario_id"], "scenario_id")
        kind = item["event_type"]
        if kind not in EVENT_TYPES:
            raise ValueError("Unsupported event type")
        status = item["data_status"]
        if status not in DATA_STATUSES:
            raise ValueError("Unsupported data status")
        t = item["simulated_time_s"]
        if type(t) is not int or not 0 <= t <= 10_000_000:
            raise ValueError("simulated_time_s must be a nonnegative integer")
        count = _number(item["mean_queue_cyclists"], "mean_queue_cyclists", 0, 1e9)
        features.append({
            "type": "Feature",
            "id": number,
            "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
            "properties": {
                "scenario_id": scenario,
                "event_type": kind,
                "simulated_time_s": t,
                "data_status": status,
                "location_source": source,
                "mean_queue_cyclists": count,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def write_geojson(rows: list[dict], output: Path) -> dict:
    doc = build_geojson(rows)  # Validate before touching the output path.
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return doc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="JSON list with georeferenced locations explicitly supplied")
    parser.add_argument("--output", type=Path,
                        default=Path("outputs/v2_map_scenarios.geojson"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    report = write_geojson(data, args.output)
    print(f"Created {len(report['features'])} georeferenced features: {args.output}")
    print("Coordinates must be externally supplied and checked; no NetLogo patch geocoding.")


if __name__ == "__main__":
    main()
