"""Tests for the NYC Open Data client. No internet connection required."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Make the src/ package importable when running unittest directly from the repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cyclistics.nyc_open_data import build_url, fetch_sample, validate_records


class _FakeResponse(io.BytesIO):
    """A tiny stand-in for the file-like response returned by urlopen()."""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class OpenDataTests(unittest.TestCase):
    def test_url_uses_official_dataset_and_bounded_limit(self):
        # Check URL construction without contacting NYC's servers.
        url = build_url("counts", 5)
        self.assertIn("ct66-47at.json", url)
        self.assertIn("%24limit=5", url)
        self.assertIn("timestamp+DESC", url)

    def test_invalid_dataset_or_limit_rejected(self):
        # We deliberately limit this starter tool to known datasets/small samples.
        for dataset, limit in (("invalid", 5), ("sensors", 0), ("counts", 1001)):
            with self.subTest(dataset=dataset, limit=limit):
                with self.assertRaises(ValueError):
                    build_url(dataset, limit)

    def test_fetch_sensors_and_preserve_provenance(self):
        records = [{"id": "42", "name": "Demo Counter", "lat": "40.7", "lon": "-74.0"}]

        # Mock the HTTP request so our CI tests don't depend on a live API.
        with patch("cyclistics.nyc_open_data.urlopen", return_value=_FakeResponse(json.dumps(records).encode())) as opener:
            snapshot = fetch_sample("sensors", limit=1, token="fake-for-unit-test")

        self.assertEqual(snapshot["record_count"], 1)
        self.assertEqual(snapshot["dataset_id"], "6up2-gnw8")

        # This also checks that the app token stays out of the saved request URL.
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header("X-app-token"), "fake-for-unit-test")
        self.assertNotIn("fake-for-unit-test", snapshot["query_url"])

    def test_valid_numeric_string_count(self):
        # Socrata can represent numeric counts as strings, so '3' is valid.
        row = {"sensor_id": "42", "travelmode": "Bicycle", "timestamp": "2026-11-01T12:00:00", "counts": "3"}
        self.assertEqual(validate_records("counts", [row]), [row])

    def test_missing_schema_field_is_rejected(self):
        # A changed or incomplete API response should fail visibly.
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_records("sensors", [{"id": "42"}])

    def test_negative_and_invalid_counts_are_rejected(self):
        # Negative, NaN, and non-numeric values aren't sensible bicycle counts.
        base = {"sensor_id": "42", "travelmode": "Bicycle", "timestamp": "2026-11-01T12:00:00"}
        for value in ("-1", "nan", "invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_records("counts", [dict(base, counts=value)])

    def test_non_list_response_is_rejected(self):
        # A normal result should be a list of rows, not an error object.
        with self.assertRaisesRegex(ValueError, "JSON list"):
            validate_records("counts", {"message": "wrong shape"})


if __name__ == "__main__":
    unittest.main()
