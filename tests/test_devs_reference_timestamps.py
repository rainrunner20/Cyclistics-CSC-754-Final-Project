"""Fixed-scenario agreement target for the external DEVS-Suite runner.

This independently runs the Python discrete-event reference; the Java runner
checks its own completion times against the same fixture. This is not broad
statistical validation of either model against observed NYC trajectories.
"""
import unittest
from cyclistics.simulation import Scenario, simulate


class CrossImplementationFixtureTests(unittest.TestCase):
    def test_reference_timestamps_for_coupled_java_scenario(self):
        scenario = Scenario(
            "coupled_java_timestamps",
            blockage_intervals=((12.0, 20.0),),
            horizon_s=30.0,
            service_headway_s=4.0,
            freeflow_travel_s=0.0,
        )
        summary, trace, _ = simulate(scenario, [10.0, 15.0])
        self.assertEqual(
            [(row["time_s"], row["event"]) for row in trace],
            [(10.0, "arrival"), (12.0, "obstruction_start"),
             (14.0, "service_complete"), (15.0, "arrival"),
             (20.0, "obstruction_end"), (24.0, "service_complete")],
        )
        self.assertEqual(summary["completed_all"], 2)
        self.assertEqual(summary["max_waiting_queue"], 1)
        self.assertAlmostEqual(summary["mean_wait_s"], 2.5)


if __name__ == "__main__":
    unittest.main()
