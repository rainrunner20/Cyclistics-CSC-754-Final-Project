"""Regression tests for the NYC-demand to NetLogo input bridge (no live API)."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics.netlogo_calibration_bridge import (  # noqa: E402
    RATE_CSV, MANIFEST, INSTRUCTIONS, PAIR_REPORT, prepare, verify_pair,
)


def calibration(*, synthetic=False, rate=300):
    return {
        "schema": "cyclistics.arrival-rate.v1",
        "created_at_utc": "2026-11-12T22:00:00+00:00",
        "source": ("Synthetic training fixture (not NYC sensor measurements)" if synthetic
                   else "NYC Open Data / NYC Department of Transportation"),
        "dataset_id": "ct66-47at", "sensor_id": "EXAMPLE-SENSOR", "travelmode": "Bicycle",
        "granularity": "Hour", "direction": "Total", "flowid": "one", "status": "1",
        "observations": 4, "counted_cyclists": int(rate) * 4,
        "observed_hours_assumed": 4, "interval_minutes_assumed": 60,
        "arrival_rate_per_hour": rate,
        "source_sha256": "a" * 64 if not synthetic else None,
        "source_retrieved_at_utc": "2026-11-12T22:00:00+00:00" if not synthetic else None,
    }


FIELDS = ["scenario", "blockage_enabled", "seed", "arrival_rate_per_hour",
          "blockage_start_s", "blockage_duration_s", "run_length_s",
          "requested", "departed", "on_lane", "pending", "peak_queue",
          "mean_queue", "mean_stop_completed_s", "conservation_ok"]


def pair():
    return [
        ["clear", 0, 754, 300, 45, 65, 600, 50, 45, 5, 0, 1, 0.02, 0, "true"],
        ["blocked", 1, 754, 300, 45, 65, 600, 50, 43, 7, 0, 8, 0.5, 3, "true"],
    ]


class NetLogoCalibrationBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.input = self.dir / "calibration.json"
        self.paired = self.dir / "paired.csv"
        self.output = self.dir / "output"
        self.save()
        self.save_pair()

    def save(self, data=None):
        self.input.write_text(json.dumps(calibration() if data is None else data), encoding="utf-8")

    def save_pair(self, values=None):
        with self.paired.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(FIELDS)
            writer.writerows(pair() if values is None else values)

    def test_prepare_writes_numeric_csv_provenance_and_commands(self):
        p = prepare(self.input, self.output)
        self.assertEqual(p["arrival_rate_per_hour"], 300)
        self.assertEqual((self.output / RATE_CSV).read_text(), "300.000000\n")
        self.assertIn('csv:from-file "../outputs/netlogo_arrival_rate.csv"',
                      (self.output / INSTRUCTIONS).read_text())
        meta = json.loads((self.output / MANIFEST).read_text())
        self.assertEqual(meta["data_origin"], "calibration_from_NYC_count_snapshot")
        self.assertEqual(len(meta["calibration_file_sha256"]), 64)

    def test_pair_validates_and_writes_provenance_report(self):
        result = verify_pair(self.input, self.paired, self.output)
        self.assertEqual(result["blocked_minus_clear"]["peak_queue"], 7)
        self.assertAlmostEqual(result["blocked_minus_clear"]["mean_queue"], 0.48)
        self.assertEqual(json.loads((self.output / PAIR_REPORT).read_text())["scenario_seed"], 754)

    def test_rejects_synthetic_without_explicit_permission(self):
        self.save(calibration(synthetic=True))
        with self.assertRaisesRegex(ValueError, "Synthetic demonstration"):
            prepare(self.input, self.output)

    def test_allows_labeled_synthetic_smoke_test(self):
        self.save(calibration(synthetic=True))
        result = prepare(self.input, self.output, allow_synthetic=True)
        self.assertEqual(result["data_origin"], "synthetic_fixture")
        verified = verify_pair(self.input, self.paired, self.output, allow_synthetic=True)
        self.assertEqual(verified["provenance"]["data_origin"], "synthetic_fixture")

    def test_rejects_wrong_dataset(self):
        c = calibration(); c["dataset_id"] = "wrong"; self.save(c)
        with self.assertRaisesRegex(ValueError, "dataset ID"):
            prepare(self.input, self.output)

    def test_rejects_pedestrians(self):
        c = calibration(); c["travelmode"] = "Pedestrian"; self.save(c)
        with self.assertRaisesRegex(ValueError, "bicycle"):
            prepare(self.input, self.output)

    def test_rejects_out_of_slider_range_instead_of_clipping(self):
        self.save(calibration(rate=1900))
        with self.assertRaisesRegex(ValueError, "slider maximum"):
            prepare(self.input, self.output)

    def test_rejects_wrong_rate_arithmetic(self):
        c = calibration(); c["counted_cyclists"] = 100; self.save(c)
        with self.assertRaisesRegex(ValueError, "disagrees"):
            prepare(self.input, self.output)

    def test_rejects_missing_real_source_digest(self):
        c = calibration(); c["source_sha256"] = None; self.save(c)
        with self.assertRaisesRegex(ValueError, "snapshot SHA256"):
            prepare(self.input, self.output)

    def test_rejects_paired_csv_using_wrong_rate(self):
        r = pair(); r[1][3] = 600; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "did not use"):
            verify_pair(self.input, self.paired, self.output)

    def test_rejects_paired_demand_mismatch(self):
        r = pair(); r[1][7] = 51; r[1][9] = 8; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "requested"):
            verify_pair(self.input, self.paired, self.output)

    def test_rejects_paired_seed_mismatch(self):
        r = pair(); r[1][2] = 12; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "seed"):
            verify_pair(self.input, self.paired, self.output)

    def test_rejects_conservation_mismatch(self):
        r = pair(); r[1][9] = 9; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "conservation"):
            verify_pair(self.input, self.paired, self.output)

    def test_rejects_duplicate_scenarios(self):
        r = pair(); r[1][0] = "clear"; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "one clear and one blocked"):
            verify_pair(self.input, self.paired, self.output)

    def test_rejects_non_finite_means(self):
        r = pair(); r[1][12] = "nan"; self.save_pair(r)
        with self.assertRaisesRegex(ValueError, "Non-finite"):
            verify_pair(self.input, self.paired, self.output)


if __name__ == "__main__":
    unittest.main()
