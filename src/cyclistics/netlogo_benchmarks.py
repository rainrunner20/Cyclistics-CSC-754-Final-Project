"""Validate NetLogo verification/benchmark CSVs and summarize measured runtimes.

No runtime is fabricated here. The two inputs must be exported by the actual
NetLogo desktop model. Timings are environment-dependent, not field validation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from html import escape
from pathlib import Path

VERIFY_FIELDS = [
    "case", "seed", "arrival_rate_per_hour", "blockage_enabled",
    "blockage_duration_s", "run_length_s", "requested", "admitted",
    "departed", "on_lane", "pending", "peak_queue", "queue_area",
    "mean_queue", "mean_stop_completed_s", "blocked_ticks", "verified",
]
BENCH_FIELDS = [
    "arrival_rate_per_hour", "blockage_enabled", "run_length_s", "seed",
    "ticks", "requested", "departed", "on_lane", "pending", "peak_queue",
    "elapsed_real_s", "ms_per_sim_tick", "conservation_ok",
]
SUMMARY_FIELDS = [
    "arrival_rate_per_hour", "blockage_enabled", "run_length_s",
    "replications", "mean_requested", "mean_peak_queue", "mean_elapsed_real_s",
    "sd_elapsed_real_s", "mean_ms_per_sim_tick", "min_ms_per_sim_tick",
    "max_ms_per_sim_tick", "simulated_seconds_per_real_second",
]
VERIFY_CASES = ("zero_demand", "clear", "clear_repeat", "zero_duration", "blocked")
RATES = (150, 600, 900)
HORIZONS = (600, 1200)
FLAGS = (0, 1)
SEEDS = (201, 202, 203)


def read_csv(path: Path, header: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Missing NetLogo export: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != header:
            raise ValueError(f"Incorrect columns in {path.name}: expected {header}")
        rows = list(reader)
    if any(None in row or any(x is None for x in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV row in {path.name}")
    return rows


def integer(row: dict[str, str], field: str) -> int:
    try:
        num = float(row[field])
        if not math.isfinite(num) or num != int(num):
            raise ValueError
        return int(num)
    except (TypeError, ValueError, OverflowError, KeyError) as exc:
        raise ValueError(f"{field} must be an integer: {row.get(field)!r}") from exc


def finite(row: dict[str, str], field: str) -> float:
    try:
        num = float(row[field])
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError(f"{field} must be finite") from exc
    if not math.isfinite(num):
        raise ValueError(f"{field} must be finite")
    return num


def true_flag(row: dict[str, str], field: str) -> None:
    if row[field].strip().lower() != "true":
        raise ValueError(f"{field} must be true")


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-8)


def check_conservation(row: dict[str, str]) -> None:
    requested = integer(row, "requested")
    departed = integer(row, "departed")
    lane = integer(row, "on_lane")
    pending = integer(row, "pending")
    if min(requested, departed, lane, pending) < 0:
        raise ValueError("Negative cyclist population")
    if requested != departed + lane + pending:
        raise ValueError("Cyclist conservation fails")


def validate_verification(path: Path) -> dict[str, dict[str, str]]:
    data = read_csv(path, VERIFY_FIELDS)
    if len(data) != len(VERIFY_CASES):
        raise ValueError("Verification export must have exactly 5 cases")
    cases: dict[str, dict[str, str]] = {}
    for row in data:
        case = row["case"]
        if case in cases or case not in VERIFY_CASES:
            raise ValueError(f"Duplicate or unknown verification case: {case}")
        true_flag(row, "verified")
        check_conservation(row)
        seed, rate = integer(row, "seed"), integer(row, "arrival_rate_per_hour")
        flag, duration = integer(row, "blockage_enabled"), integer(row, "blockage_duration_s")
        length = integer(row, "run_length_s")
        blocked_ticks = integer(row, "blocked_ticks")
        if seed != 754 or length != 600 or flag not in (0, 1):
            raise ValueError("Unexpected verification scenario parameters")
        if rate != (0 if case == "zero_demand" else 600):
            raise ValueError("Unexpected verification demand rate")
        if flag != int(case in ("zero_duration", "blocked")):
            raise ValueError("Unexpected verification blockage flag")
        if duration != (0 if case == "zero_duration" else 65):
            raise ValueError("Unexpected verification blockage duration")
        if blocked_ticks != (65 if case == "blocked" else 0):
            raise ValueError("Unexpected obstruction activation duration")
        admitted = integer(row, "admitted")
        if admitted < 0 or integer(row, "requested") != admitted + integer(row, "pending"):
            raise ValueError("Admission accounting fails")
        if admitted != integer(row, "departed") + integer(row, "on_lane"):
            raise ValueError("Admitted cyclist accounting fails")
        peak, area = integer(row, "peak_queue"), integer(row, "queue_area")
        mean_queue, stopped = finite(row, "mean_queue"), finite(row, "mean_stop_completed_s")
        if min(peak, area, mean_queue, stopped) < 0 or not close(mean_queue, area / length):
            raise ValueError("Queue statistics inconsistent with tick count")
        cases[case] = row

    if set(cases) != set(VERIFY_CASES):
        raise ValueError("Missing a required verification case")
    zero = cases["zero_demand"]
    if any(integer(zero, f) != 0 for f in ("requested", "departed", "peak_queue", "queue_area")):
        raise ValueError("Zero-demand negative control is not empty")
    controlled_fields = ("requested", "admitted", "departed", "on_lane", "pending",
                         "peak_queue", "queue_area", "mean_queue", "mean_stop_completed_s")
    for case in ("clear_repeat", "zero_duration"):
        if any(not close(finite(cases["clear"], f), finite(cases[case], f))
               for f in controlled_fields):
            raise ValueError(f"Deterministic replay mismatch: {case}")
    blocked = cases["blocked"]
    baseline = cases["clear"]
    if integer(blocked, "requested") != integer(baseline, "requested"):
        raise ValueError("Blocked/clear trials did not receive equal requested demand")
    if (integer(blocked, "peak_queue") < integer(baseline, "peak_queue") or
        finite(blocked, "mean_queue") < finite(baseline, "mean_queue")):
        raise ValueError("Obstruction verification fixture lost its queue effect")
    return cases


def validate_benchmarks(path: Path) -> list[dict[str, str]]:
    data = read_csv(path, BENCH_FIELDS)
    expected = {(r, flag, horizon, seed) for r in RATES for flag in FLAGS
                for horizon in HORIZONS for seed in SEEDS}
    if len(data) != len(expected):
        raise ValueError("Incomplete benchmark grid: expected 36 runs")
    seen = set()
    paired_demands: dict[tuple[int, int, int], int] = {}
    for row in data:
        true_flag(row, "conservation_ok")
        check_conservation(row)
        r = integer(row, "arrival_rate_per_hour")
        flag = integer(row, "blockage_enabled")
        horizon = integer(row, "run_length_s")
        seed = integer(row, "seed")
        key = (r, flag, horizon, seed)
        if key in seen:
            raise ValueError(f"Duplicate benchmark run: {key}")
        seen.add(key)
        if integer(row, "ticks") != horizon:
            raise ValueError("Benchmark ended at the wrong simulated time")
        if integer(row, "peak_queue") < 0:
            raise ValueError("Negative peak queue")
        elapsed = finite(row, "elapsed_real_s")
        per_tick = finite(row, "ms_per_sim_tick")
        if elapsed <= 0 or per_tick <= 0:
            raise ValueError("Measured runtimes must be positive")
        if not close(per_tick, 1000 * elapsed / horizon):
            raise ValueError("Elapsed time and milliseconds per tick disagree")
        demand_key = (r, horizon, seed)
        demand = integer(row, "requested")
        if demand_key in paired_demands and paired_demands[demand_key] != demand:
            raise ValueError("Blocked/clear benchmark demand differs at fixed seed")
        paired_demands[demand_key] = demand
    if seen != expected:
        raise ValueError("Incomplete benchmark design or unexpected configuration")
    return data


def summarize_benchmarks(records: list[dict[str, str]]) -> list[dict[str, float | int]]:
    groups = defaultdict(list)
    for row in records:
        key = (integer(row, "arrival_rate_per_hour"), integer(row, "blockage_enabled"),
               integer(row, "run_length_s"))
        groups[key].append(row)
    result: list[dict[str, float | int]] = []
    for rate, flag, horizon in sorted(groups):
        rows = groups[(rate, flag, horizon)]
        if len(rows) != 3:
            raise ValueError("Each benchmark setting needs exactly three runs")
        seconds = [finite(r, "elapsed_real_s") for r in rows]
        per_tick = [finite(r, "ms_per_sim_tick") for r in rows]
        result.append({
            "arrival_rate_per_hour": rate,
            "blockage_enabled": flag,
            "run_length_s": horizon,
            "replications": len(rows),
            "mean_requested": statistics.mean(integer(r, "requested") for r in rows),
            "mean_peak_queue": statistics.mean(integer(r, "peak_queue") for r in rows),
            "mean_elapsed_real_s": statistics.mean(seconds),
            "sd_elapsed_real_s": statistics.stdev(seconds),
            "mean_ms_per_sim_tick": statistics.mean(per_tick),
            "min_ms_per_sim_tick": min(per_tick),
            "max_ms_per_sim_tick": max(per_tick),
            "simulated_seconds_per_real_second": horizon / statistics.mean(seconds),
        })
    return result


def write_runtime_svg(summary: list[dict[str, float | int]], horizon: int, path: Path) -> None:
    """Lightweight SVG line chart; one horizon per chart, no plotting packages."""
    width, height = 800, 490
    x0, y0, x1, y1 = 105, 70, 746, 390
    rows = [r for r in summary if r["run_length_s"] == horizon]
    ceiling = max(float(r["mean_ms_per_sim_tick"]) for r in rows) * 1.15
    ceiling = max(0.001, ceiling)
    def x(v: int) -> float:
        return x0 + (v - RATES[0]) * (x1 - x0) / (RATES[-1] - RATES[0])
    def y(v: float) -> float:
        return y1 - v * (y1 - y0) / ceiling
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="19" '
        f'font-family="Arial">{escape(f"Cyclistics runtime: {horizon} simulated seconds")}</text>',
        f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="black"/>',
        f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="black"/>',
    ]
    for i in range(5):
        value = ceiling * i / 4
        yy = y(value)
        chunks.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}" '
                      'stroke="#ddd"/>')
        chunks.append(f'<text x="{x0-12}" y="{yy+5:.1f}" text-anchor="end" '
                      f'font-size="12">{value:.3f}</text>')
    for rate in RATES:
        xx = x(rate)
        chunks.append(f'<text x="{xx:.1f}" y="{y1+25}" text-anchor="middle" '
                      f'font-size="13">{rate}</text>')
    chunks.append(f'<text x="{(x0+x1)/2}" y="{height-48}" text-anchor="middle" '
                  'font-size="14">Requested arrivals (cyclists/hour)</text>')
    chunks.append(f'<text x="19" y="{(y0+y1)/2}" text-anchor="middle" font-size="14" '
                  'transform="rotate(-90 19 230)">Measured ms per simulation tick</text>')
    for flag, color, style, label in ((0, '#293f59', 'none', 'No obstruction'),
                                       (1, '#cf6e34', '8 4', 'Obstruction')):
        line = sorted((r for r in rows if r["blockage_enabled"] == flag),
                      key=lambda r: r["arrival_rate_per_hour"])
        points = ' '.join(f'{x(int(r["arrival_rate_per_hour"])):.1f},'
                          f'{y(float(r["mean_ms_per_sim_tick"])):.1f}' for r in line)
        chunks.append(f'<polyline points="{points}" fill="none" stroke="{color}" '
                      f'stroke-width="3" stroke-dasharray="{style}"/>')
        for r in line:
            chunks.append(f'<circle cx="{x(int(r["arrival_rate_per_hour"])):.1f}" '
                          f'cy="{y(float(r["mean_ms_per_sim_tick"])):.1f}" '
                          f'r="5" fill="white" stroke="{color}" stroke-width="2"/>')
        chunks.append(f'<text x="{x0+flag*245}" y="{height-12}" '
                      f'font-size="13" fill="{color}">{label}</text>')
    chunks.append('</svg>')
    path.write_text('\n'.join(chunks) + '\n', encoding='utf-8')


def analyze(verification: Path, benchmarks: Path, output_dir: Path) -> None:
    verified = validate_verification(verification)
    records = validate_benchmarks(benchmarks)
    summary = summarize_benchmarks(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_file = output_dir / 'netlogo_runtime_summary.csv'
    with summary_file.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary)
    for horizon in HORIZONS:
        write_runtime_svg(summary, horizon, output_dir / f'netlogo_runtime_{horizon}s.svg')
    report = {
        'verification_status': 'passed',
        'verification_cases': list(verified),
        'per_tick_invariant_checks': True,
        'benchmark_runs': len(records),
        'benchmark_summary_groups': len(summary),
        'methodology': 'NetLogo timer for go() ticks; setup excluded; graphics suppressed',
        'interpretation': 'Internal verification and local computational benchmarks only; '
                          'not empirical validation of NYC conditions',
    }
    (output_dir / 'netlogo_verification_report.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: verified 5 NetLogo checks including exact replay and obstruction timing')
    print('PASS: validated 36 runtime benchmark measurements')
    print('PASS: summarized 12 configurations (3 arrival rates x 2 blockage flags x 2 horizons)')
    print(f'Wrote: {summary_file}')
    for horizon in HORIZONS:
        print(f'Wrote: {output_dir / f"netlogo_runtime_{horizon}s.svg"}')
    print('NOTE: measured runtimes depend on the local computer and are not NYC validation.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', required=True, type=Path)
    parser.add_argument('--benchmarks', required=True, type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('outputs'))
    args = parser.parse_args()
    analyze(args.verification, args.benchmarks, args.output_dir)


if __name__ == '__main__':
    main()
