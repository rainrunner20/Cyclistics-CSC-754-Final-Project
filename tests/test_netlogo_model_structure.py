"""Static structure checks for NetLogo milestone 3.1A.

These do NOT execute or compile NetLogo. Open the actual model to verify it.
"""
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
MODEL = REPO / "netlogo" / "Cyclistics_Bike_Lane_ABM.nlogo"
CODE = REPO / "netlogo" / "Cyclistics_Bike_Lane_ABM.nls"


class NetLogoModelStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = MODEL.read_text(encoding="utf-8")
        cls.code = CODE.read_text(encoding="utf-8")

    def test_netlogo_sections_present(self):
        self.assertEqual(self.text.count("@#$#@#$#@"), 11)
        self.assertIn("NetLogo 6.3.0", self.text)
        self.assertIn("GRAPHICS-WINDOW", self.text)
        self.assertIn("PLOT", self.text)

    def test_code_reference_matches_embedded_model(self):
        self.assertEqual(self.text.split("@#$#@#$#@")[0], self.code)

    def test_model_entrypoints_and_reporters(self):
        for name in ("setup", "go", "move-cyclist", "update-obstruction",
                     "mean-stop-completed", "conservation-ok?", "run-headless-scenario"):
            self.assertTrue(any(line.startswith("to " + name) or line.startswith("to-report " + name)
                                for line in self.code.splitlines()), name)

    def test_abm_primitives_and_agents_present(self):
        for snippet in ("breed [cyclists cyclist]", "breed [trucks truck]",
                        "ask patches", "ask (sort-on", "create-cyclists 1",
                        "random-seed seed-value", "tick", "min-one-of",
                        "stop-ticks", "pending-arrivals", "arrival-draws"):
            self.assertIn(snippet, self.code)

    def test_interface_exposes_controls(self):
        interface = self.text.split("@#$#@#$#@")[1]
        for control in ("arrival-rate-per-hour", "blockage-enabled", "blockage-start",
                        "blockage-duration", "seed-value", "run-length"):
            self.assertIn(f"\n{control}\n", interface)
        self.assertIn("Conservation check", interface)

    def test_balanced_brackets_in_code(self):
        count = 0
        for char in self.code:
            if char == "[":
                count += 1
            elif char == "]":
                count -= 1
                self.assertGreaterEqual(count, 0)
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
