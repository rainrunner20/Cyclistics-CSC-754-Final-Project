"""Tests that a demo cannot silently turn detections into observed blockages."""
import copy
import tempfile
import unittest
from pathlib import Path

from cyclistics.v2_demo import build_demo


def synthetic():
    return {
        "schema": "cyclistics.observation.v1",
        "observation_id": "fake-frame",
        "source": "synthetic_fixture",
        "observed_at_utc": "2026-11-14T16:30:00Z",
        "object_class": "truck",
        "confidence": 0.8,
        "bbox_norm_xyxy": [0.1, 0.2, 0.6, 0.7],
        "lane_overlap": True,
        "segment_id": "model-segment",
    }


class V2DemoTests(unittest.TestCase):
    def test_requires_explicit_fixture_approval(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "acknowledgement"):
                build_demo(synthetic(), Path(root) / "output", approved=False)
            self.assertFalse((Path(root) / "output").exists())

    def test_actual_provider_observation_is_rejected_by_fixture_demo(self):
        with tempfile.TemporaryDirectory() as root:
            record = synthetic()
            record["source"] = "roboflow"
            with self.assertRaisesRegex(ValueError, "synthetic"):
                build_demo(record, Path(root) / "output", approved=True)

    def test_exports_pair_with_real_provenance_flags(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "output"
            summary = build_demo(synthetic(), path, approved=True)
            self.assertEqual(summary["event_count"], 2)
            self.assertEqual(summary["scenario_id"], "v2-synthetic-replay")
            self.assertFalse(summary["field_validated"])
            csv_text = (path / "netlogo_obstruction_events.csv").read_text()
            self.assertIn("12,obstruction_start", csv_text)
            self.assertIn("20,obstruction_end", csv_text)

    def test_unreviewed_observation_cannot_be_used(self):
        with tempfile.TemporaryDirectory() as root:
            record = synthetic()
            record["lane_overlap"] = None
            with self.assertRaisesRegex(ValueError, "review"):
                build_demo(record, Path(root) / "output", approved=True)


if __name__ == "__main__":
    unittest.main()
