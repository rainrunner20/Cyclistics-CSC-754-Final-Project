"""Read-only, bounded NYC Open Data samples for Cyclistics.

Research/prototyping client. This module does not calibrate arrival rates or
claim that sampled bicycle/pedestrian counts describe a particular bike lane.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://data.cityofnewyork.us/resource"
DATASETS = {
    "sensors": {
        "id": "6up2-gnw8",
        "order": "id ASC",
        "required": ("id", "name"),
    },
    "counts": {
        "id": "ct66-47at",
        "order": "timestamp DESC",
        "required": ("sensor_id", "travelmode", "timestamp", "counts"),
    },
}
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def build_url(dataset: str, limit: int) -> str:
    """Build a safe, bounded sample query using an allowlisted dataset."""
    if dataset not in DATASETS:
        raise ValueError(f"Unknown dataset: {dataset!r}")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("--limit must be a whole number between 1 and 1000")
    spec = DATASETS[dataset]
    params = urlencode({"$limit": limit, "$order": spec["order"]})
    return f"{BASE_URL}/{spec['id']}.json?{params}"


def validate_records(dataset: str, rows: object) -> list[dict]:
    """Reject obviously malformed API responses without guessing missing values."""
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON list from NYC Open Data")
    required = set(DATASETS[dataset]["required"])
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Record {index}: expected a JSON object")
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Record {index}: missing required fields {sorted(missing)}")
        if dataset == "counts":
            # Socrata often serializes numeric attributes as strings.
            try:
                count = float(row["counts"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Record {index}: invalid counts value") from exc
            if not (0 <= count < float("inf")):
                raise ValueError(f"Record {index}: counts must be finite and nonnegative")
    return rows


def fetch_sample(dataset: str, limit: int = 5, token: str | None = None) -> dict:
    """Fetch a small sample, retrying temporary server failures at most twice."""
    url = build_url(dataset, limit)
    headers = {"Accept": "application/json", "User-Agent": "Cyclistics-research/0.2"}
    app_token = token if token is not None else os.getenv("SOCRATA_APP_TOKEN")
    if app_token:
        headers["X-App-Token"] = app_token  # Never place tokens in URL or output.
    request = Request(url, headers=headers)

    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
            break
        except HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS or attempt == 2:
                raise RuntimeError(f"NYC Open Data request failed with HTTP {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt == 2:
                raise RuntimeError(f"NYC Open Data network error: {exc.reason if isinstance(exc, URLError) else exc}") from exc
        time.sleep(min(2**attempt, 4))

    records = validate_records(dataset, payload)
    return {
        "source": "NYC Open Data / NYC Department of Transportation",
        "dataset": dataset,
        "dataset_id": DATASETS[dataset]["id"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "query_url": url,
        "record_count": len(records),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a bounded NYC DOT dataset sample")
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--limit", type=int, default=5, help="sample rows, 1–1000")
    parser.add_argument("--output", type=Path, help="destination JSON file")
    args = parser.parse_args()
    # Validate before the network request.
    build_url(args.dataset, args.limit)
    output = args.output or Path("outputs") / f"nyc_{args.dataset}_sample.json"
    snapshot = fetch_sample(args.dataset, args.limit)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {snapshot['record_count']} {args.dataset} records to {output}")
    print("These are raw API sample records, NOT calibrated simulation parameters.")


if __name__ == "__main__":
    main()
