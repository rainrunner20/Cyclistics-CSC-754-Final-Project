"""Optional Roboflow inference adapter, with a strict unconfirmed-observation output.

Requires a real model ID, a real image and a user-provided API key in live use.
No test fixture is represented as genuine computer-vision evidence.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from .observation_contract import OBSERVATION_SCHEMA, validate_observation


def _number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    val = float(value)
    if not math.isfinite(val) or (positive and val <= 0):
        raise ValueError(f"{field} must be finite{' and positive' if positive else ''}")
    return val


def normalize_roboflow_response(
    response: dict, *, observed_at_utc: str, frame_id: str,
) -> list[dict]:
    """Convert standard object-detection boxes into owned normalized coordinates.

    Predictions have pixel center (x, y), width, height and an image size.
    We never claim that a recognized truck overlaps or blocks a bicycle lane.
    """
    if not isinstance(response, dict):
        raise ValueError("Roboflow result must be an object")
    image = response.get("image")
    predictions = response.get("predictions")
    if not isinstance(image, dict) or not isinstance(predictions, list):
        raise ValueError("Roboflow result requires image dimensions and predictions list")
    iw = _number(image.get("width"), "image.width", positive=True)
    ih = _number(image.get("height"), "image.height", positive=True)

    if not isinstance(frame_id, str) or not frame_id.strip() or len(frame_id) > 112:
        raise ValueError("frame_id must be a short nonempty identifier")
    observed = []
    for index, pred in enumerate(predictions):
        if not isinstance(pred, dict):
            raise ValueError("Each Roboflow prediction must be an object")
        x = _number(pred.get("x"), "prediction.x")
        y = _number(pred.get("y"), "prediction.y")
        width = _number(pred.get("width"), "prediction.width", positive=True)
        height = _number(pred.get("height"), "prediction.height", positive=True)
        bbox = [
            (x - width / 2) / iw,
            (y - height / 2) / ih,
            (x + width / 2) / iw,
            (y + height / 2) / ih,
        ]
        candidate = {
            "schema": OBSERVATION_SCHEMA,
            "observation_id": f"{frame_id.strip()}:{index}",
            "source": "roboflow",
            "observed_at_utc": observed_at_utc,
            "object_class": pred.get("class"),
            "confidence": pred.get("confidence"),
            "bbox_norm_xyxy": bbox,
            "lane_overlap": None,
            "segment_id": None,
        }
        observed.append(validate_observation(candidate))
    return observed


def infer_image_candidates(
    image_path: Path, *, model_id: str, api_key: str | None,
    observed_at_utc: str, frame_id: str, client: Any = None,
) -> list[dict]:
    """Call inference only with an explicit real image and configured model.

    For tests, a supplied client is injected; the default requires the
    optional inference-sdk and ROBOFLOW_API_KEY environment variable.
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not isinstance(model_id, str) or not model_id.strip() or len(model_id) > 128:
        raise ValueError("A nonempty Roboflow model ID is required")
    # Fail on bad metadata before transmitting any image.
    validate_observation({
        "schema": OBSERVATION_SCHEMA,
        "observation_id": frame_id,
        "source": "roboflow",
        "observed_at_utc": observed_at_utc,
        "object_class": "candidate",
        "confidence": 0,
        "bbox_norm_xyxy": [0, 0, 1, 1],
        "lane_overlap": None,
        "segment_id": None,
    })
    if client is None:
        credential = api_key if api_key is not None else os.getenv("ROBOFLOW_API_KEY")
        if not isinstance(credential, str) or not credential.strip():
            raise ValueError("Set ROBOFLOW_API_KEY for actual Roboflow image inference")
        try:
            from inference_sdk import InferenceHTTPClient
        except ImportError as exc:
            raise RuntimeError(
                "Install the optional inference-sdk package before inference"
            ) from exc
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com", api_key=credential
        )
    raw = client.infer(str(image_path), model_id=model_id)
    return normalize_roboflow_response(raw, observed_at_utc=observed_at_utc,
                                       frame_id=frame_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--observed-at-utc", required=True,
                        help="Actual camera/frame timestamp such as 2026-11-14T16:30:00Z")
    parser.add_argument("--frame-id", required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/v2_candidates.json"))
    args = parser.parse_args()
    rows = infer_image_candidates(
        args.image, model_id=args.model_id, api_key=None,
        observed_at_utc=args.observed_at_utc, frame_id=args.frame_id
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", "utf-8")
    print(f"Wrote {len(rows)} unconfirmed detection candidates to {args.output}")
    print("NOTE: object detection alone does not confirm bicycle-lane obstruction.")


if __name__ == "__main__":
    main()
