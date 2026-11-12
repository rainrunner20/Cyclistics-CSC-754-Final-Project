"""Checks for the NYC counts-to-arrival-rate pipeline (no live API needed)."""
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics.nyc_calibration import (
    SCHEMA, build_window_url, calibrate, fetch_window, inspect_counts, load_calibration,
)
from cyclistics.simulation import main as simulation_main


def row(ts: str, count: str = "25", **changes) -> dict:
    base = {
        "sensor_id": "S1", "travelmode": "Bicycle", "granularity": "Hour",
        "direction": "Total", "flowid": "F1", "status": "1",
        "timestamp": ts, "counts": count,
    }
    return dict(base, **changes)


def snapshot(rows: list[dict]) -> dict:
    return {"source": "test fixture", "dataset": "counts", "dataset_id": "ct66-47at",
            "records": rows}


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row("2026-10-15T08:00:00", "100"), row("2026-10-15T09:00:00", "200")]

    def fit(self, rows=None, **overrides):
        opts = dict(sensor_id="S1", mode="Bicycle", granularity="Hour", interval_minutes=60)
        opts.update(overrides)
        return calibrate(snapshot(self.rows if rows is None else rows), **opts)

    def test_hourly_rate_uses_all_observed_hours(self):
        fitted = self.fit()
        self.assertEqual(fitted["schema"], SCHEMA)
        self.assertEqual(fitted["observations"], 2)
        self.assertEqual(fitted["counted_cyclists"], 300)
        self.assertEqual(fitted["observed_hours_assumed"], 2)
        self.assertEqual(fitted["arrival_rate_per_hour"], 150)

    def test_15_minute_rate_scaling(self):
        rows = [row("2026-10-15T08:00:00", "30", granularity="15min"),
                row("2026-10-15T08:15:00", "45", granularity="15min")]
        fitted = self.fit(rows, granularity="15min", interval_minutes=15)
        self.assertEqual(fitted["arrival_rate_per_hour"], 150)
        self.assertEqual(fitted["observed_hours_assumed"], 0.5)

    def test_duplicate_timestamps_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.fit([self.rows[0], self.rows[0]])

    def test_gapped_rows_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing/overlapping"):
            self.fit([self.rows[0], row("2026-10-15T11:00:00")])

    def test_multiple_flows_cannot_be_added_together(self):
        rows = self.rows + [row("2026-10-15T08:00:00", flowid="F2")]
        with self.assertRaisesRegex(ValueError, "Multiple direction/flow/status"):
            self.fit(rows)
        fitted = self.fit(rows, flow_id="F1")
        self.assertEqual(fitted["observations"], 2)

    def test_mixed_statuses_rejected(self):
        rows = [self.rows[0], row("2026-10-15T09:00:00", status="99")]
        with self.assertRaisesRegex(ValueError, "Multiple direction/flow/status"):
            self.fit(rows)

    def test_non_bicycle_counts_not_included(self):
        rows = self.rows + [row("2026-10-15T08:00:00", "500", travelmode="Pedestrian")]
        self.assertEqual(self.fit(rows)["counted_cyclists"], 300)

    def test_insufficient_data_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            self.fit([self.rows[0]])

    def test_bad_interval_and_fractional_counts_rejected(self):
        for duration in (0, -15, math.inf, math.nan):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                self.fit(interval_minutes=duration)
        with self.assertRaisesRegex(ValueError, "whole numbers"):
            self.fit([self.rows[0], row("2026-10-15T09:00:00", "12.5")])

    def test_inspect_shows_separate_streams(self):
        rows = self.rows + [row("2026-10-15T08:00:00", flowid="F2")]
        groups = inspect_counts(snapshot(rows))
        self.assertEqual([count for _, count in groups], [2, 1])

    def test_query_encodes_sensor_id_as_a_safe_literal(self):
        url = build_window_url("O'Brien", "2026-10-15T08:00:00", "2026-10-15T10:00:00", 30, 0)
        query = parse_qs(urlsplit(url).query)
        self.assertIn("O''Brien", query["$where"][0])
        self.assertEqual(query["$limit"], ["30"])
        self.assertIn("timestamp ASC", query["$order"][0])

    def test_invalid_query_period_rejected(self):
        with self.assertRaisesRegex(ValueError, "earlier"):
            build_window_url("S1", "2026-10-15T10:00:00", "2026-10-15T09:00:00", 1, 0)
        with self.assertRaisesRegex(ValueError, "timezone-free"):
            build_window_url("S1", "2026-10-15T08:00:00+00:00", "2026-10-15T10:00:00", 1, 0)

    def test_fetch_paginates_until_short_page(self):
        side_effect = [self.rows, [row("2026-10-15T10:00:00")]]
        with patch("cyclistics.nyc_calibration.request_json", side_effect=side_effect) as mocked:
            fetched = fetch_window("S1", "2026-10-15T08:00:00", "2026-10-15T12:00:00", page_size=2)
        self.assertEqual(fetched["record_count"], 3)
        self.assertEqual(mocked.call_count, 2)

    def test_fetch_refuses_truncated_data(self):
        with patch("cyclistics.nyc_calibration.request_json", side_effect=[self.rows, [row("2026-10-15T10:00:00")]]):
            with self.assertRaisesRegex(ValueError, "exceeds"):
                fetch_window("S1", "2026-10-15T08:00:00", "2026-10-15T12:00:00", max_records=2, page_size=2)

    def test_calibration_rate_file_rejects_invalid_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rate.json"
            path.write_text(json.dumps({"schema": "wrong", "arrival_rate_per_hour": 100}))
            with self.assertRaisesRegex(ValueError, "Expected"):
                load_calibration(path)
            path.write_text(json.dumps({"schema": SCHEMA, "arrival_rate_per_hour": -10}))
            with self.assertRaisesRegex(ValueError, "invalid"):
                load_calibration(path)

    def test_simulation_accepts_calibration_and_saves_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "calibration.json"
            path.write_text(json.dumps(self.fit()))
            out = Path(folder) / "outputs"
            arguments = ["cyclistics", "--calibration", str(path), "--output-dir", str(out)]
            with patch.object(sys, "argv", arguments):
                simulation_main()
            meta = json.loads((out / "simulation_inputs.json").read_text())
            self.assertEqual(meta["input_type"], "data_informed_poisson_rate")
            self.assertEqual(meta["arrival_rate_per_hour"], 150)
            self.assertTrue((out / "scenario_metrics.csv").is_file())

    def test_checked_in_synthetic_fixture_is_not_misrepresented_as_nyc_data(self):
        fixture = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "synthetic_hourly_counts.json"
        data = json.loads(fixture.read_text())
        fit = calibrate(data, sensor_id="demo-sensor", mode="Bicycle",
                        granularity="Hour", interval_minutes=60)
        self.assertEqual(fit["arrival_rate_per_hour"], 300)
        self.assertIn("Synthetic", fit["source"])


if __name__ == "__main__":
    unittest.main()
