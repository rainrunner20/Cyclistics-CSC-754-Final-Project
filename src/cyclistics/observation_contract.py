"""Validate a candidate camera observation before it reaches any simulation.

A detection is not a confirmed bicycle-lane obstruction. This module has no
network access, no ML model, and does not schedule any simulation events.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any

OBSERVATION_SCHEMA = "cyclistics.observation.v1"
FIELDS = frozenset({
    "schema", "observation_id", "source", "observed_at_utc",
    "object_class", "confidence", "bbox_norm_xyxy", "lane_overlap",
    "segment_id",
})
SOURCES = frozenset({"synthetic_fixture", "roboflow", "manual_review"})


def _name(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{field} must be a non-empty string of at most 128 characters")
    return value.strip()


def _normalized_coordinate(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Bounding box coordinates must be numeric")
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError("Bounding box coordinates must be finite and normalized to [0, 1]")
    return number


def validate_observation(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return an owned, JSON-compatible copy of one unconfirmed observation.

    UTC time and a normalized bounding box can be carried across adapters.
    Neither the rectangle nor the classifier score verifies lane occupation.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("Observation payload must be a mapping")
    missing = FIELDS - payload.keys()
    extra = payload.keys() - FIELDS
    if missing:
        raise ValueError(f"Missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected fields: {sorted(extra)}")
    if payload["schema"] != OBSERVATION_SCHEMA:
        raise ValueError("Unsupported observation schema")

    source = _name(payload["source"], "source")
    if source not in SOURCES:
        raise ValueError("Unrecognized observation source")

    stamp = payload["observed_at_utc"]
    if not isinstance(stamp, str) or not stamp.endswith("Z"):
        raise ValueError("observed_at_utc must use explicit UTC (Z)")
    try:
        when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid UTC observation timestamp") from exc
    if when.utcoffset() != timedelta(0):
        raise ValueError("Timestamp must be UTC")
    
    confidence = payload["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence must be numeric in [0, 1]")
    confidence = float(confidence)
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence must be finite and within [0, 1]")

    bounds = payload["bbox_norm_xyxy"]
    if not isinstance(bounds, (tuple, list)) or len(bounds) != 4:
        raise ValueError("bbox_norm_xyxy must have four normalized coordinates")
    x_min, y_min, x_max, y_max = [_normalized_coordinate(v) for v in bounds]
    if x_min >= x_max or y_min >= y_max:
        raise ValueError("Invalid bounding box extents")

    overlap = payload["lane_overlap"]
    if overlap is not None and type(overlap) is not bool:
        raise ValueError("lane_overlap must be true, false or null")

    return {
        "schema": OBSERVATION_SCHEMA,
        "observation_id": _name(payload["observation_id"], "observation_id"),
        "source": source,
        "observed_at_utc": stamp,
        "object_class": _name(payload["object_class"], "object_class"),
        "confidence": confidence,
        "bbox_norm_xyxy": [x_min, y_min, x_max, y_max],
        "lane_overlap": overlap,
        "segment_id": _name(payload["segment_id"], "segment_id", nullable=True),
    }
