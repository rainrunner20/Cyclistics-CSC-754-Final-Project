"""Static guardrails for NetLogo controlled experiments; not a NetLogo runtime test."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nlogo"
SOURCE = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nls"


class PairedExperimentStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.model = MODEL.read_text(encoding="utf-8")

    def test_source_matches_embedded_code(self):
        self.assertEqual(self.source, self.model.split("@#$#@#$#@")[0])

    def test_csv_extension_and_export(self):
        self.assertIn("extensions [csv]", self.source)
        self.assertIn('csv:to-file "../outputs/netlogo_paired_results.csv"', self.source)
        self.assertIn('"scenario" "blockage_enabled"', self.source)

    def test_pair_preserves_experiment_inputs(self):
        self.assertIn("let original-arrivals arrival-draws", self.source)
        self.assertIn("let original-speeds speed-draws", self.source)
        self.assertIn("if arrival-draws != original-arrivals", self.source)
        self.assertIn("if speed-draws != original-speeds", self.source)
        self.assertIn("set blockage-enabled 0\n  setup", self.source)
        self.assertIn("set blockage-enabled 1\n  setup", self.source)
        self.assertIn("set blockage-enabled original-blockage", self.source)

    def test_desired_speeds_are_paired_by_admission_order(self):
        self.assertIn("set speed-draws (n-values run-length", self.source)
        self.assertIn("set free-speed (item admitted-count speed-draws)", self.source)
        self.assertIn("set admitted-count admitted-count + 1", self.source)
        self.assertNotIn("set free-speed (0.7 + random-float 0.6)", self.source)

    def test_mean_queue_uses_actual_ticks(self):
        self.assertIn("set queue-area (queue-area + queue-now)", self.source)
        self.assertIn("report (queue-area / ticks)", self.source)

    def test_one_click_interface(self):
        widget_block = self.model.split("@#$#@#$#@")[1]
        self.assertIn("Compare clear vs blocked\nrun-paired-experiment", widget_block)
        self.assertIn("Mean queue (riders)\nmean-queue", widget_block)

    def test_conservation_checks_before_export(self):
        self.assertIn('if not conservation-ok? [ error "Clear-lane conservation failed" ]', self.source)
        self.assertIn('if not conservation-ok? [ error "Blocked-lane conservation failed" ]', self.source)
        self.assertIn('if (item 7 clear-row) != (item 7 blocked-row)', self.source)

    def test_previous_runtime_fixes_preserved(self):
        self.assertIn("foreach (sort-on [(- xcor)] cyclists) [ rider ->", self.source)
        self.assertIn("set waiting? (possible-step <= 0.000000001)", self.source)


if __name__ == "__main__":
    unittest.main()
