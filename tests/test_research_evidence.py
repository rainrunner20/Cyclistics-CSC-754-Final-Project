"""Evidence-packaging contract. Fixture numbers are synthetic test data.

Only a NetLogo desktop export may be used for actual project results.
"""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cyclistics.research_evidence import build_evidence
from test_netlogo_sensitivity_analysis import sample_records, write_fixture


class ResearchEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / "netlogo_sensitivity_raw.csv"
        self.model = self.root / "Cyclistics_Bike_Lane_ABM.nlogo"
        self.model.write_text("test fixture model, not a real NetLogo run\n", encoding="utf-8")
        self.results = self.root / "research"
        self.records = sample_records()
        write_fixture(self.raw, self.records)

    def test_real_input_contract_creates_table_figures_and_manifest(self):
        manifest = build_evidence(self.raw, self.model, self.results)
        self.assertEqual(manifest["schema"], "cyclistics.research-evidence.v1")
        self.assertEqual(manifest["observations"]["paired_rows"], 160)
        self.assertEqual(manifest["observations"]["summary_rows"], 16)
        self.assertFalse(manifest["field_validated"])
        self.assertEqual(manifest["source"]["raw_sha256"],
                         hashlib.sha256(self.raw.read_bytes()).hexdigest())
        self.assertEqual(manifest["source"]["model_sha256"],
                         hashlib.sha256(self.model.read_bytes()).hexdigest())
        expected = {
            "paper_sensitivity_table.csv", "paper_sensitivity_table.md",
            "netlogo_delta_mean_queue.svg", "netlogo_delta_peak_queue.svg",
        }
        self.assertEqual(set(manifest["outputs_sha256"]), expected)
        for name, digest in manifest["outputs_sha256"].items():
            self.assertEqual(hashlib.sha256((self.results / name).read_bytes()).hexdigest(), digest)
        self.assertEqual(set(p.name for p in self.results.iterdir()),
                         expected | {"evidence_manifest.json"})
        with (self.results / "paper_sensitivity_table.csv").open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 16)
        selected = next(r for r in rows if r["arrival_rate_per_hour"] == "600"
                        and r["blockage_duration_s"] == "60")
        self.assertAlmostEqual(float(selected["avg_delta_peak_queue"]), 4.5)
        self.assertEqual(selected["replications"], "10")

    def test_missing_raw_csv_never_generates_research_outputs(self):
        self.raw.unlink()
        with self.assertRaises(FileNotFoundError):
            build_evidence(self.raw, self.model, self.results)
        self.assertFalse(self.results.exists())

    def test_corrupt_or_incomplete_experiment_is_rejected(self):
        write_fixture(self.raw, self.records[:-1])
        with self.assertRaisesRegex(ValueError, "Incomplete sensitivity grid"):
            build_evidence(self.raw, self.model, self.results)
        self.assertFalse(self.results.exists())

    def test_missing_model_blocks_untraceable_figures(self):
        self.model.unlink()
        with self.assertRaises(FileNotFoundError):
            build_evidence(self.raw, self.model, self.results)
        self.assertFalse(self.results.exists())

    def test_markdown_does_not_claim_real_world_accuracy(self):
        build_evidence(self.raw, self.model, self.results)
        table = (self.results / "paper_sensitivity_table.md").read_text(encoding="utf-8")
        self.assertIn("synthetic", table.lower())
        self.assertIn("not measured NYC", table)
        self.assertIn("completed-rider", table)
        self.assertIn("95%", table)
        self.assertEqual(table.count("\n| 600 |"), 4)

    def test_same_input_reproduces_identical_outputs(self):
        first = build_evidence(self.raw, self.model, self.results)
        copied = {p.name: p.read_bytes() for p in self.results.iterdir()}
        second = build_evidence(self.raw, self.model, self.results)
        self.assertEqual(first, second)
        self.assertEqual(copied, {p.name: p.read_bytes() for p in self.results.iterdir()})


if __name__ == "__main__":
    unittest.main()
