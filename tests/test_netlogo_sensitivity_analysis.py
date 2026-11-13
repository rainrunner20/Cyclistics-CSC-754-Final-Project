"""Verify CSV validation, paired means, t intervals, and report graphics.

These tests use synthetic in-memory fixtures; only NetLogo desktop actually
executes the ABM. Never mistake fixture data for empirical model results.
"""
import csv
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from cyclistics.netlogo_sensitivity import (
    COLUMNS, DURATIONS, RATES, SEEDS, analyze, mean_and_ci, read_and_validate, summarize,
)


def sample_records():
    rows = []
    for rate in RATES:
        for seed in SEEDS:
            requested = 25 + rate // 30 + seed % 4
            clear_departed = requested - 2
            clear_peak = 1
            clear_mean = 0.05
            clear_stop = 0.0
            for dur in DURATIONS:
                blocked_departed = clear_departed - dur // 60
                blocked_peak = clear_peak + dur // 15 + (seed % 2 if dur else 0)
                blocked_mean = clear_mean + dur * (rate / 600) * (1 + (seed % 3) / 5) / 100
                blocked_stop = dur * (1 + (seed % 3) / 6) / 12
                values = [
                    rate, dur, seed, 45, 600, requested,
                    clear_departed, blocked_departed, blocked_departed - clear_departed,
                    clear_peak, blocked_peak, blocked_peak - clear_peak,
                    clear_mean, blocked_mean, blocked_mean - clear_mean,
                    clear_stop, blocked_stop, blocked_stop - clear_stop,
                    requested - clear_departed, requested - blocked_departed,
                    "true", "true",
                ]
                rows.append(dict(zip(COLUMNS, values)))
    return rows


def write_fixture(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


class SensitivityAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "input.csv"
        self.records = sample_records()
        write_fixture(self.path, self.records)

    def test_exact_replicated_design(self):
        records = read_and_validate(self.path)
        self.assertEqual(len(records), 160)
        self.assertEqual({(int(x["arrival_rate_per_hour"]), int(x["blockage_duration_s"]))
                          for x in records}, {(r, d) for r in RATES for d in DURATIONS})

    def test_summary_uses_paired_differences(self):
        summary = summarize(read_and_validate(self.path))
        self.assertEqual(len(summary), 16)
        row = next(x for x in summary if x["arrival_rate_per_hour"] == 600
                   and x["blockage_duration_s"] == 60)
        self.assertAlmostEqual(row["avg_delta_departed"], -1)
        self.assertAlmostEqual(row["avg_delta_peak_queue"], 4.5)
        self.assertEqual(row["replications"], 10)
        self.assertLess(row["ci95_low_delta_mean_queue"], row["avg_delta_mean_queue"])
        self.assertGreater(row["ci95_high_delta_mean_queue"], row["avg_delta_mean_queue"])

    def test_zero_duration_delta_is_exactly_zero(self):
        summary = summarize(read_and_validate(self.path))
        for r in summary:
            if r["blockage_duration_s"] == 0:
                self.assertEqual(r["avg_delta_departed"], 0)
                self.assertEqual(r["avg_delta_mean_queue"], 0)
                self.assertEqual(r["avg_delta_peak_queue"], 0)

    def test_sample_sd_and_t_ci(self):
        mean, sd, low, high = mean_and_ci(list(range(1, 11)))
        self.assertEqual(mean, 5.5)
        self.assertAlmostEqual(sd, 3.0276503541, places=8)
        self.assertAlmostEqual(mean - low, 2.2621571627409915 * sd / (10 ** 0.5))
        self.assertAlmostEqual(high - mean, mean - low)

    def test_cli_outputs_valid_svg_and_summary(self):
        out = self.root / "outputs"
        analyze(self.path, out)
        with (out / "netlogo_sensitivity_summary.csv").open(newline="") as f:
            data = list(csv.DictReader(f))
        self.assertEqual(len(data), 16)
        for filename in ("netlogo_delta_mean_queue.svg", "netlogo_delta_peak_queue.svg"):
            tree = ElementTree.parse(out / filename)
            self.assertTrue(tree.getroot().tag.endswith("svg"))
            self.assertGreater((out / filename).stat().st_size, 10000)

    def test_rejects_missing_scenario(self):
        write_fixture(self.path, self.records[:-1])
        with self.assertRaisesRegex(ValueError, "Incomplete sensitivity grid"):
            read_and_validate(self.path)

    def test_rejects_duplicate_scenario(self):
        write_fixture(self.path, self.records + [self.records[0]])
        with self.assertRaisesRegex(ValueError, "Duplicate experiment combination"):
            read_and_validate(self.path)

    def test_rejects_wrong_delta(self):
        self.records[18]["delta_mean_queue"] = 999
        write_fixture(self.path, self.records)
        with self.assertRaisesRegex(ValueError, "delta_mean_queue does not equal"):
            read_and_validate(self.path)

    def test_rejects_broken_conservation(self):
        self.records[18]["blocked_remaining"] = 999
        write_fixture(self.path, self.records)
        with self.assertRaisesRegex(ValueError, "cyclist conservation fails"):
            read_and_validate(self.path)

    def test_rejects_unmatched_baselines(self):
        self.records[1]["clear_mean_queue"] = 20
        self.records[1]["delta_mean_queue"] = self.records[1]["blocked_mean_queue"] - 20
        write_fixture(self.path, self.records)
        with self.assertRaisesRegex(ValueError, "inconsistent clear baseline"):
            read_and_validate(self.path)

    def test_rejects_invalid_pair_flag(self):
        self.records[19]["paired_inputs_ok"] = "false"
        write_fixture(self.path, self.records)
        with self.assertRaisesRegex(ValueError, "paired_inputs_ok is not true"):
            read_and_validate(self.path)

    def test_rejects_non_finite_metrics(self):
        self.records[19]["blocked_mean_queue"] = "NaN"
        write_fixture(self.path, self.records)
        with self.assertRaisesRegex(ValueError, "must be finite"):
            read_and_validate(self.path)


if __name__ == "__main__":
    unittest.main()
