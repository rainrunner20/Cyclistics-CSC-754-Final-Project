"""Source-level guardrails only; the actual NetLogo GUI must execute the model."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'netlogo/Cyclistics_Bike_Lane_ABM.nls'
MODEL = ROOT / 'netlogo/Cyclistics_Bike_Lane_ABM.nlogo'


class NetLogoVerificationStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = SRC.read_text(encoding='utf-8')
        cls.model = MODEL.read_text(encoding='utf-8')

    def test_source_and_model_are_in_sync(self):
        self.assertEqual(self.code, self.model.split('@#$#@#$#@')[0])
        self.assertEqual(self.model.count('@#$#@#$#@'), 11)

    def test_existing_sensitivity_study_untouched(self):
        self.assertIn('to run-sensitivity-study', self.code)
        self.assertIn('csv:to-file "../outputs/netlogo_sensitivity_raw.csv"', self.code)
        self.assertIn('foreach (sort-on [(- xcor)] cyclists)', self.code)
        self.assertIn('set waiting? (possible-step <= 0.000000001)', self.code)

    def test_each_tick_checks_cyclists_and_obstruction(self):
        self.assertIn('to-report run-checked-scenario [case-label]', self.code)
        self.assertIn('repeat run-length [\n    let instant ticks\n    go', self.code)
        for snippet in ('if not conservation-ok?',
                        'if admitted-count != (departed-count + count cyclists)',
                        'if queue-area != queue-counted',
                        'if obstruction-active? != should-be-blocked?',
                        'if (count trucks) != expected-trucks'):
            self.assertIn(snippet, self.code)

    def test_verification_has_negative_and_replay_controls(self):
        for marker in ('"zero_demand"', '"clear_repeat"', '"zero_duration"',
                       '"blocked"', 'let clear-arrival-draws arrival-draws',
                       'let clear-speed-draws speed-draws',
                       'if (item 15 blocked-row) != 65',
                       'csv:to-file "../outputs/netlogo_verification_checks.csv"'):
            self.assertIn(marker, self.code)

    def test_benchmarks_measure_netlogo_timer_after_setup(self):
        for marker in ('to run-runtime-benchmarks', 'let rates [150 600 900]',
                       'let horizons [600 1200]', 'let blockage-flags [0 1]',
                       'let seeds [201 202 203]',
                       'setup\n          reset-timer\n          repeat run-length [ go ]',
                       'let elapsed-s timer',
                       'csv:to-file "../outputs/netlogo_runtime_benchmarks.csv"'):
            self.assertIn(marker, self.code)

    def test_interface_exposes_both_actions(self):
        interface = self.model.split('@#$#@#$#@')[1]
        self.assertIn('Run verification checks\nrun-verification-suite', interface)
        self.assertIn('Benchmark runtime\nrun-runtime-benchmarks', interface)


if __name__ == '__main__':
    unittest.main()
