"""Make a provenance-stamped performance report from actual NetLogo exports.

This command does not run NetLogo or synthesize measurements. The underlying
validator requires the complete 5-case verification and 36-run benchmark grids.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from .netlogo_benchmarks import (
    HORIZONS,
    RATES,
    SEEDS,
    summarize_benchmarks,
    validate_benchmarks,
    validate_verification,
    write_runtime_svg,
)

SCHEMA = "cyclistics.performance-evidence.v1"
TABLE_FIELDS = (
    "arrival_rate_per_hour",
    "blockage_enabled",
    "run_length_s",
    "replications",
    "mean_requested",
    "mean_peak_queue",
    "mean_elapsed_real_s",
    "sd_elapsed_real_s",
    "mean_ms_per_sim_tick",
    "min_ms_per_sim_tick",
    "max_ms_per_sim_tick",
    "simulated_seconds_per_real_second",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _value(value: float | int) -> str:
    return f"{value:.6f}" if isinstance(value, float) else str(value)


def _write_table_csv(rows: list[dict[str, float | int]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: _value(row[name]) for name in TABLE_FIELDS})


def _write_table_md(rows: list[dict[str, float | int]], path: Path) -> None:
    lines = [
        "# NetLogo computational performance — measured desktop runs",
        "",
        "These are locally measured wall-clock runtimes for a simulated",
        "one-lane cyclist model, not NYC field observations or physical travel time.",
        "Each setting has three replicate seeds; this is a descriptive",
        "benchmark rather than evidence of general computational scaling.",
        "",
        "| Attempted cyclists/hour | Obstruction | Horizon (simulated s) | Mean elapsed (wall-clock s) | SD (wall-clock s) | Mean ms/tick | Simulated s per real s |",
        "| ---: | :---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['arrival_rate_per_hour']} | "
            f"{'Yes' if row['blockage_enabled'] else 'No'} | "
            f"{row['run_length_s']} | {row['mean_elapsed_real_s']:.4f} | "
            f"{row['sd_elapsed_real_s']:.4f} | "
            f"{row['mean_ms_per_sim_tick']:.4f} | "
            f"{row['simulated_seconds_per_real_second']:.2f} |"
        )
    lines.extend([
        "",
        "Measurement method: NetLogo timer measures the run after setup;",
        "view updates are suppressed, and a separate unmeasured 100-tick warmup",
        "precedes the benchmark grid. These timings depend on local hardware,",
        "NetLogo/Java versions, and other computer activity.",
        "",
        "Scope: Verification checks include cyclist accounting, replay and",
        "obstruction timing. Runtime results say nothing about agreement with",
        "DEVS-Suite timings, observed NYC queues, or real-world model validity.",
        "No formal inference about performance differences is made from only",
        "three measurements per configuration. This is not NYC field validation.",
        "",
        "See performance_manifest.json for SHA-256 source and output hashes.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def build_performance_evidence(
    verification_csv: Path,
    benchmark_csv: Path,
    model_file: Path,
    output_dir: Path,
) -> dict:
    """Validate every source before creating output files."""
    verification_csv = Path(verification_csv)
    benchmark_csv = Path(benchmark_csv)
    model_file = Path(model_file)
    output_dir = Path(output_dir)
    if not model_file.is_file():
        raise FileNotFoundError(f"NetLogo model not found: {model_file}")

    cases = validate_verification(verification_csv)
    records = validate_benchmarks(benchmark_csv)
    summary = summarize_benchmarks(records)
    if len(cases) != 5 or len(records) != 36 or len(summary) != 12:
        raise ValueError("Unexpected verification or runtime benchmark grid")

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_table_csv(summary, output_dir / "performance_table.csv")
    _write_table_md(summary, output_dir / "performance_table.md")
    for horizon in HORIZONS:
        write_runtime_svg(
            summary, horizon, output_dir / f"netlogo_runtime_{horizon}s.svg"
        )

    names = (
        "performance_table.csv", "performance_table.md",
        *(f"netlogo_runtime_{horizon}s.svg" for horizon in HORIZONS),
    )
    manifest = {
        "schema": SCHEMA,
        "field_validated": False,
        "cross_model_runtime_comparable": False,
        "observations": {
            "verification_cases": len(cases),
            "benchmark_runs": len(records),
            "summary_groups": len(summary),
            "rates_per_hour": list(RATES),
            "seeds": list(SEEDS),
            "horizons_simulated_seconds": list(HORIZONS),
            "obstruction_enabled": [False, True],
            "replications_per_group": len(SEEDS),
        },
        "measurement": {
            "clock": "NetLogo timer (wall-clock real seconds)",
            "setup_included": False,
            "warmup": "100 unmeasured simulation ticks before the measured grid",
            "interpretation": "host-dependent descriptive computation time, not NYC validation",
        },
        "source_sha256": {
            "verification_csv": _sha256(verification_csv),
            "benchmark_csv": _sha256(benchmark_csv),
            "model": _sha256(model_file),
            "benchmark_analyzer": _sha256(
                Path(__file__).with_name("netlogo_benchmarks.py")
            ),
            "evidence_builder": _sha256(Path(__file__)),
        },
        "outputs_sha256": {
            name: _sha256(output_dir / name) for name in names
        },
    }
    (output_dir / "performance_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification", required=True, type=Path)
    parser.add_argument("--benchmarks", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/performance_evidence"))
    args = parser.parse_args()
    report = build_performance_evidence(
        args.verification, args.benchmarks, args.model, args.output_dir
    )
    print(f"PASS: validated {report['observations']['verification_cases']} verification cases")
    print(f"PASS: validated {report['observations']['benchmark_runs']} measured runtime rows")
    print(f"PASS: wrote {report['observations']['summary_groups']} benchmark groups")
    print(f"Research evidence: {args.output_dir}")
    print("NOTE: wall-clock benchmarks are machine-specific, not NYC field validation.")


if __name__ == "__main__":
    main()
