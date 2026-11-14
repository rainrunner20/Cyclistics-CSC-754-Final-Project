"""Analyze Cyclistics synthetic NetLogo obstruction sensitivity experiments.

Usage (repository root, with Python 3.11+):
    python -m cyclistics.netlogo_sensitivity --input outputs/netlogo_sensitivity_raw.csv --output-dir outputs

Only Python's standard library is required. This does not run NetLogo itself.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

RATES = (150, 300, 600, 900)
DURATIONS = (0, 30, 60, 120)
SEEDS = tuple(range(101, 111))
EXPECTED_START = 45
EXPECTED_HORIZON = 600
# Student's t critical value (two-sided 95% interval; df = 9).
T_CRIT_95_DF9 = 2.2621571627409915

COLUMNS = (
    "arrival_rate_per_hour", "blockage_duration_s", "seed", "blockage_start_s",
    "run_length_s", "requested", "clear_departed", "blocked_departed",
    "delta_departed", "clear_peak_queue", "blocked_peak_queue", "delta_peak_queue",
    "clear_mean_queue", "blocked_mean_queue", "delta_mean_queue",
    "clear_mean_stop_completed_s", "blocked_mean_stop_completed_s",
    "delta_mean_stop_completed_s", "clear_remaining", "blocked_remaining",
    "conservation_ok", "paired_inputs_ok",
)
INTEGER_COLUMNS = (
    "arrival_rate_per_hour", "blockage_duration_s", "seed", "blockage_start_s",
    "run_length_s", "requested", "clear_departed", "blocked_departed",
    "delta_departed", "clear_peak_queue", "blocked_peak_queue", "delta_peak_queue",
    "clear_remaining", "blocked_remaining",
)
NUMERIC_COLUMNS = COLUMNS[:-2]
PAIR_METRICS = (
    ("departed", "delta_departed"),
    ("peak_queue", "delta_peak_queue"),
    ("mean_queue", "delta_mean_queue"),
    ("mean_stop_completed_s", "delta_mean_stop_completed_s"),
)


def _float(text: str, field: str, row_number: int) -> float:
    try:
        result = float(text)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Row {row_number}: {field} is not numeric: {text!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"Row {row_number}: {field} must be finite")
    return result


def read_and_validate(source: Path) -> list[dict[str, float]]:
    """Require the exact 4x4x10 design, matched inputs, and conservation.

    A malformed or incomplete experiment should fail rather than generate a
    potentially misleading figure for the course report.
    """
    if not source.is_file():
        raise FileNotFoundError(f"NetLogo CSV not found: {source}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(reader.fieldnames) != set(COLUMNS):
            raise ValueError("NetLogo CSV columns do not match the sensitivity schema")
        parsed = []
        combinations = set()
        clear_baselines: dict[tuple[int, int], tuple[float, ...]] = {}
        for line, raw in enumerate(reader, 2):
            row = {key: _float(raw[key], key, line) for key in NUMERIC_COLUMNS}
            for field in INTEGER_COLUMNS:
                if not row[field].is_integer():
                    raise ValueError(f"Row {line}: {field} must be an integer")
            for key in ("conservation_ok", "paired_inputs_ok"):
                if (raw[key] or "").strip().lower() != "true":
                    raise ValueError(f"Row {line}: {key} is not true")
            rate = int(row["arrival_rate_per_hour"])
            duration = int(row["blockage_duration_s"])
            seed = int(row["seed"])
            key = (rate, duration, seed)
            if key in combinations:
                raise ValueError(f"Duplicate experiment combination: {key}")
            combinations.add(key)
            if (row["blockage_start_s"] != EXPECTED_START or
                    row["run_length_s"] != EXPECTED_HORIZON):
                raise ValueError(f"Row {line}: unexpected start time or horizon")

            for metric, delta in PAIR_METRICS:
                actual_delta = row[f"blocked_{metric}"] - row[f"clear_{metric}"]
                if not math.isclose(row[delta], actual_delta, abs_tol=1e-7, rel_tol=1e-9):
                    raise ValueError(f"Row {line}: {delta} does not equal blocked - clear")
            for label in ("clear", "blocked"):
                if not math.isclose(
                    row["requested"], row[f"{label}_departed"] + row[f"{label}_remaining"],
                    abs_tol=1e-8, rel_tol=0,
                ):
                    raise ValueError(f"Row {line}: {label} cyclist conservation fails")
                for metric in ("departed", "peak_queue", "mean_queue",
                               "mean_stop_completed_s", "remaining"):
                    if row[f"{label}_{metric}"] < 0:
                        raise ValueError(f"Row {line}: {label}_{metric} cannot be negative")
            if duration == 0:
                for metric, _ in PAIR_METRICS:
                    if not math.isclose(row[f"blocked_{metric}"], row[f"clear_{metric}"],
                                        abs_tol=1e-9, rel_tol=0):
                        raise ValueError(f"Row {line}: zero-duration scenario must equal clear baseline")

            baseline_key = (rate, seed)
            baseline = (
                row["requested"], row["clear_departed"], row["clear_peak_queue"],
                row["clear_mean_queue"], row["clear_mean_stop_completed_s"],
                row["clear_remaining"],
            )
            if baseline_key in clear_baselines and baseline != clear_baselines[baseline_key]:
                raise ValueError(f"Row {line}: same rate/seed has inconsistent clear baseline")
            clear_baselines[baseline_key] = baseline
            parsed.append(row)

    expected = {(r, d, s) for r in RATES for d in DURATIONS for s in SEEDS}
    if combinations != expected:
        missing = sorted(expected - combinations)
        unexpected = sorted(combinations - expected)
        raise ValueError(
            f"Incomplete sensitivity grid: {len(combinations)}/{len(expected)} rows; "
            f"missing={missing[:4]}, unexpected={unexpected[:4]}"
        )
    return parsed


def mean_and_ci(values: list[float]) -> tuple[float, float, float, float]:
    n = len(values)
    if n != len(SEEDS):
        raise ValueError(f"Expected {len(SEEDS)} independent seeds, got {n}")
    mu = statistics.mean(values)
    sd = statistics.stdev(values)
    half_width = T_CRIT_95_DF9 * sd / math.sqrt(n)
    return mu, sd, mu - half_width, mu + half_width


def summarize(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    groups = defaultdict(list)
    for row in rows:
        groups[(int(row["arrival_rate_per_hour"]), int(row["blockage_duration_s"]))].append(row)
    summary = []
    for rate in RATES:
        for duration in DURATIONS:
            group = groups.get((rate, duration), [])
            if len(group) != len(SEEDS) or sorted(int(x["seed"]) for x in group) != list(SEEDS):
                raise ValueError(f"Rate {rate}, duration {duration}: incomplete seed replication")
            entry: dict[str, float] = {
                "arrival_rate_per_hour": rate,
                "blockage_duration_s": duration,
                "replications": len(group),
            }
            for field in ("requested", "clear_departed", "blocked_departed",
                          "clear_mean_queue", "blocked_mean_queue"):
                entry[f"avg_{field}"] = statistics.mean(x[field] for x in group)
            for _, delta in PAIR_METRICS:
                mu, sd, lower, upper = mean_and_ci([x[delta] for x in group])
                entry[f"avg_{delta}"] = mu
                entry[f"sd_{delta}"] = sd
                entry[f"ci95_low_{delta}"] = lower
                entry[f"ci95_high_{delta}"] = upper
            summary.append(entry)
    return summary


def save_csv(summary: list[dict[str, float]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        for row in summary:
            writer.writerow({k: f"{v:.6f}" if isinstance(v, float) else v
                             for k, v in row.items()})


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
COLORS = {150: "#057A73", 300: "#D9773C", 600: "#2666B3", 900: "#7549A6"}


def render_svg(summary: list[dict[str, float]], metric: str, title: str, unit: str,
               filepath: Path) -> None:
    """Produce a clean, vector, dependency-free plot for reports/slides."""
    width, height = 1000, 650
    x0, y0, x1, y1 = 112, 150, 930, 545
    rows = {(int(x["arrival_rate_per_hour"]), int(x["blockage_duration_s"])): x
            for x in summary}
    lows = [r[f"ci95_low_{metric}"] for r in summary] + [0]
    highs = [r[f"ci95_high_{metric}"] for r in summary] + [0]
    min_data, max_data = min(lows), max(highs)
    extent = max(0.2, max_data - min_data)
    y_min = min(0, min_data - extent * 0.12)
    y_max = max(0, max_data + extent * 0.12)
    if y_max <= y_min:
        y_max = y_min + 1

    def sx(duration: int) -> float:
        return x0 + (duration / max(DURATIONS)) * (x1 - x0)

    def sy(value: float) -> float:
        return y1 - ((value - y_min) / (y_max - y_min)) * (y1 - y0)

    svg = ET.Element(f"{{{SVG_NS}}}svg", {
        "viewBox": f"0 0 {width} {height}", "width": str(width), "height": str(height),
        "role": "img", "aria-label": title,
    })

    def add(tag: str, attrs: dict[str, object], content: str | None = None):
        e = ET.SubElement(svg, f"{{{SVG_NS}}}{tag}", {k: str(v) for k,v in attrs.items()})
        if content is not None: e.text = content
        return e

    add("rect", {"width": width, "height": height, "fill": "#FFFFFF"})
    add("text", {"x": x0, "y": 52, "fill": "#17253B", "font-family": "Arial, sans-serif",
                 "font-size": 29, "font-weight": 700}, title)
    add("text", {"x": x0, "y": 85, "fill": "#59677D", "font-family": "Arial, sans-serif",
                 "font-size": 15}, "Synthetic NetLogo scenarios · paired across 10 seeds · mean ± 95% t interval")
    for idx, rate in enumerate(RATES):
        x = x0 + idx * 194
        add("line", {"x1": x, "y1": 117, "x2": x + 36, "y2": 117,
                     "stroke": COLORS[rate], "stroke-width": 3})
        add("text", {"x": x + 43, "y": 122, "font-family": "Arial, sans-serif",
                     "font-size": 15, "fill": "#344358"}, f"{rate} cyclists/hr")
    for idx in range(6):
        val = y_min + (y_max - y_min) * idx / 5
        py = sy(val)
        add("line", {"x1": x0, "y1": f"{py:.1f}", "x2": x1, "y2": f"{py:.1f}",
                     "stroke": "#E9EDF2", "stroke-width": 1})
        add("text", {"x": x0 - 13, "y": f"{py + 5:.1f}", "text-anchor": "end",
                     "font-size": 14, "font-family": "Arial, sans-serif", "fill": "#58677D"}, f"{val:.2f}")
    for duration in DURATIONS:
        px = sx(duration)
        add("text", {"x": f"{px:.1f}", "y": y1 + 28, "text-anchor": "middle",
                     "font-size": 15, "font-family": "Arial, sans-serif", "fill": "#3D5068"}, str(duration))
    add("line", {"x1": x0, "y1": y1, "x2": x1, "y2": y1,
                 "stroke": "#8290A3", "stroke-width": 1.3})
    add("text", {"x": (x0+x1)/2, "y": 617, "text-anchor": "middle",
                 "font-family": "Arial, sans-serif", "font-size": 17,
                 "fill": "#344358"}, "Obstruction duration (seconds)")
    add("text", {"transform": f"translate(30 {(y0+y1)/2}) rotate(-90)",
                 "font-family": "Arial, sans-serif", "font-size": 16,
                 "text-anchor": "middle", "fill": "#344358"}, unit)
    for rate in RATES:
        pts = []
        for dur in DURATIONS:
            row = rows[(rate, dur)]
            mu = row[f"avg_{metric}"]
            lo = row[f"ci95_low_{metric}"]
            hi = row[f"ci95_high_{metric}"]
            px, py = sx(dur), sy(mu)
            pts.append(f"{px:.2f},{py:.2f}")
            add("line", {"x1": f"{px:.2f}", "y1": f"{sy(lo):.2f}",
                         "x2": f"{px:.2f}", "y2": f"{sy(hi):.2f}",
                         "stroke": COLORS[rate], "stroke-width": 2, "stroke-opacity": 0.76})
            for v in (lo, hi):
                pvy = sy(v)
                add("line", {"x1": f"{px-5:.2f}", "y1": f"{pvy:.2f}",
                             "x2": f"{px+5:.2f}", "y2": f"{pvy:.2f}",
                             "stroke": COLORS[rate], "stroke-width": 1.9})
        add("polyline", {"points": " ".join(pts), "fill": "none",
                         "stroke": COLORS[rate], "stroke-width": 3,
                         "stroke-linejoin": "round", "stroke-linecap": "round"})
        for dur in DURATIONS:
            row = rows[(rate,dur)]
            add("circle", {"cx": f"{sx(dur):.2f}", "cy": f"{sy(row[f'avg_{metric}']):.2f}",
                           "r": 5, "fill": COLORS[rate], "stroke": "#FFF", "stroke-width": 1.5})
    add("text", {"x": x0, "y": 642, "font-size": 12,
                 "font-family": "Arial, sans-serif", "fill": "#69768A"},
        "Difference = obstructed minus clear. Internal simulation results, not NYC measurements.")
    ET.ElementTree(svg).write(filepath, encoding="utf-8", xml_declaration=True)


def analyze(source: Path, destination: Path) -> list[dict[str, float]]:
    parsed = read_and_validate(source)
    summary = summarize(parsed)
    destination.mkdir(parents=True, exist_ok=True)
    save_csv(summary, destination / "netlogo_sensitivity_summary.csv")
    render_svg(summary, "delta_mean_queue", "Queueing response to lane obstruction",
               "Change in mean queue (cyclists)", destination / "netlogo_delta_mean_queue.svg")
    render_svg(summary, "delta_peak_queue", "Peak queue response to lane obstruction",
               "Change in peak queue (cyclists)", destination / "netlogo_delta_peak_queue.svg")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("outputs/netlogo_sensitivity_raw.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    summary = analyze(args.input, args.output_dir)
    print(f"PASS: validated {len(RATES)*len(DURATIONS)*len(SEEDS)} paired experiment rows")
    print(f"PASS: generated {len(summary)} aggregated scenarios with 10-seed t intervals")
    print(f"Wrote: {args.output_dir/'netlogo_sensitivity_summary.csv'}")
    print(f"Wrote: {args.output_dir/'netlogo_delta_mean_queue.svg'}")
    print(f"Wrote: {args.output_dir/'netlogo_delta_peak_queue.svg'}")
    print("NOTE: these are simulation outputs, not measured NYC congestion effects.")


if __name__ == "__main__":
    main()
