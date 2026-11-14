"""Read-only diagnostics for ambiguous NYC bicycle counter observations.

The report surfaces anomalies and preserves separate flows; it never changes
raw data or authorizes a stream for use as validated field evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .nyc_open_data import DATASETS

REPORT_SCHEMA = "cyclistics.nyc-counter-quality.v1"
KEY_FIELDS = ("sensor_id", "travelmode", "granularity", "direction", "flowid", "status")
REQUIRED_FIELDS = (*KEY_FIELDS, "timestamp", "counts")


def interval_minutes(value: str) -> int | None:
    """Interpret only documented-duration labels; never guess unfamiliar units."""
    alias = {"Hour": 60, "15min": 15, "30min": 30}
    if value in alias:
        return alias[value]
    match = re.fullmatch(r"PT([1-9][0-9]*)([MH])", value)
    if not match:
        return None
    number, unit = int(match[1]), match[2]
    minutes = number if unit == "M" else number * 60
    return minutes if 0 < minutes <= 1440 else None


def _timestamp(text: str) -> datetime:
    try:
        value = datetime.fromisoformat(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid timestamp: {text!r}") from exc
    if value.tzinfo is not None:
        raise ValueError("timestamp must be timezone-free NYC dataset local time")
    return value


def _count(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("counts must be a nonnegative whole number")
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("counts must be a nonnegative whole number") from exc
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError("counts must be a nonnegative whole number")
    return int(number)


def _metadata_devices(metadata: dict | None, used_sensors: set[str]) -> dict[str, list[str]]:
    if metadata is None:
        return {}
    if not isinstance(metadata, dict) or metadata.get("dataset") != "sensors" or not isinstance(metadata.get("records"), list):
        raise ValueError("Expected NYC sensors snapshot with records list")
    found: dict[str, set[str]] = defaultdict(set)
    for row in metadata["records"]:
        if not isinstance(row, dict):
            raise ValueError("Invalid sensors metadata record")
        identifier = str(row.get("id", ""))
        if identifier in used_sensors and row.get("counters_id") not in (None, ""):
            found[identifier].add(str(row["counters_id"]))
    return {key: sorted(found[key]) for key in sorted(found)}


def analyze_snapshot(snapshot: dict, sensors_metadata: dict | None = None) -> dict:
    """Describe each measured stream without choosing, combining or repairing it."""
    if (not isinstance(snapshot, dict) or snapshot.get("dataset") != "counts"
            or snapshot.get("dataset_id") != DATASETS["counts"]["id"]
            or not isinstance(snapshot.get("records"), list)):
        raise ValueError("Expected NYC counts snapshot with records and counts dataset ID")

    grouped: dict[tuple[str, ...], list[tuple[datetime, int]]] = defaultdict(list)
    for index, record in enumerate(snapshot["records"]):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index}: expected an object")
        for field in REQUIRED_FIELDS:
            if field not in record or record[field] is None or str(record[field]).strip() == "":
                raise ValueError(f"Record {index}: missing/empty {field}")
        key = tuple(str(record[field]) for field in KEY_FIELDS)
        try:
            parsed_time = _timestamp(str(record["timestamp"]))
            count = _count(record["counts"])
        except ValueError as exc:
            raise ValueError(f"Record {index}: {exc}") from exc
        grouped[key].append((parsed_time, count))

    streams: list[dict] = []
    ambiguous_candidates: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for key in sorted(grouped):
        row = dict(zip(KEY_FIELDS, key))
        entries = sorted(grouped[key])
        observed = len(entries)
        step = interval_minutes(row["granularity"])
        warnings = ["status_requires_source_review"]  # e.g. 'raw' is not a QA certificate
        if row["travelmode"].casefold() not in ("bicycle", "bike"):
            warnings.append("non_bicycle_mode")
        if step is None:
            warnings.append("unknown_interval")
        if observed < 2:
            warnings.append("insufficient_observations")
        distinct_times = {time for time, _ in entries}
        if len(distinct_times) != observed:
            warnings.append("duplicate_timestamps")
        if step is not None:
            for (time1, _), (time2, _) in zip(entries, entries[1:]):
                delta_seconds = (time2 - time1).total_seconds()
                if delta_seconds > step * 60 + 0.01:
                    if "missing_intervals" not in warnings:
                        warnings.append("missing_intervals")
                elif 0 < delta_seconds < step * 60 - 0.01:
                    if "irregular_interval" not in warnings:
                        warnings.append("irregular_interval")

        # A rate only makes sense for a complete, nonduplicated time series.
        disqualifying = {"unknown_interval", "insufficient_observations", "non_bicycle_mode",
                         "duplicate_timestamps", "missing_intervals", "irregular_interval"}
        candidate = None
        if step is not None and not disqualifying.intersection(warnings):
            candidate = round(sum(c for _, c in entries) / (observed * step / 60), 6)
        row.update({
            "observations": observed,
            "first_timestamp_local": entries[0][0].isoformat(),
            "last_timestamp_local": entries[-1][0].isoformat(),
            "counted_cyclists": sum(c for _, c in entries),
            "interval_minutes": step,
            "candidate_hourly_rate": candidate,
            "warnings": sorted(warnings),
            "field_validated": False,
        })
        streams.append(row)
        # Status is not in this grouping: similarly named flows may coexist
        # with different processing states and must not be summed.
        comparison_key = (row["sensor_id"], row["travelmode"], row["granularity"], row["direction"])
        ambiguous_candidates[comparison_key].append(row)

    ambiguous = []
    for key, members in sorted(ambiguous_candidates.items()):
        ids = sorted({member["flowid"] for member in members})
        if len(ids) <= 1:
            continue
        ambiguous.append({
            "sensor_id": key[0], "travelmode": key[1],
            "granularity": key[2], "direction": key[3],
            "flow_ids": ids,
            "reason": "Multiple distinct flows share the same sensor/mode/direction; do not sum automatically",
        })
        for member in members:
            member["warnings"] = sorted(set(member["warnings"] + ["ambiguous_direction_flows"]))

    devices = _metadata_devices(sensors_metadata, {r["sensor_id"] for r in streams})
    return {
        "schema": REPORT_SCHEMA,
        "source": snapshot.get("source"),
        "dataset_id": snapshot["dataset_id"],
        "record_count": len(snapshot["records"]),
        "stream_count": len(streams),
        "streams": streams,
        "ambiguous_direction_groups": ambiguous,
        "hardware_by_sensor": devices,
        "recommended_rate_selection": "manual_review_required",
        "field_validated": False,
        "interpretation": "Read-only diagnostic; candidate rates are not QA approval or empirical model validation",
    }


def write_report(counts_path: Path, output_path: Path,
                 sensors_path: Path | None = None) -> dict:
    """Validate completely before writing; never leave a partial report."""
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    metadata = json.loads(sensors_path.read_text(encoding="utf-8")) if sensors_path else None
    report = analyze_snapshot(counts, metadata)
    report["source_sha256"] = hashlib.sha256(counts_path.read_bytes()).hexdigest()
    if sensors_path:
        report["sensors_metadata_sha256"] = hashlib.sha256(sensors_path.read_bytes()).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", required=True, type=Path, help="Saved NYC counts snapshot")
    parser.add_argument("--sensors", type=Path, help="Optional saved NYC sensor metadata")
    parser.add_argument("--output", required=True, type=Path, help="Diagnostic JSON output")
    args = parser.parse_args()
    report = write_report(args.counts, args.output, args.sensors)
    print(f"PASS: analyzed {report['record_count']} rows / {report['stream_count']} streams")
    print(f"Ambiguous direction groups: {len(report['ambiguous_direction_groups'])}")
    for stream in report["streams"]:
        rate = stream["candidate_hourly_rate"]
        print(f"  {stream['direction']:>5} flow={stream['flowid']:<12} "
              f"count={stream['counted_cyclists']:<5} "
              f"candidate={str(rate) if rate is not None else 'unavailable'} cyclists/hr "
              f"warnings={','.join(stream['warnings'])}")
    print(f"Report: {args.output}")
    print("NOTE: do not combine ambiguous streams; these data are NOT field-validated.")


if __name__ == "__main__":
    main()
