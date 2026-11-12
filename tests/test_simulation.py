import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics import Scenario, sample_arrivals, simulate


class ReferenceModelTests(unittest.TestCase):
    def test_seeded_arrivals_are_repeatable(self):
        self.assertEqual(sample_arrivals(300, 1800, 754), sample_arrivals(300, 1800, 754))

    def test_no_arrivals_is_valid(self):
        metrics, _, _ = simulate(Scenario("empty"), [])
        self.assertEqual(metrics['mean_wait_s'], 0)
        self.assertEqual(metrics['completed_all'], 0)

    def test_blockage_increases_delay(self):
        arrivals = [301.0, 312.0, 330.0, 350.0, 390.0]
        base, _, _ = simulate(Scenario("clear"), arrivals)
        blocked, _, _ = simulate(Scenario("blocked", ((300, 600),)), arrivals)
        self.assertEqual(blocked['completed_all'], len(arrivals))
        self.assertGreater(blocked['mean_wait_s'], base['mean_wait_s'])

    def test_earlier_clearance_reduces_delay(self):
        arrivals = [301.0, 312.0, 330.0, 350.0, 390.0]
        long, _, _ = simulate(Scenario("long", ((300, 600),)), arrivals)
        short, _, _ = simulate(Scenario("short", ((300, 360),)), arrivals)
        self.assertGreater(long['mean_wait_s'], short['mean_wait_s'])

    def test_simultaneous_arrival_and_blockage_start(self):
        metrics, trace, _ = simulate(Scenario("edge", ((300, 310),)), [300.0])
        self.assertGreater(metrics['mean_wait_s'], 0)
        self.assertEqual(trace[0]['event'], 'obstruction_start')

    def test_invalid_overlapping_windows_rejected(self):
        with self.assertRaises(ValueError):
            Scenario('bad', ((300, 400), (350, 500)))

    def test_busy_service_finishes_before_new_passage_is_stopped(self):
        m, _, _ = simulate(Scenario('x', ((302, 320),), service_headway_s=3), [300, 301])
        self.assertEqual(m['completed_all'], 2)
        self.assertGreater(m['mean_wait_s'], 0)

# Extra verification checks for reproducible research and input robustness.
class SimulationRobustnessTests(unittest.TestCase):
    def test_rejects_non_finite_parameters(self):
        from cyclistics import run_suite
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=str(invalid)):
                with self.assertRaises(ValueError):
                    sample_arrivals(invalid, 1800, 754)
                with self.assertRaises(ValueError):
                    Scenario("invalid", horizon_s=invalid)
                with self.assertRaises(ValueError):
                    simulate(Scenario("valid"), [invalid])
        with self.assertRaises(ValueError):
            run_suite(Path("outputs"), horizon_s=float("nan"))

    def test_arrivals_out_of_order_rejected(self):
        with self.assertRaises(ValueError):
            simulate(Scenario("order"), [6.0, 2.0])

    def test_conserves_cyclists(self):
        arrivals = [10.0, 11.0, 12.0, 500.0, 1799.0]
        metrics, trace, _ = simulate(Scenario("check", ((300, 600),)), arrivals)
        self.assertEqual(metrics["arrivals"], metrics["completed_all"])
        self.assertEqual(sum(x["event"] == "service_complete" for x in trace), len(arrivals))
        self.assertTrue(all(x["queue_waiting"] >= 0 for x in trace))

    def test_default_suite_writes_csv(self):
        import tempfile
        from cyclistics import run_suite
        with tempfile.TemporaryDirectory() as temporary:
            results = run_suite(Path(temporary), seed=754)
            self.assertEqual(len(results), 4)
            self.assertTrue((Path(temporary) / "scenario_metrics.csv").is_file())
            self.assertTrue((Path(temporary) / "netlogo_events_clear_lane.csv").is_file())

    def test_suite_requires_sufficient_horizon_for_default_scenarios(self):
        from cyclistics import run_suite
        with self.assertRaisesRegex(ValueError, "horizon >= 870"):
            run_suite(Path("outputs"), horizon_s=600)


if __name__ == "__main__":
    unittest.main()
