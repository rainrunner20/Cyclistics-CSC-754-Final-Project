"""Tests for the optional computer-vision observation boundary.

These payloads are invented software fixtures, never real camera detections.
"""
import unittest

from cyclistics.observation_contract import (
    OBSERVATION_SCHEMA,
    validate_observation,
)


def candidate():
    return {
        "schema": OBSERVATION_SCHEMA,
        "observation_id": "sample-frame-0001",
        "source": "synthetic_fixture",
        "observed_at_utc": "2026-11-14T16:30:00Z",
        "object_class": "truck",
        "confidence": 0.87,
        "bbox_norm_xyxy": [0.2, 0.1, 0.7, 0.8],
        "lane_overlap": None,
        "segment_id": None,
    }


class ObservationContractTests(unittest.TestCase):
    def test_valid_candidate_is_normalized_without_claiming_a_blockage(self):
        record = validate_observation(candidate())
        self.assertEqual(record["schema"], OBSERVATION_SCHEMA)
        self.assertEqual(record["source"], "synthetic_fixture")
        self.assertIsNone(record["lane_overlap"])
        self.assertEqual(record["confidence"], 0.87)
        self.assertNotIn("simulation_time_s", record)
        self.assertNotIn("confirmed_blockage", record)

    def test_optional_reviewed_segment_and_bbox(self):
        row = candidate()
        row.update(source="manual_review", segment_id="user-supplied-segment",
                   lane_overlap=True)
        actual = validate_observation(row)
        self.assertTrue(actual["lane_overlap"])
        self.assertEqual(actual["segment_id"], "user-supplied-segment")

    def test_rejects_unrecognized_schema_and_unsafe_extra_data(self):
        for field, value in (
            ("schema", "unversioned"),
            ("observed_at_utc", "tomorrow"),
            ("observed_at_utc", "2026-11-14T16:30:00"),
            ("observed_at_utc", "2026-11-14T11:30:00-05:00"),
            ("source", "some_unknown_camera"),
            ("object_class", ""),
            ("observation_id", " "),
            ("segment_id", 42),
            ("lane_overlap", 1),
        ):
            with self.subTest(field=field, value=value):
                row = candidate()
                row[field] = value
                with self.assertRaises(ValueError):
                    validate_observation(row)
        row = candidate()
        row["raw_image_b64"] = "not allowed"
        with self.assertRaisesRegex(ValueError, "Unexpected fields"):
            validate_observation(row)

    def test_rejects_confidence_out_of_range_nonfinite_or_boolean(self):
        for value in (-0.01, 1.01, float("nan"), float("inf"), True, "0.9"):
            with self.subTest(value=value):
                row = candidate()
                row["confidence"] = value
                with self.assertRaises(ValueError):
                    validate_observation(row)

    def test_rejects_non_normalized_or_invalid_bbox(self):
        for value in (
            [0.5, 0.2, 0.5, 0.8],
            [0.8, 0.2, 0.4, 0.8],
            [-0.1, 0.2, 0.5, 0.8],
            [0.1, 0.2, 1.2, 0.8],
            [0.1, 0.2, float("nan"), 0.8],
            [True, 0.2, 0.5, 0.8],
            [0.1, 0.2, 0.5],
            "0.1,0.2,0.5,0.8",
        ):
            with self.subTest(value=value):
                row = candidate()
                row["bbox_norm_xyxy"] = value
                with self.assertRaises(ValueError):
                    validate_observation(row)

    def test_does_not_accept_missing_required_fields(self):
        for key in candidate():
            with self.subTest(key=key):
                row = candidate()
                row.pop(key)
                with self.assertRaises(ValueError):
                    validate_observation(row)

    def test_does_not_mutate_input(self):
        row = candidate()
        original_bbox = row["bbox_norm_xyxy"]
        out = validate_observation(row)
        out["bbox_norm_xyxy"][0] = 0.9
        self.assertEqual(original_bbox[0], 0.2)
        self.assertIsNot(out["bbox_norm_xyxy"], original_bbox)


if __name__ == "__main__":
    unittest.main()
