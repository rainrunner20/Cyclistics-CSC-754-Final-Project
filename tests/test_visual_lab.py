"""Contract tests for the Python DES-backed browser event inspector."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cyclistics.visual_lab import SCHEMA, build_visual_lab


class VisualLabTests(unittest.TestCase):
    def test_deterministic_paired_scenarios(self):
        first = build_visual_lab(rate=900, seed=754)
        second = build_visual_lab(rate=900, seed=754)
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], SCHEMA)
        self.assertEqual(first["engine"], "python_des_reference")
        self.assertEqual(len(first["scenarios"]), 3)
        self.assertEqual(first["parameters"]["arrival_source"], "seeded_poisson")
        arrivals = [
            [e["time_s"] for e in case["events"] if e["event"] == "arrival"]
            for case in first["scenarios"]
        ]
        self.assertEqual(arrivals[0], arrivals[1])
        self.assertEqual(arrivals[1], arrivals[2])

    def test_trace_is_real_simulator_output_and_conserved(self):
        from cyclistics.simulation import Scenario, simulate
        fixture = [44.0, 45.0, 46.0, 60.0, 99.0]
        result = build_visual_lab(
            horizon=200, blockage_start=45, blockage_duration=100,
            early_clearance_duration=20, arrivals=fixture,
        )
        blocked = result["scenarios"][1]
        expected_metrics, expected_trace, _ = simulate(
            Scenario("blocked_lane", ((45, 145),), horizon_s=200), fixture
        )
        self.assertEqual(blocked["metrics"], expected_metrics)
        self.assertEqual(
            [(e["time_s"], e["event"], e["queue_waiting"]) for e in blocked["events"]],
            [(e["time_s"], e["event"], e["queue_waiting"]) for e in expected_trace],
        )
        self.assertTrue(all(e["conservation_ok"] for e in blocked["events"]))
        self.assertEqual(
            blocked["events"][-1]["completed_so_far"],
            len(fixture),
        )
        self.assertGreater(
            blocked["metrics"]["mean_wait_s"],
            result["scenarios"][2]["metrics"]["mean_wait_s"],
        )

    def test_priority_when_arrival_and_blockage_start_coincide(self):
        result = build_visual_lab(
            horizon=100, blockage_start=12, blockage_duration=20,
            early_clearance_duration=5, arrivals=[12.0],
        )
        rows = result["scenarios"][1]["events"]
        self.assertEqual([r["event"] for r in rows[:2]],
                         ["obstruction_start", "arrival"])
        self.assertEqual(rows[1]["queue_waiting"], 1)
        self.assertEqual(rows[1]["phase"], "blocked")

    def test_edge_cases_and_validation(self):
        empty = build_visual_lab(rate=0)
        self.assertEqual(empty["parameters"]["arrival_count"], 0)
        for kwargs in (
            {"rate": -1},
            {"rate": float("nan")},
            {"horizon": 0},
            {"blockage_start": 300},
            {"blockage_duration": 300},
            {"early_clearance_duration": 0},
            {"early_clearance_duration": 200},
            {"seed": 7.5},
            {"arrivals": [20, 10]},
            {"arrivals": [float("inf")]},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_visual_lab(**kwargs)

    def test_json_contract_roundtrips_without_nonfinite_numbers(self):
        result = build_visual_lab(rate=300)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "lab.json"
            path.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded, result)
            for scenario in loaded["scenarios"]:
                times = [r["time_s"] for r in scenario["events"]]
                self.assertEqual(times, sorted(times))


if __name__ == "__main__":
    unittest.main()
