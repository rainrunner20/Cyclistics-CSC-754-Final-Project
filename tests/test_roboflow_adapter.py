"""Unit tests for Roboflow prediction conversion; no hosted API is contacted."""
import json
import tempfile
import unittest
from pathlib import Path

from cyclistics.roboflow_adapter import (
    infer_image_candidates,
    normalize_roboflow_response,
)


class _RecordingClient:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def infer(self, image, model_id):
        self.calls.append((image, model_id))
        return self.output


def response():
    return {
        "image": {"width": 640, "height": 480},
        "predictions": [
            {"class": "truck", "confidence": 0.91,
             "x": 320, "y": 220, "width": 160, "height": 200}
        ],
    }


class RoboflowAdapterTests(unittest.TestCase):
    def test_transforms_real_api_response_shape_to_unconfirmed_observations(self):
        result = normalize_roboflow_response(
            response(), observed_at_utc="2026-11-14T16:30:00Z",
            frame_id="test-frame")
        self.assertEqual(len(result), 1)
        obj = result[0]
        self.assertEqual(obj["source"], "roboflow")
        self.assertEqual(obj["bbox_norm_xyxy"],
                         [0.375, 0.25, 0.625, 0.6666666666666666])
        self.assertIsNone(obj["lane_overlap"])
        self.assertIsNone(obj["segment_id"])
        self.assertEqual(obj["object_class"], "truck")

    def test_client_is_optional_and_all_data_passed_explicitly(self):
        client = _RecordingClient(response())
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "frame.jpg"
            file.write_bytes(b"test only; provider is mocked")
            result = infer_image_candidates(
                file, model_id="example/1", api_key=None, client=client,
                observed_at_utc="2026-11-14T16:30:00Z", frame_id="test-1")
            self.assertEqual(client.calls, [(str(file), "example/1")])
            self.assertEqual(result[0]["observation_id"], "test-1:0")

    def test_invalid_image_dimensions_and_box_are_rejected(self):
        for invalid in (
            {**response(), "image": {"width": 0, "height": 480}},
            {**response(), "image": {"width": 640, "height": 480}, "predictions": [
                {"class": "truck", "confidence": 0.7, "x": 900,
                 "y": 220, "width": 160, "height": 200},
            ]},
            {**response(), "image": {"width": 640, "height": 480}, "predictions": [
                {"class": "truck", "confidence": 1.3, "x": 320,
                 "y": 220, "width": 160, "height": 200},
            ]},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    normalize_roboflow_response(
                        invalid, observed_at_utc="2026-11-14T16:30:00Z",
                        frame_id="bad")

    def test_invalid_schema_empty_or_nonlist_predictions_are_rejected(self):
        for bad in (None, [], {"predictions": []}, {"image": {"width": 5, "height": 6},
                                                    "predictions": "not a list"}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    normalize_roboflow_response(
                        bad, observed_at_utc="2026-11-14T16:30:00Z", frame_id="invalid")

    def test_missing_image_or_credentials_fail_before_network(self):
        with tempfile.TemporaryDirectory() as root:
            missing = Path(root) / "missing.jpg"
            with self.assertRaises(FileNotFoundError):
                infer_image_candidates(
                    missing, model_id="sample/1", api_key=None,
                    observed_at_utc="2026-11-14T16:30:00Z", frame_id="missing")
            image = Path(root) / "test.jpg"
            image.write_bytes(b"a")
            with self.assertRaisesRegex(ValueError, "ROBOFLOW_API_KEY"):
                infer_image_candidates(
                    image, model_id="sample/1", api_key="",
                    observed_at_utc="2026-11-14T16:30:00Z", frame_id="missing")

    def test_model_id_and_timestamp_must_be_explicit(self):
        with tempfile.TemporaryDirectory() as root:
            image = Path(root) / "f.jpg"
            image.write_bytes(b"sample")
            client = _RecordingClient(response())
            with self.assertRaises(ValueError):
                infer_image_candidates(
                    image, model_id="", api_key=None, client=client,
                    observed_at_utc="2026-11-14T16:30:00Z", frame_id="x")
            with self.assertRaises(ValueError):
                infer_image_candidates(
                    image, model_id="sample/1", api_key=None, client=client,
                    observed_at_utc="2026-11-14T11:30:00", frame_id="x")


if __name__ == "__main__":
    unittest.main()
