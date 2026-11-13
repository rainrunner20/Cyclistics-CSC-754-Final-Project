"""Compare *limited* evidence from independent Cyclistics simulation engines.

Python and Java share a small deterministic fixture; NetLogo contributes only
its own paired-scenario consistency. This is not a live co-simulation or
field-validation tool.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from .simulation import Scenario, simulate

SCHEMA = "cyclistics.cross-model-comparison.v1"
ARRIVALS = [10.0, 15.0]
BLOCKAGE = (12.0, 20.0)
HEADWAY = 4.0
HORIZON = 30.0
JAVA_DEP = re.compile(r"^DEPARTURE,([0-9]+(?:\.[0-9]+)?),(cyclist-[0-9]+)$")
JAVA_COUNTS = {
    "generated": 2,
    "obstruction events": 2,
    "departed": 2,
    "max waiting": 1,
    "remaining": 0,
}
NETLOGO_FIELDS = (
    "scenario", "blockage_enabled", "seed", "arrival_rate_per_hour",
    "blockage_start_s", "blockage_duration_s", "run_length_s",
    "requested", "departed", "on_lane", "pending", "peak_queue",
    "mean_queue", "mean_stop_completed_s", "conservation_ok",
)


def _safe_number(raw: str, *, nonnegative: bool = True) -> float:
    try:
        value = float(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Expected numeric value, got {raw!r}") from exc
    if not math.isfinite(value) or (nonnegative and value < 0):
        raise ValueError(f"Invalid non-finite/negative value: {raw!r}")
    return value


def _whole(raw: str) -> int:
    value = _safe_number(raw)
    if not value.is_integer():
        raise ValueError(f"Expected whole-number count, got {raw!r}")
    return int(value)


def _python_fixture() -> dict:
    case = Scenario(
        "shared_java_deterministic_fixture",
        blockage_intervals=(BLOCKAGE,), horizon_s=HORIZON,
        service_headway_s=HEADWAY, freeflow_travel_s=0.0,
    )
    summary, trace, _ = simulate(case, ARRIVALS)
    departures = [row["time_s"] for row in trace if row["event"] == "service_complete"]
    # The Python fixture is independently executed, never filled in from a
    # saved Java log or an assumed 'PASS' line.
    if (departures != [14.0, 24.0] or summary["completed_all"] != 2
            or summary["max_waiting_queue"] != 1
            or summary["mean_wait_s"] != 2.5):
        raise AssertionError("Python reference changed: recheck the shared fixture")
    return {
        "status": "reference_executed",
        "arrival_seconds": ARRIVALS,
        "blockage_interval_seconds": list(BLOCKAGE),
        "passage_seconds": HEADWAY,
        "horizon_seconds": HORIZON,
        "ordered_departure_seconds": departures,
        "peak_waiting_queue": summary["max_waiting_queue"],
        "mean_wait_seconds": summary["mean_wait_s"],
        "event_order": [{"time_seconds": row["time_s"], "event": row["event"]}
                        for row in trace],
    }


def parse_java_log(text: str, expected_departures: list[float],
                   *, expected_queue: int) -> dict:
    """Read actual runner output; textual shape cannot *attest* JAR provenance."""
    departures: list[tuple[str, float]] = []
    counts: dict[str, int] = {}
    for original in text.splitlines():
        line = original.strip()
        if line.startswith("DEPARTURE,"):
            match = JAVA_DEP.fullmatch(line)
            if match is None:
                raise ValueError(f"Malformed Java DEPARTURE row: {line!r}")
            timestamp = _safe_number(match.group(1))
            departures.append((match.group(2), timestamp))
        for key in JAVA_COUNTS:
            found = re.fullmatch(rf"{re.escape(key)}\s*=\s*(\d+)", line)
            if found:
                if key in counts:
                    raise ValueError(f"Duplicate Java summary field {key}")
                counts[key] = int(found.group(1))

    expected = [(f"cyclist-{n}", stamp)
                for n, stamp in enumerate(expected_departures, start=1)]
    if len(departures) != len(expected):
        raise ValueError("Java departure record count differs from Python reference")
    for actual, required in zip(departures, expected):
        if actual[0] != required[0] or abs(actual[1] - required[1]) > 1e-6:
            raise ValueError(f"Java departure {actual} differs from expected {required}")
    expected_counts = JAVA_COUNTS | {"max waiting": expected_queue}
    if counts != expected_counts:
        raise ValueError(f"Java summary counters disagree: {counts!r}")
    if "PASS: real coordinator departure timestamps match 14s and 24s." not in text:
        raise ValueError("Java runner success marker missing")
    return {
        "status": "matches_python_deterministic_fixture",
        "departure_seconds": [time for _, time in departures],
        "departure_ids": [ident for ident, _ in departures],
        "summary": counts,
        "note": "Parsed runner text; this alone does not authenticate the external DEVS-Suite JAR.",
    }


def parse_netlogo_pair(rows: list[dict[str, str]]) -> dict:
    """Within-model comparison only; never compare these numbers to Java."""
    if len(rows) != 2 or {r.get("scenario") for r in rows} != {"clear", "blocked"}:
        raise ValueError("Expected exactly one 'clear' and one 'blocked' NetLogo row")
    if any(any(k not in row or row[k] in (None, "") for k in NETLOGO_FIELDS)
           for row in rows):
        raise ValueError("Incomplete NetLogo CSV columns")
    by_name = {r["scenario"]: r for r in rows}
    a, b = by_name["clear"], by_name["blocked"]
    for key in ("seed", "arrival_rate_per_hour", "blockage_start_s",
                "blockage_duration_s", "run_length_s", "requested"):
        if _safe_number(a[key]) != _safe_number(b[key]):
            raise ValueError(f"Paired NetLogo inputs differ: {key}")
    if _whole(a["blockage_enabled"]) != 0 or _whole(b["blockage_enabled"]) != 1:
        raise ValueError("Expected clear=0 and blocked=1")
    if _safe_number(a["run_length_s"]) <= 0 or _safe_number(a["arrival_rate_per_hour"]) > 1800:
        raise ValueError("Invalid NetLogo run length or arrival rate")
    for row in (a, b):
        if row["conservation_ok"].strip().lower() != "true":
            raise ValueError("NetLogo row did not pass conservation")
        requested = _whole(row["requested"])
        if requested != sum(_whole(row[col]) for col in ("departed", "on_lane", "pending")):
            raise ValueError("NetLogo cyclist accounting does not balance")
        for field in ("mean_queue", "mean_stop_completed_s"):
            _safe_number(row[field])
        _whole(row["peak_queue"])
    return {
        "status": "within_netlogo_consistent_only",
        "seed": _whole(a["seed"]),
        "arrival_rate_per_hour": _safe_number(a["arrival_rate_per_hour"]),
        "horizon_seconds": _safe_number(a["run_length_s"]),
        "requested_cyclists_each": _whole(a["requested"]),
        "blocked_minus_clear": {
            "departed": _whole(b["departed"]) - _whole(a["departed"]),
            "peak_queue": _whole(b["peak_queue"]) - _whole(a["peak_queue"]),
            "mean_queue": round(_safe_number(b["mean_queue"]) - _safe_number(a["mean_queue"]), 6),
            "mean_stop_completed_s": round(
                _safe_number(b["mean_stop_completed_s"]) -
                _safe_number(a["mean_stop_completed_s"]), 6),
        },
        "note": "NetLogo is not using the deterministic Java/Python event schedule.",
    }


def compare_models(java_log_text: str | None = None,
                   netlogo_csv_text: str | None = None) -> dict:
    reference = _python_fixture()
    java = ({"status": "pending_real_coordinator_log"} if java_log_text is None else
            parse_java_log(java_log_text, reference["ordered_departure_seconds"],
                           expected_queue=reference["peak_waiting_queue"]))
    if netlogo_csv_text is None:
        netlogo = {"status": "not_supplied"}
    else:
        netlogo = parse_netlogo_pair(list(csv.DictReader(netlogo_csv_text.splitlines())))
    return {
        "schema": SCHEMA,
        "python_reference": reference,
        "java_comparison": java,
        "netlogo_comparison": netlogo,
        "same_three_model_scenario": False,
        "field_validated": False,
        "scope": ("Exact single-fixture Python-Java comparison when real Java output "
                  "is supplied; separate within-NetLogo paired-scenario check. "
                  "No live model coupling or NYC outcome validation."),
    }


def write_report(output: Path, *, java_log: Path | None = None,
                 netlogo_paired: Path | None = None) -> dict:
    """Parse every optional input before creating or overwriting a report."""
    java_text = java_log.read_text(encoding="utf-8-sig") if java_log else None
    netlogo_text = netlogo_paired.read_text(encoding="utf-8-sig") if netlogo_paired else None
    result = compare_models(java_text, netlogo_text)
    hashes = {}
    if java_log is not None:
        hashes["java_log"] = hashlib.sha256(java_log.read_bytes()).hexdigest()
    if netlogo_paired is not None:
        hashes["netlogo_paired"] = hashlib.sha256(netlogo_paired.read_bytes()).hexdigest()
    result["inputs_sha256"] = hashes
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java-log", type=Path,
                        help="Saved stdout of real DEVS-Suite coordinator runner")
    parser.add_argument("--netlogo-paired", type=Path,
                        help="NetLogo export from run-paired-experiment")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = write_report(args.output, java_log=args.java_log,
                          netlogo_paired=args.netlogo_paired)
    print(f"Python: {report['python_reference']['status']}")
    print(f"Java: {report['java_comparison']['status']}")
    print(f"NetLogo: {report['netlogo_comparison']['status']}")
    print(f"Wrote comparison: {args.output}")
    print("NOTE: the three models do NOT execute the same stochastic scenario.")


if __name__ == "__main__":
    main()
