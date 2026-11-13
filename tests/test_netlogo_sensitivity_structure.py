"""Structural guardrails only: these do NOT execute NetLogo itself."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nls"
MODEL = ROOT / "netlogo" / "Cyclistics_Bike_Lane_ABM.nlogo"


class SensitivityStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.model = MODEL.read_text(encoding="utf-8")

    def test_embedded_source_remains_exact(self):
        self.assertEqual(self.model.split("@#$#@#$#@")[0], self.source)
        self.assertEqual(self.model.count("@#$#@#$#@"), 11)

    def test_one_click_interface_procedure(self):
        self.assertIn("\nBUTTON\n10\n447\n242\n481\nRun sensitivity study\nrun-sensitivity-study", self.model)
        self.assertIn("to run-sensitivity-study", self.source)

    def test_exact_four_by_four_by_ten_design(self):
        self.assertIn("let rates [150 300 600 900]", self.source)
        self.assertIn("let durations [0 30 60 120]", self.source)
        self.assertIn("let seeds [101 102 103 104 105 106 107 108 109 110]", self.source)
        self.assertIn("set run-length 600", self.source)
        self.assertIn("set blockage-start 45", self.source)
        self.assertIn("arrival-rate-per-hour\narrival-rate-per-hour\n0\n1800\n600.0\n30", self.model)

    def test_no_blockage_baseline_reused_per_rate_seed(self):
        self.assertLess(self.source.index("let base-arrivals arrival-draws"),
                        self.source.index("foreach durations [ duration ->"))
        self.assertIn("set blockage-enabled 0\n      set blockage-duration 0\n      setup", self.source)
        self.assertIn("set blockage-enabled (ifelse-value (duration = 0) [0] [1])", self.source)

    def test_controlled_draws_and_invariants(self):
        for phrase in ("if arrival-draws != base-arrivals", "if speed-draws != base-speeds",
                       "if requested-arrivals != base-requested", "if not conservation-ok?",
                       "if duration = 0 [", "Zero-duration control differs from its baseline"):
            self.assertIn(phrase, self.source)

    def test_restores_all_user_controls(self):
        for name in ("arrival-rate-per-hour", "blockage-enabled", "blockage-start",
                     "blockage-duration", "seed-value", "run-length"):
            self.assertIn("set " + name + " original-", self.source)
        self.assertIn("no-display", self.source)
        self.assertIn("  setup\n  display", self.source)

    def test_exports_unrounded_pair_deltas(self):
        self.assertIn('csv:to-file "../outputs/netlogo_sensitivity_raw.csv"', self.source)
        self.assertIn("(fput columns rows)", self.source)
        self.assertIn("(treatment-mean-queue - base-mean-queue)", self.source)
        self.assertIn("(departed-count - base-departed)", self.source)
        self.assertIn('"paired_inputs_ok"', self.source)

    def test_original_ABM_fixes_preserved(self):
        self.assertIn("foreach (sort-on [(- xcor)] cyclists) [ rider ->", self.source)
        self.assertIn("set waiting? (possible-step <= 0.000000001)", self.source)
        self.assertIn("to run-paired-experiment", self.source)
        self.assertIn("if speed-draws != original-speeds", self.source)


if __name__ == "__main__":
    unittest.main()
