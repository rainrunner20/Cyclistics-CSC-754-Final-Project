"""Tests for grounded GeoJSON output consumed by the ArcGIS v2 dashboard."""
import json
import tempfile
import unittest
from pathlib import Path

from cyclistics.v2_geojson import build_geojson, write_geojson


def item():
    return {
        "longitude": -73.98, "latitude": 40.66,
        "location_source": "user_supplied_coordinate",
        "scenario_id": "synthetic-demo",
        "event_type": "obstruction_start",
        "simulated_time_s": 45,
        "data_status": "simulated",
        "mean_queue_cyclists": 3.0,
    }


class V2GeojsonTests(unittest.TestCase):
    def test_exports_only_supplied_coordinates_and_labels_simulation(self):
        result = build_geojson([item()])
        self.assertEqual(result["type"], "FeatureCollection")
        self.assertEqual(len(result["features"]), 1)
        feat = result["features"][0]
        self.assertEqual(feat["geometry"]["coordinates"], [-73.98, 40.66])
        self.assertEqual(feat["properties"]["data_status"], "simulated")
        self.assertEqual(feat["properties"]["location_source"], "user_supplied_coordinate")

    def test_rejects_invalid_coordinates_or_unsupported_status(self):
        for key, val in (
            ("longitude", -200), ("latitude", 98),
            ("longitude", float("nan")), ("latitude", True),
            ("data_status", "observed_real_queue"),
            ("location_source", ""),
            ("simulated_time_s", -1), ("mean_queue_cyclists", -1),
        ):
            with self.subTest(key=key):
                row = item()
                row[key] = val
                with self.assertRaises(ValueError):
                    build_geojson([row])

    def test_no_coordinate_guessing_and_no_secret_extra_properties(self):
        row = item()
        row.pop("longitude")
        with self.assertRaises(ValueError):
            build_geojson([row])
        row = item()
        row["camera_private_url"] = "private"
        with self.assertRaises(ValueError):
            build_geojson([row])

    def test_empty_geojson_is_allowed_without_inventing_a_pin(self):
        self.assertEqual(build_geojson([]),
                         {"type": "FeatureCollection", "features": []})

    def test_writer_preserves_exact_explicit_data(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scenarios.geojson"
            write_geojson([item()], path)
            parsed = json.loads(path.read_text("utf-8"))
            self.assertEqual(parsed["features"][0]["properties"]["scenario_id"],
                             "synthetic-demo")


if __name__ == "__main__":
    unittest.main()
