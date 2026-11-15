"""TTC and common-crossing-gap *surrogates* from synthetic trajectory fixtures."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cyclistics.v2_conflicts import analyze_trajectories, analyze_csv


def row(t, typ, ident, x, lane, speed, merged):
    return {
        "tick_s": str(t), "type": typ, "agent_id": str(ident),
        "x_patch": str(x), "lane_y": str(lane),
        "desired_speed_patches_per_tick": str(speed), "merged": merged,
    }


FIELDS = ("tick_s", "type", "agent_id", "x_patch", "lane_y",
          "desired_speed_patches_per_tick", "merged")


class ConflictProxyTests(unittest.TestCase):
    def test_ttc_is_only_computed_for_car_behind_merged_bicyclist(self):
        rows = [
            row(0, "car", 1, 0, 2, 2.0, "false"),
            row(0, "cyclist", 2, 2.0, 2, 1.0, "true"),
            row(0, "cyclist", 3, 2.0, 0, 1.0, "false"),
        ]
        result = analyze_trajectories(rows)
        self.assertEqual(result["ttc_proxy_events"], 1)
        self.assertAlmostEqual(result["min_ttc_s"], 0.9)
        self.assertEqual(result["field_validated"], False)
        self.assertEqual(result["crash_probability_estimated"], False)

    def test_no_close_car_returns_null_ttc(self):
        result = analyze_trajectories([
            row(0, "car", 1, 7, 2, 1.2, "false"),
            row(0, "cyclist", 2, 2, 2, 1.0, "true"),
        ])
        self.assertEqual(result["ttc_proxy_events"], 0)
        self.assertIsNone(result["min_ttc_s"])

    def test_shared_x_crossing_gap_is_reported_as_pet_like_not_real_pet(self):
        rows = [
            row(0, "cyclist", 2, 5, 2, 2, "true"),
            row(1, "cyclist", 2, 7, 2, 2, "true"),
            row(0, "car", 1, 4, 2, 4, "false"),
            row(1, "car", 1, 8, 2, 4, "false"),
        ]
        result = analyze_trajectories(rows, crossing_x=6.5)
        self.assertEqual(result["crossing_gap_proxy_events"], 1)
        self.assertAlmostEqual(result["min_crossing_gap_s"], 0.125)
        self.assertEqual(result["crossing_gap_description"], "same-direction passage-time separation, not validated PET")

    def test_bad_kinematics_and_duplicate_identity_are_rejected(self):
        for rows in [
            [row(0, "cyclist", 1, 2, 5, 1, "false")],
            [row(0, "car", 1, 2, 0, 1, "false")],
            [row(0, "car", 1, 2, 2, -1, "false")],
            [row(0, "car", 1, 2, 2, 1, "true")],
            [row(0, "cyclist", 1, 2, 2, 1, "false")],
            [row(0, "car", 1, 2, 2, 1, "false")] * 2,
            [row(0, "car", 1, 2, 2, 1, "false"), row(1, "car", 1, 1, 2, 1, "false")],
        ]:
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    analyze_trajectories(rows)

    def test_archives_actual_csv_hash_and_reproducible_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "traj.csv"
            out = Path(tmp) / "analysis"
            with inp.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows([
                    row(0, "car", 1, 0, 2, 2, "false"),
                    row(0, "cyclist", 2, 2, 2, 1, "true")
                ])
            report = analyze_csv(inp, out)
            self.assertEqual(report["rows"], 2)
            self.assertEqual(report["input_sha256"], hashlib.sha256(inp.read_bytes()).hexdigest())
            self.assertEqual(report["field_validated"], False)
            self.assertIn("summary.json", report["output_sha256"])
            files = {p.name: p.read_bytes() for p in out.iterdir()}
            self.assertEqual(report, analyze_csv(inp, out))
            self.assertEqual(files, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_missing_or_wrong_header_does_not_make_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "missing.csv"
            out = Path(tmp) / "analysis"
            with self.assertRaises(FileNotFoundError):
                analyze_csv(inp, out)
            self.assertFalse(out.exists())
            inp.write_text("not,a,trajectory\n")
            with self.assertRaises(ValueError):
                analyze_csv(inp, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
