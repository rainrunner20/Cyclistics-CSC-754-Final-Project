"""Visual-only NetLogo checks for Cyclistics milestone 3.6.

These inspect source and the saved Interface definition. They do not execute
NetLogo or replace checking the model in the desktop application.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nls"
MODEL = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nlogo"
SECTION = "@#$#@#$#@"


def procedure(code: str, name: str) -> str:
    """Find a top-level procedure so checks don't match unrelated comments."""
    pattern = rf"(?ms)^to(?:-report)?\s+{re.escape(name)}(?:\s+[^\n]*)?\n(.*?)^end\s*$"
    match = re.search(pattern, code)
    if match is None:
        raise AssertionError(f"Missing NetLogo procedure: {name}")
    return match.group(1)


class NetLogoVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.model = MODEL.read_text(encoding="utf-8")
        cls.interface = cls.model.split(SECTION)[1]

    def test_saved_model_and_editable_source_match(self):
        self.assertEqual(self.model.split(SECTION)[0], self.source)

    def test_world_dimensions_remain_single_lane_baseline(self):
        # Surrounding rows can look like roads/sidewalks, but cannot become
        # passable cyclist lanes during this purely visual increment.
        self.assertIn("\n-16\n16\n-4\n4\n", self.interface)
        self.assertIn("setxy min-pxcor 0", procedure(self.source, "admit-pending-cyclist"))
        self.assertIn("xcor > [xcor] of myself", procedure(self.source, "move-cyclist"))
        self.assertNotIn("set ycor", procedure(self.source, "move-cyclist"))

    def test_street_painter_exists_and_setup_calls_it(self):
        setup = procedure(self.source, "setup")
        street = procedure(self.source, "paint-street-background")
        self.assertIn("paint-street-background", setup)
        self.assertIn("ask patches", street)
        self.assertIn("pycor = 0", street)
        self.assertIn("abs pycor = 1", street)
        self.assertIn("bike-lane-color", street)
        self.assertLess(setup.index("paint-street-background"), setup.index("set arrival-draws"))

    def test_green_bike_lane_has_a_single_color_definition(self):
        # Shared color helper prevents a truck clearing back to the old blue.
        color = procedure(self.source, "bike-lane-color")
        self.assertRegex(color, r"\breport\s+(?:\(?\s*)?green\b")
        street = procedure(self.source, "paint-street-background")
        update = procedure(self.source, "update-obstruction")
        self.assertIn("set pcolor bike-lane-color", street)
        self.assertIn("set pcolor bike-lane-color", update)
        self.assertNotIn("set pcolor sky", update)

    def test_obstruction_remains_at_original_location_and_schedule(self):
        update = procedure(self.source, "update-obstruction")
        self.assertIn("ticks >= blockage-start", update)
        self.assertIn("ticks < (blockage-start + blockage-duration)", update)
        self.assertEqual(update.count("pxcor >= 6 and pxcor <= 7"), 2)
        self.assertIn("set pcolor orange", update)
        self.assertIn("setxy 6.5 0", update)

    def test_interface_explains_agent_colors_and_keeps_existing_plot(self):
        self.assertIn("TEXTBOX", self.interface)
        for label in ("Moving (blue)", "Stopped (yellow)",
                      "Truck (red)", "Blocked zone (orange)"):
            self.assertIn(label, self.interface)
        self.assertIn("Queue length over time", self.interface)
        self.assertIn('"plot queue-now"', self.interface)

    def test_experiment_controls_and_sampling_remain_available(self):
        self.assertIn("set arrival-draws (n-values run-length", self.source)
        self.assertIn("set speed-draws (n-values run-length", self.source)
        self.assertIn("run-paired-experiment", self.interface)
        self.assertIn("run-sensitivity-study", self.interface)
        self.assertIn("run-verification-suite", self.interface)
        self.assertIn("run-runtime-benchmarks", self.interface)
        self.assertIn('csv:to-file "../outputs/netlogo_paired_results.csv"', self.source)


if __name__ == "__main__":
    unittest.main()
