"""Offline, deterministic tests for the NYC Open Data read-only client."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics.nyc_open_data import build_url, fetch_sample, validate_records


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class OpenDataTests(unittest.TestCase):
    def test_url_uses_official_dataset_and_bounded_limit(self):
        url = build_url("counts", 5)
        self.assertIn("ct66-47at.json", url)
        self.assertIn("%24limit=5", url)
        self.assertIn("timestamp+DESC", url)

    def test_invalid_dataset_or_limit_rejected(self):
        for dataset, limit in (("invalid", 5), ("sensors", 0), ("counts", 1001)):
            with self.subTest(dataset=dataset, limit=limit):
                with self.assertRaises(ValueError):
                    build_url(dataset, limit)

    def test_fetch_sensors_and_preserve_provenance(self):
        records = [{"id": "42", "name": "Demo Counter", "lat": "40.7", "lon": "-74.0"}]
        with patch("cyclistics.nyc_open_data.urlopen", return_value=_FakeResponse(json.dumps(records).encode())) as opener:
            snapshot = fetch_sample("sensors", limit=1, token="fake-for-unit-test")
        self.assertEqual(snapshot["record_count"], 1)
        self.assertEqual(snapshot["dataset_id"], "6up2-gnw8")
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header("X-app-token"), "fake-for-unit-test")
        self.assertNotIn("fake-for-unit-test", snapshot["query_url"])

    def test_valid_numeric_string_count(self):
        row = {"sensor_id": "42", "travelmode": "Bicycle", "timestamp": "2026-11-01T12:00:00", "counts": "3"}
        self.assertEqual(validate_records("counts", [row]), [row])

    def test_missing_schema_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_records("sensors", [{"id": "42"}])

    def test_negative_and_invalid_counts_are_rejected(self):
        base = {"sensor_id": "42", "travelmode": "Bicycle", "timestamp": "2026-11-01T12:00:00"}
        for value in ("-1", "nan", "invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_records("counts", [dict(base, counts=value)])

    def test_non_list_response_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "JSON list"):
            validate_records("counts", {"message": "wrong shape"})


if __name__ == "__main__":
    unittest.main()
