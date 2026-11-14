"""Validate NetLogo bench analysis with fabricated *test fixtures*, not research data."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from cyclistics.netlogo_benchmarks import (
    BENCH_FIELDS, VERIFY_FIELDS, RATES, SEEDS, HORIZONS, FLAGS,
    analyze, summarize_benchmarks, validate_benchmarks, validate_verification,
)


def verification_fixture():
    columns = {
        'seed': 754, 'arrival_rate_per_hour': 600, 'blockage_enabled': 0,
        'blockage_duration_s': 65, 'run_length_s': 600,
        'requested': 107, 'admitted': 107, 'departed': 96, 'on_lane': 11,
        'pending': 0, 'peak_queue': 1, 'queue_area': 14,
        'mean_queue': 14 / 600, 'mean_stop_completed_s': 0,
        'blocked_ticks': 0, 'verified': 'true',
    }
    cases = []
    for name in ('zero_demand', 'clear', 'clear_repeat', 'zero_duration', 'blocked'):
        row = {'case': name, **columns}
        if name == 'zero_demand':
            row.update(arrival_rate_per_hour=0, requested=0, admitted=0,
                       departed=0, on_lane=0, peak_queue=0, queue_area=0, mean_queue=0)
        elif name == 'zero_duration':
            row.update(blockage_enabled=1, blockage_duration_s=0)
        elif name == 'blocked':
            row.update(blockage_enabled=1, peak_queue=21, queue_area=790,
                       mean_queue=790 / 600, mean_stop_completed_s=8.094, blocked_ticks=65)
        cases.append(row)
    return cases


def benchmark_fixture():
    rows = []
    for rate in RATES:
        for horizon in HORIZONS:
            for flag in FLAGS:
                for seed in SEEDS:
                    arrivals = int(horizon * rate / 3600) + seed % 5
                    elapsed = ((0.025 + rate / 50000) * (horizon / 600) *
                               (1 + 0.04 * (seed-201)) * (1 + 0.05 * flag))
                    rows.append({
                        'arrival_rate_per_hour': rate, 'blockage_enabled': flag,
                        'run_length_s': horizon, 'seed': seed, 'ticks': horizon,
                        'requested': arrivals, 'departed': arrivals - 2,
                        'on_lane': 2, 'pending': 0, 'peak_queue': 1 + 4 * flag,
                        'elapsed_real_s': elapsed, 'ms_per_sim_tick': 1000 * elapsed / horizon,
                        'conservation_ok': 'true',
                    })
    return rows


def write_csv(path: Path, fields: list[str], rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class NetLogoBenchmarkAnalysisTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.work = Path(tmp.name)
        self.verification = self.work / 'checks.csv'
        self.benchmarks = self.work / 'benchmarks.csv'
        self.vrows = verification_fixture()
        self.brows = benchmark_fixture()
        self.save()

    def save(self):
        write_csv(self.verification, VERIFY_FIELDS, self.vrows)
        write_csv(self.benchmarks, BENCH_FIELDS, self.brows)

    def test_five_verification_cases(self):
        self.assertEqual(len(validate_verification(self.verification)), 5)

    def test_rejects_missing_case(self):
        self.vrows.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, 'exactly 5'):
            validate_verification(self.verification)

    def test_rejects_replay_mismatch(self):
        self.vrows[2]['peak_queue'] = 9
        self.save()
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            validate_verification(self.verification)

    def test_rejects_zero_duration_mismatch(self):
        self.vrows[3]['peak_queue'] = 9
        self.save()
        with self.assertRaisesRegex(ValueError, 'replay mismatch'):
            validate_verification(self.verification)

    def test_rejects_bad_queue_area(self):
        self.vrows[4]['mean_queue'] = 500
        self.save()
        with self.assertRaisesRegex(ValueError, 'Queue statistics'):
            validate_verification(self.verification)

    def test_exact_36_benchmarks(self):
        self.assertEqual(len(validate_benchmarks(self.benchmarks)), 36)

    def test_rejects_missing_benchmark(self):
        self.brows.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, 'Incomplete benchmark grid'):
            validate_benchmarks(self.benchmarks)

    def test_rejects_duplicate_benchmark(self):
        self.brows[1] = dict(self.brows[0])
        self.save()
        with self.assertRaisesRegex(ValueError, 'Duplicate benchmark'):
            validate_benchmarks(self.benchmarks)

    def test_rejects_non_finite_runtime(self):
        self.brows[0]['elapsed_real_s'] = 'Infinity'
        self.save()
        with self.assertRaisesRegex(ValueError, 'finite'):
            validate_benchmarks(self.benchmarks)

    def test_rejects_broken_runtime_calculation(self):
        self.brows[0]['ms_per_sim_tick'] = '999'
        self.save()
        with self.assertRaisesRegex(ValueError, 'disagree'):
            validate_benchmarks(self.benchmarks)

    def test_rejects_mismatched_benchmark_demand(self):
        self.brows[3]['requested'] += 1
        self.brows[3]['on_lane'] += 1
        self.save()
        with self.assertRaisesRegex(ValueError, 'demand differs'):
            validate_benchmarks(self.benchmarks)

    def test_rejects_conservation_error(self):
        self.brows[0]['pending'] = 10
        self.save()
        with self.assertRaisesRegex(ValueError, 'conservation'):
            validate_benchmarks(self.benchmarks)

    def test_summary_contains_twelve_configurations(self):
        rows = summarize_benchmarks(validate_benchmarks(self.benchmarks))
        self.assertEqual(len(rows), 12)
        row = next(x for x in rows if x['arrival_rate_per_hour'] == 900 and
                   x['blockage_enabled'] == 1 and x['run_length_s'] == 1200)
        self.assertEqual(row['replications'], 3)
        self.assertGreater(row['mean_ms_per_sim_tick'], 0)
        self.assertGreater(row['simulated_seconds_per_real_second'], 0)

    def test_cli_outputs_valid_report_and_charts(self):
        target = self.work / 'outputs'
        analyze(self.verification, self.benchmarks, target)
        with (target / 'netlogo_runtime_summary.csv').open(newline='') as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 12)
        for horizon in HORIZONS:
            root = ElementTree.parse(target / f'netlogo_runtime_{horizon}s.svg').getroot()
            self.assertTrue(root.tag.endswith('svg'))
        report = json.loads((target / 'netlogo_verification_report.json').read_text())
        self.assertEqual(report['benchmark_runs'], 36)
        self.assertEqual(report['verification_status'], 'passed')


if __name__ == '__main__':
    unittest.main()
