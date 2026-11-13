"""Carry a checked NYC count-derived *mean rate* into the independent NetLogo ABM.

The current NetLogo model already supports `csv:from-file` (csv extension).
This bridge writes a single-number CSV for explicit import in its Command Center,
then checks whether its paired A/B export used the selected input value.

This is input calibration, NOT empirical validation of predicted queues/delays.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from .nyc_calibration import load_calibration
from .nyc_open_data import DATASETS

BRIDGE_SCHEMA = "cyclistics.netlogo-rate-bridge.v1"
NETLOGO_SLIDER_MAX = 1800  # matches arrival-rate-per-hour slider in the current .nlogo
RATE_CSV = "netlogo_arrival_rate.csv"
INSTRUCTIONS = "netlogo_calibration_commands.txt"
MANIFEST = "netlogo_rate_provenance.json"
PAIR_REPORT = "netlogo_calibrated_pair_report.json"


def validated_calibration(path: Path, *, allow_synthetic: bool = False) -> dict:
    """Validate provenance fields before preparing an explicit NetLogo input."""
    data = load_calibration(path)
    expected = ("source", "dataset_id", "sensor_id", "travelmode", "granularity",
                "direction", "flowid", "status", "observations", "counted_cyclists",
                "observed_hours_assumed", "interval_minutes_assumed", "arrival_rate_per_hour")
    for key in expected:
        if key not in data or data[key] is None or data[key] == "":
            raise ValueError(f"Calibration is missing required provenance: {key}")
    if data["dataset_id"] != DATASETS["counts"]["id"]:
        raise ValueError("Unsupported NYC counts dataset ID")
    if str(data["travelmode"]).casefold() not in ("bicycle", "bike"):
        raise ValueError("Only bicycle-count calibration can feed the bicycle ABM")
    for key in ("observations", "counted_cyclists", "observed_hours_assumed", "interval_minutes_assumed"):
        val = data[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val):
            raise ValueError(f"Invalid numeric calibration field: {key}")
    if data["observations"] < 2 or int(data["observations"]) != data["observations"]:
        raise ValueError("Calibration needs at least two whole observations")
    if data["counted_cyclists"] < 0 or int(data["counted_cyclists"]) != data["counted_cyclists"]:
        raise ValueError("Cyclist count must be a nonnegative integer")
    if data["observed_hours_assumed"] <= 0 or data["interval_minutes_assumed"] <= 0:
        raise ValueError("Observation period and interval must be positive")
    rate = float(data["arrival_rate_per_hour"])
    if rate > NETLOGO_SLIDER_MAX:
        raise ValueError(f"Calibration rate {rate:g}/hour exceeds NetLogo slider maximum "
                         f"{NETLOGO_SLIDER_MAX}/hour; do not silently clip it")
    # The previously fitted rate is rounded to six decimals, so a small tolerance is appropriate.
    inferred = float(data["counted_cyclists"]) / float(data["observed_hours_assumed"])
    if not math.isclose(rate, inferred, rel_tol=1e-6, abs_tol=1e-5):
        raise ValueError("Rate disagrees with recorded count / observation hours")
    origin = str(data["source"])
    synthetic = "synthetic" in origin.casefold() or "fixture" in origin.casefold()
    if synthetic and not allow_synthetic:
        raise ValueError("Synthetic demonstration calibration detected: use --allow-synthetic "
                         "for a labeled smoke test; do not claim this is NYC-observed data")
    if not synthetic and not data.get("source_sha256"):
        raise ValueError("Real-observation calibration must include snapshot SHA256 provenance")
    if not synthetic and not data.get("source_retrieved_at_utc"):
        raise ValueError("Real-observation calibration must include snapshot retrieval time")
    return data


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8")


def manifest_for(calibration: dict, path: Path) -> dict:
    return {
        "schema": BRIDGE_SCHEMA,
        "calibration_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "data_origin": "synthetic_fixture" if "synthetic" in str(calibration["source"]).lower()
                       or "fixture" in str(calibration["source"]).lower()
                       else "calibration_from_NYC_count_snapshot",
        "source": calibration["source"],
        "dataset_id": calibration["dataset_id"],
        "sensor_id": calibration["sensor_id"],
        "travelmode": calibration["travelmode"],
        "granularity": calibration["granularity"],
        "direction": calibration["direction"],
        "flowid": calibration["flowid"],
        "status": calibration["status"],
        "source_sha256": calibration.get("source_sha256"),
        "source_retrieved_at_utc": calibration.get("source_retrieved_at_utc"),
        "first_timestamp_local": calibration.get("first_timestamp_local"),
        "last_timestamp_local": calibration.get("last_timestamp_local"),
        "observations": calibration["observations"],
        "interval_minutes_assumed": calibration["interval_minutes_assumed"],
        "observed_hours_assumed": calibration["observed_hours_assumed"],
        "arrival_rate_per_hour": calibration["arrival_rate_per_hour"],
        "netlogo_model": "netlogo/Cyclistics_Bike_Lane_ABM.nlogo",
        "netlogo_input": f"outputs/{RATE_CSV}",
        "netlogo_arrival_assumption": "Bernoulli, one simulated second per tick, "
                                      "probability = observed_mean_per_hour / 3600",
        "limitation": "NYC counts inform only demand rate. Agent trajectories, queues, speeds "
                      "and obstruction outcomes remain synthetic and unvalidated.",
    }


def prepare(calibration_path: Path, output_dir: Path, *, allow_synthetic: bool = False) -> dict:
    data = validated_calibration(calibration_path, allow_synthetic=allow_synthetic)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / RATE_CSV).open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerow([format(data["arrival_rate_per_hour"], ".6f")])
    manifest = manifest_for(data, calibration_path)
    _write_json(output_dir / MANIFEST, manifest)
    commands = (
        "; Cyclistics / NetLogo Command Center. Open the model from the netlogo/ folder.\n"
        "; Run one command per line, with Go stopped. This loads the single numeric CSV cell.\n"
        'set arrival-rate-per-hour (first (first (csv:from-file "../outputs/netlogo_arrival_rate.csv")))\n'
        'show (word "Loaded calibrated cyclists/hour: " arrival-rate-per-hour)\n'
        "; Then compare equal-demand simulated scenarios (still NOT empirical validation).\n"
        "run-paired-experiment\n"
    )
    (output_dir / INSTRUCTIONS).write_text(commands, encoding="utf-8")
    return manifest


def _number(row: dict[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Missing or invalid paired experiment {key}") from exc
    if not math.isfinite(value):
        raise ValueError(f"Non-finite paired experiment {key}")
    return value


def _whole(row: dict[str, str], key: str) -> int:
    value = _number(row, key)
    if int(value) != value or value < 0:
        raise ValueError(f"Expected nonnegative whole number: {key}")
    return int(value)


def verify_pair(calibration_path: Path, paired_path: Path, output_dir: Path,
                *, allow_synthetic: bool = False) -> dict:
    data = validated_calibration(calibration_path, allow_synthetic=allow_synthetic)
    if not paired_path.is_file():
        raise ValueError("NetLogo paired-results CSV not found; run run-paired-experiment first")
    with paired_path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 2 or {r.get("scenario") for r in rows} != {"clear", "blocked"}:
        raise ValueError("Expected exactly one clear and one blocked scenario")
    by_name = {r["scenario"]: r for r in rows}
    clear, blocked = by_name["clear"], by_name["blocked"]
    for name, r in by_name.items():
        if _whole(r, "blockage_enabled") != int(name == "blocked"):
            raise ValueError("Incorrect blockage flag")
        if r.get("conservation_ok", "").casefold() != "true":
            raise ValueError("NetLogo conservation check was not true")
        n = _whole(r, "requested")
        if n != sum(_whole(r, col) for col in ("departed", "on_lane", "pending")):
            raise ValueError("NetLogo cyclist conservation is invalid")
        if not math.isclose(_number(r, "arrival_rate_per_hour"),
                            float(data["arrival_rate_per_hour"]), rel_tol=0, abs_tol=1e-6):
            raise ValueError("Run did not use selected calibration rate; load the rate in NetLogo")
        if _number(r, "mean_queue") < 0 or _number(r, "mean_stop_completed_s") < 0:
            raise ValueError("Negative queue / stop measure")
        _whole(r, "peak_queue")
        if _whole(r, "run_length_s") == 0:
            raise ValueError("Run horizon must be positive")
    matched = ("seed", "blockage_start_s", "blockage_duration_s", "run_length_s",
               "requested")
    for field in matched:
        if not math.isclose(_number(clear, field), _number(blocked, field),
                            rel_tol=0, abs_tol=1e-8):
            raise ValueError(f"Paired scenarios differ on {field}")
    report = {
        "schema": BRIDGE_SCHEMA,
        "status": "verified_calibrated_input_not_real_world_outcomes",
        "provenance": manifest_for(data, calibration_path),
        "paired_results_file_sha256": hashlib.sha256(paired_path.read_bytes()).hexdigest(),
        "scenario_seed": _whole(clear, "seed"),
        "horizon_seconds": _whole(clear, "run_length_s"),
        "requested_cyclists_each": _whole(clear, "requested"),
        "clear": {"departed": _whole(clear, "departed"),
                  "peak_queue": _whole(clear, "peak_queue"),
                  "mean_queue": _number(clear, "mean_queue"),
                  "mean_stopped_seconds_among_departed": _number(clear, "mean_stop_completed_s")},
        "blocked": {"departed": _whole(blocked, "departed"),
                    "peak_queue": _whole(blocked, "peak_queue"),
                    "mean_queue": _number(blocked, "mean_queue"),
                    "mean_stopped_seconds_among_departed": _number(blocked, "mean_stop_completed_s")},
        "blocked_minus_clear": {
            "departed": _whole(blocked, "departed") - _whole(clear, "departed"),
            "peak_queue": _whole(blocked, "peak_queue") - _whole(clear, "peak_queue"),
            "mean_queue": round(_number(blocked, "mean_queue") - _number(clear, "mean_queue"), 6),
            "mean_stopped_seconds_among_departed": round(
                _number(blocked, "mean_stop_completed_s") -
                _number(clear, "mean_stop_completed_s"), 6),
        },
        "limitation": "These are synthetic obstruction scenarios calibrated only for demand, "
                      "not real NYC queue/delay predictions or field validation.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / PAIR_REPORT, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare", help="Convert an existing validated rate JSON for NetLogo")
    check = sub.add_parser("verify", help="Check that NetLogo's paired results used the rate")
    for cmd in (prep, check):
        cmd.add_argument("--calibration", required=True, type=Path)
        cmd.add_argument("--output-dir", required=True, type=Path)
        cmd.add_argument("--allow-synthetic", action="store_true",
                         help="ONLY for labeled development smoke tests, not NYC results")
    check.add_argument("--paired-results", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        manifest = prepare(args.calibration, args.output_dir, allow_synthetic=args.allow_synthetic)
        print(f"PASS: NetLogo demand input prepared: {manifest['arrival_rate_per_hour']:g} cyclists/hour")
        print(f"Source: {manifest['source']}; sensor={manifest['sensor_id']}")
        print(f"View NetLogo commands: {args.output_dir / INSTRUCTIONS}")
        print(f"Rate file: {args.output_dir / RATE_CSV}; provenance: {args.output_dir / MANIFEST}")
        print("NOTE: calibrated arrivals are synthetic. Do not claim field validation.")
    else:
        result = verify_pair(args.calibration, args.paired_results, args.output_dir,
                             allow_synthetic=args.allow_synthetic)
        print("PASS: NetLogo paired scenario used the supplied calibration rate and conserved cyclists")
        print(f"Mean queue increase: {result['blocked_minus_clear']['mean_queue']:.3f} riders")
        print(f"Report: {args.output_dir / PAIR_REPORT}")
        print("NOTE: the result is data-informed simulation, NOT observed NYC congestion.")


if __name__ == "__main__":
    main()
