"""Turn selected NYC bicycle-counter observations into a simulation arrival-rate estimate.

The output is a *parameter estimate*, not a replay of individual cyclists or
proof that our simulator predicts real traffic. The discrete-event simulation
still generates synthetic arrivals using the estimated mean.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from .nyc_open_data import BASE_URL, DATASETS, request_json, validate_records

SCHEMA = "cyclistics.arrival-rate.v1"


def _local_timestamp(value: str) -> datetime:
    """Accept explicit local timestamps; the NYC dataset uses floating timestamps."""
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid timestamp {value!r}; expected YYYY-MM-DDTHH:MM:SS") from exc
    if parsed.tzinfo is not None:
        raise ValueError("Use a timezone-free timestamp matching NYC dataset's local clock")
    return parsed


def _soql_text(value: str) -> str:
    """Quote a string literal for SoQL; never interpolate unescaped user text."""
    if not value or any(ord(character) < 32 for character in value):
        raise ValueError("Invalid empty/control-character sensor ID")
    return "'" + value.replace("'", "''") + "'"


def build_window_url(sensor_id: str, start: str, end: str, limit: int, offset: int) -> str:
    """Ask NYC for one counter and a bounded local-time range (not all 21M rows)."""
    first, last = _local_timestamp(start), _local_timestamp(end)
    if first >= last:
        raise ValueError("--start must be earlier than --end")
    if type(limit) is not int or not 1 <= limit <= 1000 or type(offset) is not int or offset < 0:
        raise ValueError("Invalid pagination settings")

    # We only filter on counter and time here. Filtering mode/status/flow during
    # calibration makes it easier to detect duplicates and overlapping streams.
    condition = (f"sensor_id = {_soql_text(sensor_id)} "
                 f"AND timestamp >= '{first.isoformat()}' "
                 f"AND timestamp < '{last.isoformat()}'")
    query = urlencode({
        "$where": condition,
        "$order": "timestamp ASC, flowid ASC, direction ASC, travelmode ASC",
        "$limit": limit,
        "$offset": offset,
    })
    return f"{BASE_URL}/{DATASETS['counts']['id']}.json?{query}"


def fetch_window(sensor_id: str, start: str, end: str, max_records: int = 3000,
                 page_size: int = 1000) -> dict:
    """Fetch bounded pages and *refuse* a potentially incomplete snapshot."""
    if type(max_records) is not int or not 1 <= max_records <= 10000:
        raise ValueError("--max-records must be between 1 and 10000")
    if type(page_size) is not int or not 1 <= page_size <= 1000:
        raise ValueError("Invalid page size")

    rows: list[dict] = []
    first_url = build_window_url(sensor_id, start, end, min(page_size, max_records), 0)
    while len(rows) < max_records:
        url = build_window_url(sensor_id, start, end,
                               min(page_size, max_records - len(rows)), len(rows))
        page = validate_records("counts", request_json(url))
        rows.extend(page)
        if len(page) < min(page_size, max_records - (len(rows) - len(page))):
            break
    else:
        # Even if exactly 3,000 rows were returned, we cannot know whether a
        # 3,001st row exists. Never silently calibrate a truncated dataset.
        extra_url = build_window_url(sensor_id, start, end, 1, len(rows))
        if validate_records("counts", request_json(extra_url)):
            raise ValueError("The result exceeds --max-records; choose a smaller window or increase the cap")

    return {
        "source": "NYC Open Data / NYC Department of Transportation",
        "dataset": "counts",
        "dataset_id": DATASETS["counts"]["id"],
        "sensor_id": sensor_id,
        "start_local": _local_timestamp(start).isoformat(),
        "end_local_exclusive": _local_timestamp(end).isoformat(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "first_query_url": first_url,
        "record_count": len(rows),
        "records": rows,
    }


def _read_snapshot(path: Path) -> dict:
    """Load a saved data snapshot and fail loudly on malformed inputs."""
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("records"), list):
        raise ValueError("Expected a saved NYC snapshot with a 'records' list")
    if snapshot.get("dataset") != "counts" or snapshot.get("dataset_id") != DATASETS["counts"]["id"]:
        raise ValueError("This is not a Cyclistics NYC bicycle-count snapshot")
    validate_records("counts", snapshot["records"])
    return snapshot


def inspect_counts(snapshot: dict) -> list[tuple[tuple[str, ...], int]]:
    """Show distinct streams so we don't accidentally add totals and directions."""
    groups = Counter(
        tuple(str(row.get(key, "<missing>")) for key in
              ("sensor_id", "travelmode", "granularity", "direction", "flowid", "status"))
        for row in snapshot["records"]
    )
    return sorted(groups.items(), key=lambda item: (-item[1], item[0]))


def calibrate(snapshot: dict, *, sensor_id: str, mode: str, granularity: str,
              interval_minutes: float, direction: str | None = None,
              flow_id: str | None = None, status: str | None = None,
              input_sha256: str | None = None) -> dict:
    """Estimate cyclists/hour from a contiguous, *single* measurement stream.

    We require an explicit interval size because the text granularity label
    alone does not prove the duration represented by each count.
    """
    if not math.isfinite(interval_minutes) or interval_minutes <= 0:
        raise ValueError("--interval-minutes must be finite and positive")
    if not sensor_id or not mode or not granularity:
        raise ValueError("Select --sensor-id, --mode and --granularity from inspect output")
    validate_records("counts", snapshot["records"])

    filtered = [row for row in snapshot["records"]
                if str(row.get("sensor_id", "")) == sensor_id
                and str(row.get("travelmode", "")) == mode
                and str(row.get("granularity", "")) == granularity
                and (direction is None or str(row.get("direction", "<missing>")) == direction)
                and (flow_id is None or str(row.get("flowid", "<missing>")) == flow_id)
                and (status is None or str(row.get("status", "<missing>")) == status)]
    if len(filtered) < 2:
        raise ValueError("Need at least two observations for one selected counter/stream")

    # Directional flows and total flows can describe the same cyclists. We
    # refuse mixed streams instead of quietly double counting them.
    streams = {tuple(str(row.get(key, "<missing>")) for key in
                     ("direction", "flowid", "status")) for row in filtered}
    if len(streams) != 1:
        raise ValueError("Multiple direction/flow/status streams found. Use inspect, then "
                         "specify --direction, --flow-id and/or --status.")

    seen: set[datetime] = set()
    dated: list[tuple[datetime, int]] = []
    for row in filtered:
        t = _local_timestamp(str(row["timestamp"]))
        if t in seen:
            raise ValueError(f"Duplicate measurement timestamp {t.isoformat()} in the same stream")
        seen.add(t)
        count = float(row["counts"])
        if not math.isfinite(count) or count < 0 or not count.is_integer():
            raise ValueError("Counts must be finite nonnegative whole numbers")
        dated.append((t, int(count)))
    dated.sort()

    expected_gap_seconds = interval_minutes * 60
    for (first, _), (second, _) in zip(dated, dated[1:]):
        gap = (second - first).total_seconds()
        if not math.isclose(gap, expected_gap_seconds, abs_tol=0.01):
            raise ValueError(f"Missing/overlapping intervals between {first.isoformat()} "
                             f"and {second.isoformat()}; select a contiguous window")

    total = sum(count for _, count in dated)
    observed_hours = len(dated) * interval_minutes / 60
    selected = next(iter(streams))
    return {
        "schema": SCHEMA,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": snapshot.get("source", "unspecified count snapshot"),
        "dataset_id": snapshot.get("dataset_id", "unknown"),
        "source_retrieved_at_utc": snapshot.get("retrieved_at_utc"),
        "source_sha256": input_sha256,
        "sensor_id": sensor_id,
        "travelmode": mode,
        "granularity": granularity,
        "direction": selected[0],
        "flowid": selected[1],
        "status": selected[2],
        "interval_minutes_assumed": interval_minutes,
        "first_timestamp_local": dated[0][0].isoformat(),
        "last_timestamp_local": dated[-1][0].isoformat(),
        "observations": len(dated),
        "counted_cyclists": total,
        "observed_hours_assumed": round(observed_hours, 6),
        "arrival_rate_per_hour": round(total / observed_hours, 6),
        "sampling_model": "Poisson arrivals at estimated constant mean; not replayed observations",
        "data_quality_note": ("The status code is not interpreted as valid by this script. "
                              "Verify it against the NYC data dictionary; check that "
                              "interval length and measurement semantics are appropriate."),
    }


def load_calibration(path: Path) -> dict:
    """Check a calibration file before it changes the simulation input."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("Expected a Cyclistics arrival-rate calibration JSON file")
    rate = data.get("arrival_rate_per_hour")
    if isinstance(rate, bool) or not isinstance(rate, (float, int)) or not math.isfinite(rate) or rate < 0:
        raise ValueError("Calibration contains an invalid arrival_rate_per_hour")
    return data


def _save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and calibrate NYC bicycle count measurements")
    sub = parser.add_subparsers(dest="command", required=True)
    sensors = sub.add_parser("sensors", help="list available counter IDs from sensor sample")
    sensors.add_argument("--input", required=True, type=Path)

    fetch = sub.add_parser("fetch", help="download one sensor's counts for a time window")
    fetch.add_argument("--sensor-id", required=True)
    fetch.add_argument("--start", required=True, help="YYYY-MM-DDTHH:MM:SS, NYC local clock")
    fetch.add_argument("--end", required=True, help="exclusive end, NYC local clock")
    fetch.add_argument("--max-records", type=int, default=3000)
    fetch.add_argument("--output", required=True, type=Path)

    inspect = sub.add_parser("inspect", help="show exact modes, granularities and flows")
    inspect.add_argument("--input", required=True, type=Path)

    fit = sub.add_parser("calibrate", help="estimate a mean arrival rate from one stream")
    fit.add_argument("--input", required=True, type=Path)
    fit.add_argument("--sensor-id", required=True)
    fit.add_argument("--mode", required=True, help="exact travelmode from inspect")
    fit.add_argument("--granularity", required=True, help="exact granularity from inspect")
    fit.add_argument("--interval-minutes", required=True, type=float)
    fit.add_argument("--direction")
    fit.add_argument("--flow-id")
    fit.add_argument("--status")
    fit.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "sensors":
        snapshot = json.loads(args.input.read_text(encoding="utf-8"))
        if snapshot.get("dataset") != "sensors" or not isinstance(snapshot.get("records"), list):
            raise ValueError("Pass a saved sensor sample from cyclistics.nyc_open_data")
        for row in snapshot["records"]:
            print(f"{row.get('id', '?'):>12}  {row.get('name', '')}  "
                  f"modes={row.get('travelmodes', '?')}  granularity={row.get('granularity', '?')}")
    elif args.command == "fetch":
        snapshot = fetch_window(args.sensor_id, args.start, args.end, args.max_records)
        _save_json(args.output, snapshot)
        print(f"Saved {snapshot['record_count']} records to {args.output}")
        print("Next: inspect --input <same file> to see stream options.")
    elif args.command == "inspect":
        snapshot = _read_snapshot(args.input)
        print("rows | sensor_id | travelmode | granularity | direction | flowid | status")
        for values, count in inspect_counts(snapshot):
            print(f"{count:4} | " + " | ".join(values))
        print("Copy the exact values from ONE stream for the calibrate command.")
    else:
        snapshot = _read_snapshot(args.input)
        digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
        result = calibrate(snapshot, sensor_id=args.sensor_id, mode=args.mode,
                           granularity=args.granularity, interval_minutes=args.interval_minutes,
                           direction=args.direction, flow_id=args.flow_id, status=args.status,
                           input_sha256=digest)
        _save_json(args.output, result)
        print(f"Estimated rate: {result['arrival_rate_per_hour']:.2f} cyclists/hour "
              f"from {result['observations']} intervals")
        print(f"Saved calibration to {args.output}")
        print("Reminder: the simulator will STILL generate synthetic Poisson arrivals.")


if __name__ == "__main__":
    main()
