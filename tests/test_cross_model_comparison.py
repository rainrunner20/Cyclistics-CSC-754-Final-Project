"""Contract tests for a *limited* cross-model evidence report.

Java stdout fixtures here are invented for testing the parser. They do not
prove that a real DEVS-Suite run took place.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cyclistics.cross_model_comparison import (
    compare_models, parse_java_log, parse_netlogo_pair, write_report,
)

FAKE_JAVA_LOG = """Compiling real production classes against DEVS-Suite...
Starting DEVS-Suite coordinator (headless)...
DEPARTURE,14.000,cyclist-1
DEPARTURE,24.000,cyclist-2
Cyclistics coupled-DEVS summary:
  generated=2
  obstruction events=2
  departed=2
  max waiting=1
  remaining=0
PASS: real coordinator departure timestamps match 14s and 24s.
"""

COLUMNS = ["scenario", "blockage_enabled", "seed", "arrival_rate_per_hour",
           "blockage_start_s", "blockage_duration_s", "run_length_s",
           "requested", "departed", "on_lane", "pending", "peak_queue",
           "mean_queue", "mean_stop_completed_s", "conservation_ok"]


def paired_csv() -> str:
    rows = [
        ["clear", "0", "754", "99", "45", "65", "600",
         "13", "12", "1", "0", "0", "0", "0", "true"],
        ["blocked", "1", "754", "99", "45", "65", "600",
         "13", "12", "1", "0", "3", "0.158", "7.917", "true"],
    ]
    import io
    handle = io.StringIO(newline="")
    writer = csv.writer(handle)
    writer.writerow(COLUMNS)
    writer.writerows(rows)
    return handle.getvalue()


class CrossModelComparisonTests(unittest.TestCase):
    def test_python_reference_scenario_matches_expected_devs_events(self):
        report = compare_models()
        ref = report["python_reference"]
        self.assertEqual(ref["ordered_departure_seconds"], [14.0, 24.0])
        self.assertEqual(ref["peak_waiting_queue"], 1)
        self.assertEqual(ref["mean_wait_seconds"], 2.5)
        self.assertEqual(ref["arrival_seconds"], [10.0, 15.0])

    def test_without_real_java_evidence_reports_pending_not_parity(self):
        report = compare_models()
        self.assertEqual(report["java_comparison"]["status"], "pending_real_coordinator_log")
        self.assertEqual(report["netlogo_comparison"]["status"], "not_supplied")
        self.assertFalse(report["same_three_model_scenario"])
        self.assertFalse(report["field_validated"])

    def test_java_stdout_is_compared_to_python_reference(self):
        result = parse_java_log(FAKE_JAVA_LOG, [14.0, 24.0], expected_queue=1)
        self.assertEqual(result["status"], "matches_python_deterministic_fixture")
        self.assertEqual(result["departure_seconds"], [14.0, 24.0])

    def test_java_log_rejects_swapped_order_and_wrong_time(self):
        for log in (FAKE_JAVA_LOG.replace("DEPARTURE,14.000,cyclist-1", "DEPARTURE,24.000,cyclist-1"),
                    FAKE_JAVA_LOG.replace("DEPARTURE,24.000,cyclist-2", "DEPARTURE,25.000,cyclist-2")):
            with self.subTest(log=log):
                with self.assertRaises(ValueError):
                    parse_java_log(log, [14.0, 24.0], expected_queue=1)

    def test_java_log_rejects_claimed_pass_without_events(self):
        with self.assertRaises(ValueError):
            parse_java_log("PASS: real coordinator departure timestamps match 14s and 24s.",
                           [14.0, 24.0], expected_queue=1)

    def test_java_log_rejects_wrong_counts_and_duplicates(self):
        for log in (FAKE_JAVA_LOG.replace("generated=2", "generated=3"),
                    FAKE_JAVA_LOG.replace("DEPARTURE,24.000,cyclist-2",
                                          "DEPARTURE,14.000,cyclist-1")):
            with self.subTest(log=log):
                with self.assertRaises(ValueError):
                    parse_java_log(log, [14.0, 24.0], expected_queue=1)

    def test_netlogo_pair_keeps_two_compatible_inputs(self):
        rows = list(csv.DictReader(paired_csv().splitlines()))
        result = parse_netlogo_pair(rows)
        self.assertEqual(result["status"], "within_netlogo_consistent_only")
        self.assertEqual(result["seed"], 754)
        self.assertEqual(result["requested_cyclists_each"], 13)
        self.assertAlmostEqual(result["blocked_minus_clear"]["mean_queue"], 0.158)
        self.assertAlmostEqual(result["blocked_minus_clear"]["mean_stop_completed_s"], 7.917)

    def test_netlogo_rejects_mismatched_seed_demand_or_bad_conservation(self):
        for changed, value in (("seed", "755"), ("requested", "14"),
                               ("conservation_ok", "false"),
                               ("blockage_start_s", "99")):
            rows = list(csv.DictReader(paired_csv().splitlines()))
            rows[1][changed] = value
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    parse_netlogo_pair(rows)

    def test_netlogo_rejects_extra_row_and_non_finite_measurement(self):
        rows = list(csv.DictReader(paired_csv().splitlines()))
        with self.assertRaises(ValueError):
            parse_netlogo_pair(rows + [rows[0]])
        rows[1]["mean_queue"] = "nan"
        with self.assertRaises(ValueError):
            parse_netlogo_pair(rows)

    def test_report_includes_hashes_but_never_claims_field_validation(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            j = folder / "java.log"
            n = folder / "paired.csv"
            out = folder / "comparison.json"
            j.write_text(FAKE_JAVA_LOG, encoding="utf-8")
            n.write_text(paired_csv(), encoding="utf-8")
            result = write_report(out, java_log=j, netlogo_paired=n)
            self.assertEqual(result["java_comparison"]["status"],
                             "matches_python_deterministic_fixture")
            self.assertEqual(result["netlogo_comparison"]["status"],
                             "within_netlogo_consistent_only")
            self.assertEqual(result["inputs_sha256"]["java_log"],
                             hashlib.sha256(j.read_bytes()).hexdigest())
            self.assertTrue(out.is_file())
            self.assertFalse(result["same_three_model_scenario"])
            self.assertFalse(result["field_validated"])

    def test_invalid_input_does_not_write_new_partial_report(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            j = folder / "java.log"
            out = folder / "comparison.json"
            j.write_text("incomplete", encoding="utf-8")
            with self.assertRaises(ValueError):
                write_report(out, java_log=j)
            self.assertFalse(out.exists())

    def test_cli_can_make_clearly_incomplete_report(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "comparison.json"
            command = [sys.executable, "-m", "cyclistics.cross_model_comparison",
                       "--output", str(out)]
            result = subprocess.run(command, capture_output=True, text=True,
                                    timeout=12)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))
                             ["java_comparison"]["status"], "pending_real_coordinator_log")


if __name__ == "__main__":
    unittest.main()
