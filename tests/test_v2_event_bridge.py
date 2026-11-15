"""Tests for the v2 deterministic obstruction-event log and NetLogo replay export."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cyclistics.v2_event_bridge import (
    EVENT_SCHEMA,
    build_replay_package,
    event_from_reviewed_observation,
    validate_events,
)


def event(ident="truck-start", tick=12, kind="obstruction_start"):
    return {
        "schema": EVENT_SCHEMA,
        "event_id": ident,
        "scenario_id": "replay-test",
        "source": "synthetic_fixture",
        "source_observation_id": None,
        "simulated_time_s": tick,
        "event_type": kind,
        "segment_id": "demo-lane",
    }


class V2EventBridgeTests(unittest.TestCase):
    def test_out_of_order_replay_becomes_stable_and_deduplicated(self):
        rows = [event("end", 20, "obstruction_end"), event(), event()]
        actual = validate_events(rows)
        self.assertEqual([e["event_id"] for e in actual], ["truck-start", "end"])
        self.assertEqual([e["simulated_time_s"] for e in actual], [12, 20])

    def test_conflicting_duplicate_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            validate_events([event(), event("truck-start", 13)])

    def test_reject_mixed_scenarios_and_unpaired_events(self):
        changed = event("end", 20, "obstruction_end")
        changed["scenario_id"] = "other"
        with self.assertRaisesRegex(ValueError, "Single scenario"):
            validate_events([event(), changed])
        with self.assertRaisesRegex(ValueError, "Unmatched"):
            validate_events([event("end", 20, "obstruction_end")])
        with self.assertRaisesRegex(ValueError, "Unclosed"):
            validate_events([event()])
        with self.assertRaisesRegex(ValueError, "end must follow"):
            validate_events([event(), event("end", 12, "obstruction_end")])

    def test_reject_noninteger_seconds_unsupported_sources_and_fields(self):
        for key, value in [
            ("simulated_time_s", -1),
            ("simulated_time_s", 3.4),
            ("simulated_time_s", float("nan")),
            ("simulated_time_s", True),
            ("event_type", "collision"),
            ("source", "unknown_opaque"),
            ("segment_id", "  "),
        ]:
            with self.subTest(key=key, value=value):
                altered = event()
                altered[key] = value
                with self.assertRaises(ValueError):
                    validate_events([altered])
        altered = event()
        altered["raw_video"] = "private"
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            validate_events([altered])

    def test_explicitly_reviewed_camera_observation_required(self):
        candidate = {
            "schema": "cyclistics.observation.v1",
            "observation_id": "frame-1",
            "source": "roboflow",
            "observed_at_utc": "2026-11-14T16:30:00Z",
            "object_class": "truck",
            "confidence": 0.95,
            "bbox_norm_xyxy": [0.1, 0.2, 0.5, 0.7],
            "lane_overlap": None,
            "segment_id": "known-lane",
        }
        with self.assertRaisesRegex(ValueError, "review"):
            event_from_reviewed_observation(candidate, approved=True, start_tick=12,
                                            duration_s=8, scenario_id="reviewed")
        candidate["lane_overlap"] = True
        with self.assertRaisesRegex(ValueError, "approval"):
            event_from_reviewed_observation(candidate, approved=False, start_tick=12,
                                            duration_s=8, scenario_id="reviewed")
        start, end = event_from_reviewed_observation(
            candidate, approved=True, start_tick=12, duration_s=8, scenario_id="reviewed")
        self.assertEqual((start["simulated_time_s"], end["simulated_time_s"]), (12, 20))
        self.assertEqual(start["source_observation_id"], "frame-1")
        self.assertEqual(len(validate_events([end, start])), 2)

    def test_archived_replay_csv_and_hashes_are_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "replay"
            first = build_replay_package(
                [event("end", 20, "obstruction_end"), event(), event()], output)
            self.assertEqual(first["event_count"], 2)
            self.assertFalse(first["field_validated"])
            self.assertFalse(first["live_coupled"])
            self.assertEqual(first["scenario_id"], "replay-test")
            with (output / "netlogo_obstruction_events.csv").open(
                    newline="", encoding="utf-8") as handle:
                csvrows = list(csv.DictReader(handle))
            self.assertEqual([(r["time_s"], r["event_type"]) for r in csvrows],
                             [("12", "obstruction_start"), ("20", "obstruction_end")])
            self.assertEqual(
                hashlib.sha256((output / "netlogo_obstruction_events.csv").read_bytes()).hexdigest(),
                first["output_sha256"]["netlogo_obstruction_events.csv"],
            )
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            second = build_replay_package([event(), event("end", 20, "obstruction_end")], output)
            self.assertEqual(first, second)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(json.loads((output / "replay_manifest.json").read_text()),
                             first)

    def test_invalid_inputs_create_no_evidence_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad"
            with self.assertRaises(ValueError):
                build_replay_package([event()], path)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
