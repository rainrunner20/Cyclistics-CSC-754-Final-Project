"""Test only the evidence packer, never represent fixture runtimes as measurements."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

from cyclistics.performance_evidence import build_performance_evidence
from test_netlogo_benchmark_analysis import (
    BENCH_FIELDS, VERIFY_FIELDS, benchmark_fixture, verification_fixture, write_csv,
)


class PerformanceEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.verification = self.root / "verification.csv"
        self.benchmarks = self.root / "benchmarks.csv"
        self.model = self.root / "Cyclistics_Bike_Lane_ABM.nlogo"
        self.model.write_text("SYNTHETIC TEST MODEL ONLY\n", encoding="utf-8")
        self.out = self.root / "performance_evidence"
        self.vrows = verification_fixture()
        self.brows = benchmark_fixture()
        self.save()

    def save(self):
        write_csv(self.verification, VERIFY_FIELDS, self.vrows)
        write_csv(self.benchmarks, BENCH_FIELDS, self.brows)

    def test_exports_expected_tables_figures_and_hash_manifest(self):
        report = build_performance_evidence(
            self.verification, self.benchmarks, self.model, self.out
        )
        self.assertEqual(report["schema"], "cyclistics.performance-evidence.v1")
        self.assertEqual(report["observations"]["verification_cases"], 5)
        self.assertEqual(report["observations"]["benchmark_runs"], 36)
        self.assertEqual(report["observations"]["summary_groups"], 12)
        self.assertFalse(report["field_validated"])
        self.assertFalse(report["cross_model_runtime_comparable"])
        self.assertEqual(report["source_sha256"]["benchmark_csv"],
                         hashlib.sha256(self.benchmarks.read_bytes()).hexdigest())
        self.assertEqual(report["source_sha256"]["model"],
                         hashlib.sha256(self.model.read_bytes()).hexdigest())

        expected = {
            "performance_table.csv", "performance_table.md",
            "netlogo_runtime_600s.svg", "netlogo_runtime_1200s.svg"
        }
        self.assertEqual(set(report["outputs_sha256"]), expected)
        self.assertEqual({p.name for p in self.out.iterdir()},
                         expected | {"performance_manifest.json"})
        for name, digest in report["outputs_sha256"].items():
            self.assertEqual(hashlib.sha256((self.out / name).read_bytes()).hexdigest(),
                             digest)

        with (self.out / "performance_table.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 12)
        self.assertEqual({r["run_length_s"] for r in rows}, {"600", "1200"})
        self.assertEqual({r["replications"] for r in rows}, {"3"})
        for horizon in (600, 1200):
            root = ElementTree.parse(self.out / f"netlogo_runtime_{horizon}s.svg")
            self.assertTrue(root.getroot().tag.endswith("svg"))
        self.assertEqual(json.loads((self.out / "performance_manifest.json").read_text()),
                         report)

    def test_missing_inputs_do_not_make_research_outputs(self):
        self.benchmarks.unlink()
        with self.assertRaisesRegex(ValueError, "Missing NetLogo export"):
            build_performance_evidence(self.verification, self.benchmarks, self.model, self.out)
        self.assertFalse(self.out.exists())

    def test_incomplete_benchmark_grid_is_rejected(self):
        self.brows.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, "Incomplete benchmark grid"):
            build_performance_evidence(self.verification, self.benchmarks, self.model, self.out)
        self.assertFalse(self.out.exists())

    def test_corrupt_runtime_is_rejected(self):
        self.brows[0]["elapsed_real_s"] = "NaN"
        self.save()
        with self.assertRaisesRegex(ValueError, "must be finite"):
            build_performance_evidence(self.verification, self.benchmarks, self.model, self.out)
        self.assertFalse(self.out.exists())

    def test_missing_model_or_verification_failure_is_rejected(self):
        self.model.unlink()
        with self.assertRaises(FileNotFoundError):
            build_performance_evidence(self.verification, self.benchmarks, self.model, self.out)
        self.assertFalse(self.out.exists())
        self.model.write_text("test model again\n")
        self.vrows.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, "exactly 5"):
            build_performance_evidence(self.verification, self.benchmarks, self.model, self.out)
        self.assertFalse(self.out.exists())

    def test_repeat_export_is_byte_identical_and_cautious(self):
        first = build_performance_evidence(
            self.verification, self.benchmarks, self.model, self.out
        )
        files = {p.name: p.read_bytes() for p in self.out.iterdir()}
        second = build_performance_evidence(
            self.verification, self.benchmarks, self.model, self.out
        )
        self.assertEqual(first, second)
        self.assertEqual(files, {p.name: p.read_bytes() for p in self.out.iterdir()})
        md = (self.out / "performance_table.md").read_text()
        self.assertIn("simulated", md.lower())
        self.assertIn("wall-clock", md.lower())
        self.assertIn("not NYC", md)
        self.assertIn("three", md.lower())


if __name__ == "__main__":
    unittest.main()
