"""Tests for counter-quality diagnostics; all observations here are synthetic."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics.nyc_data_quality import analyze_snapshot, write_report


def build_snapshot(*, counts=(1, 4, 3, 2), add_second_flow=True) -> dict:
    start = datetime(2026, 10, 15, 8)
    rows = []
    flows = [("in", "F1", counts)]
    if add_second_flow:
        flows += [("in", "F2", (5, 8, 7, 6)), ("out", "F3", (3, 2, 3, 2))]
    for direction, flow_id, amounts in flows:
        for index, count in enumerate(amounts):
            rows.append({
                "sensor_id": "demo-sensor", "travelmode": "bike",
                "granularity": "PT15M", "direction": direction,
                "flowid": flow_id, "status": "raw",
                "timestamp": (start + timedelta(minutes=15 * index)).isoformat(),
                "counts": str(count),
            })
    return {"dataset": "counts", "dataset_id": "ct66-47at",
            "source": "Synthetic test data; not NYC measurements", "records": rows}


def sensor_metadata() -> dict:
    return {"dataset": "sensors", "records": [
        {"id": "demo-sensor", "counters_id": "first-hardware"},
        {"id": "demo-sensor", "counters_id": "replacement-hardware"},
        {"id": "other-sensor", "counters_id": "irrelevant"},
    ]}


def stream(report, flow_id):
    return next(row for row in report["streams"] if row["flowid"] == flow_id)


class NYCDataQualityTests(unittest.TestCase):
    def test_each_flow_kept_separate_and_candidate_rates_are_not_summed(self):
        report = analyze_snapshot(build_snapshot())
        self.assertEqual(report["record_count"], 12)
        self.assertEqual(report["stream_count"], 3)
        self.assertEqual(stream(report, "F1")["counted_cyclists"], 10)
        self.assertEqual(stream(report, "F2")["counted_cyclists"], 26)
        self.assertEqual(stream(report, "F1")["candidate_hourly_rate"], 10.0)
        self.assertEqual(stream(report, "F2")["candidate_hourly_rate"], 26.0)
        self.assertEqual(len(report["ambiguous_direction_groups"]), 1)
        self.assertEqual(report["ambiguous_direction_groups"][0]["flow_ids"], ["F1", "F2"])
        self.assertEqual(report["recommended_rate_selection"], "manual_review_required")

    def test_raw_status_always_remains_unverified(self):
        report = analyze_snapshot(build_snapshot(add_second_flow=False))
        self.assertIn("status_requires_source_review", stream(report, "F1")["warnings"])
        self.assertFalse(report["field_validated"])

    def test_duplicate_timestamp_rejects_rate_candidate(self):
        snapshot = build_snapshot(add_second_flow=False)
        snapshot["records"][1]["timestamp"] = snapshot["records"][0]["timestamp"]
        row = stream(analyze_snapshot(snapshot), "F1")
        self.assertIn("duplicate_timestamps", row["warnings"])
        self.assertIsNone(row["candidate_hourly_rate"])

    def test_gap_rejects_rate_candidate(self):
        snapshot = build_snapshot(add_second_flow=False)
        snapshot["records"].pop(1)
        row = stream(analyze_snapshot(snapshot), "F1")
        self.assertIn("missing_intervals", row["warnings"])
        self.assertIsNone(row["candidate_hourly_rate"])

    def test_unknown_granularity_rejects_rate_candidate(self):
        snapshot = build_snapshot(add_second_flow=False)
        for rec in snapshot["records"]:
            rec["granularity"] = "unknown"
        row = stream(analyze_snapshot(snapshot), "F1")
        self.assertIn("unknown_interval", row["warnings"])
        self.assertIsNone(row["candidate_hourly_rate"])

    def test_one_observation_rejects_rate_candidate(self):
        snapshot = build_snapshot(add_second_flow=False)
        snapshot["records"] = snapshot["records"][:1]
        row = stream(analyze_snapshot(snapshot), "F1")
        self.assertIn("insufficient_observations", row["warnings"])
        self.assertIsNone(row["candidate_hourly_rate"])

    def test_rejects_fractional_negative_and_non_numeric_counts(self):
        for invalid in ("-2", "2.5", "not-counts", "NaN"):
            with self.subTest(invalid=invalid):
                data = build_snapshot(add_second_flow=False)
                data["records"][0]["counts"] = invalid
                with self.assertRaisesRegex(ValueError, "counts"):
                    analyze_snapshot(data)

    def test_rejects_missing_fields_and_invalid_timestamps(self):
        data = build_snapshot(add_second_flow=False)
        del data["records"][0]["flowid"]
        with self.assertRaisesRegex(ValueError, "flowid"):
            analyze_snapshot(data)
        data = build_snapshot(add_second_flow=False)
        data["records"][0]["timestamp"] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "timestamp"):
            analyze_snapshot(data)

    def test_counter_replacement_metadata_does_not_pick_a_flow(self):
        report = analyze_snapshot(build_snapshot(), sensor_metadata())
        self.assertEqual(report["hardware_by_sensor"]["demo-sensor"],
                         ["first-hardware", "replacement-hardware"])
        self.assertEqual(report["recommended_rate_selection"], "manual_review_required")

    def test_non_bicycle_mode_is_flagged_not_used_as_candidate(self):
        data = build_snapshot(add_second_flow=False)
        for row in data["records"]:
            row["travelmode"] = "pedestrian"
        observation = stream(analyze_snapshot(data), "F1")
        self.assertIn("non_bicycle_mode", observation["warnings"])
        self.assertIsNone(observation["candidate_hourly_rate"])

    def test_report_records_original_file_hash_and_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, target = root / "counts.json", root / "quality.json"
            source.write_text(json.dumps(build_snapshot()), encoding="utf-8")
            result = write_report(source, target)
            self.assertEqual(result["source_sha256"],
                             hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertTrue(target.is_file())
            command = [sys.executable, "-m", "cyclistics.nyc_data_quality",
                       "--counts", str(source), "--output", str(target)]
            environment = dict(__import__("os").environ)
            environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
            completed = subprocess.run(command, capture_output=True, text=True,
                                       env=environment, timeout=10)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("3 streams", completed.stdout)

    def test_invalid_input_does_not_write_partial_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source, target = folder / "counts.json", folder / "report.json"
            source.write_text('{"records": []}', encoding="utf-8")
            with self.assertRaises(ValueError):
                write_report(source, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
