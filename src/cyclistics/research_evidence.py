"""Package *verified NetLogo exports* as paper-ready evidence.

This tool never simulates cyclists and never substitutes test fixtures for a
missing NetLogo CSV. Reuse the established 160-row validator and paired
statistics so the paper table and figures cannot silently drift apart.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from .netlogo_sensitivity import (
    DURATIONS,
    RATES,
    SEEDS,
    read_and_validate,
    render_svg,
    summarize,
)

SCHEMA = "cyclistics.research-evidence.v1"
OUTPUT_COLUMNS = (
    "arrival_rate_per_hour",
    "blockage_duration_s",
    "replications",
    "avg_clear_mean_queue",
    "avg_blocked_mean_queue",
    "avg_delta_mean_queue",
    "ci95_low_delta_mean_queue",
    "ci95_high_delta_mean_queue",
    "avg_delta_peak_queue",
    "ci95_low_delta_peak_queue",
    "ci95_high_delta_peak_queue",
    "avg_delta_departed",
    "avg_delta_mean_stop_completed_s",
)

CHARTS = (
    ("delta_mean_queue", "Queueing response to lane obstruction",
     "Change in mean queue (cyclists)", "netlogo_delta_mean_queue.svg"),
    ("delta_peak_queue", "Peak queue response to lane obstruction",
     "Change in peak queue (cyclists)", "netlogo_delta_peak_queue.svg"),
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _formatted(value: object) -> str:
    # Consistent six decimals makes the table deterministic across runs.
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _paper_rows(summary: list[dict[str, float]]) -> list[dict[str, object]]:
    return [{name: row[name] for name in OUTPUT_COLUMNS} for row in summary]


def _csv_table(rows: list[dict[str, object]], output: Path) -> None:
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({k: _formatted(v) for k, v in row.items()} for row in rows)


def _markdown_table(rows: list[dict[str, object]], output: Path) -> None:
    lines = [
        "# NetLogo sensitivity study — simulated cyclist queue response",
        "",
        "Synthetic one-lane NetLogo ABM experiment; not measured NYC traffic.",
        "Four demand levels, four blockage durations, 10 matched random seeds per setting.",
        "Each row reports blocked minus clear. Intervals are approximate paired-difference",
        "95% Student t intervals (9 degrees of freedom), conditional on model assumptions.",
        "",
        "| Demand (cyclists/hour) | Block (s) | Mean queue change (95% CI) | Peak queue change (95% CI) | Departures change |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        mean = row["avg_delta_mean_queue"]
        mean_low = row["ci95_low_delta_mean_queue"]
        mean_high = row["ci95_high_delta_mean_queue"]
        peak = row["avg_delta_peak_queue"]
        peak_low = row["ci95_low_delta_peak_queue"]
        peak_high = row["ci95_high_delta_peak_queue"]
        departed = row["avg_delta_departed"]
        lines.append(
            f"| {row['arrival_rate_per_hour']} | {row['blockage_duration_s']} | "
            f"{mean:.3f} [{mean_low:.3f}, {mean_high:.3f}] | "
            f"{peak:.3f} [{peak_low:.3f}, {peak_high:.3f}] | "
            f"{departed:+.3f} |"
        )
    lines.extend([
        "",
        "**Interpretation:** Mean queue is the average end-of-tick waiting count,",
        "not end-to-end travel time. Departures count cyclists completing within",
        "the fixed 600-second simulated horizon, not long-term throughput.",
        "The CSV also contains a completed-rider stop-time difference, a",
        "selection-sensitive endpoint statistic that must not be called",
        "population mean travel delay. Neither the figures nor intervals",
        "establish real-world model validity or collision/safety risk.",
        "",
        "Source hashes, model-code hashes, and figure hashes are in evidence_manifest.json.",
        "",
    ])
    output.write_text("\n".join(lines), encoding="utf-8")


def build_evidence(raw_csv: Path, model_file: Path, output_dir: Path) -> dict:
    """Validate first; don't leave plausible-looking results for bad inputs."""
    raw_csv = Path(raw_csv)
    model_file = Path(model_file)
    output_dir = Path(output_dir)

    # Validate before creating output files. All 160 rows must be genuine
    # data supplied by the caller; there is no bundled default dataset.
    if not model_file.is_file():
        raise FileNotFoundError(f"NetLogo model file not found: {model_file}")
    records = read_and_validate(raw_csv)
    summary = summarize(records)
    if len(records) != 160 or len(summary) != 16:
        raise ValueError("Unexpected sensitivity study size")

    output_dir.mkdir(parents=True, exist_ok=True)
    table = _paper_rows(summary)
    _csv_table(table, output_dir / "paper_sensitivity_table.csv")
    _markdown_table(table, output_dir / "paper_sensitivity_table.md")
    for metric, title, unit, filename in CHARTS:
        render_svg(summary, metric, title, unit, output_dir / filename)

    names = ("paper_sensitivity_table.csv", "paper_sensitivity_table.md",
             *(item[3] for item in CHARTS))
    manifest = {
        "schema": SCHEMA,
        "field_validated": False,
        "same_scenario_as_devsjava": False,
        "source": {
            "raw_csv": raw_csv.name,
            "raw_sha256": _sha256(raw_csv),
            "model_file": model_file.name,
            "model_sha256": _sha256(model_file),
            "sensitivity_analyzer_sha256": _sha256(
                Path(__file__).with_name("netlogo_sensitivity.py")
            ),
            "evidence_builder_sha256": _sha256(Path(__file__)),
        },
        "observations": {
            "paired_rows": len(records),
            "summary_rows": len(summary),
            "rates_per_hour": list(RATES),
            "blockage_durations_s": list(DURATIONS),
            "seeds": list(SEEDS),
            "blockage_start_s": 45,
            "horizon_ticks": 600,
            "seed_count_per_configuration": len(SEEDS),
        },
        "uncertainty": {
            "method": "paired differences; approximate two-sided Student t 95% interval",
            "degrees_of_freedom": 9,
            "scope": "simulation replicate variability under assumed model, not field uncertainty",
        },
        "scope": (
            "Synthetic one-lane NetLogo ABM sensitivity only. "
            "No observed NYC queueing outcomes, real-world validation, "
            "or cross-engine numerical parity."
        ),
        "outputs_sha256": {name: _sha256(output_dir / name) for name in names},
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path,
                        help="Raw 160-row CSV exported by NetLogo Run sensitivity study")
    parser.add_argument("--model", required=True, type=Path,
                        help="The .nlogo source that generated the raw export")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/research_evidence"))
    args = parser.parse_args()
    result = build_evidence(args.input, args.model, args.output_dir)
    print(f"PASS: validated {result['observations']['paired_rows']} paired NetLogo rows")
    print(f"PASS: generated {result['observations']['summary_rows']} research table rows")
    print(f"Research evidence: {args.output_dir}")
    print("NOTE: synthetic simulation, not measured NYC performance or field validation.")


if __name__ == "__main__":
    main()
