"""Explicitly approved, synthetic v2 demo from mock observation to replay CSV.

The fixture must never be described as an actual Roboflow detection or NYC
obstruction. Real observations require separate geometry and human review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .observation_contract import validate_observation
from .v2_event_bridge import build_replay_package, event_from_reviewed_observation


def build_demo(
    observation: dict, output_dir: Path, *, approved: bool,
) -> dict:
    item = validate_observation(observation)
    if item["source"] != "synthetic_fixture":
        raise ValueError("This demo only accepts transparently synthetic fixtures")
    if approved is not True:
        raise ValueError("Explicit --approve-synthetic acknowledgement required")
    events = event_from_reviewed_observation(
        item, approved=True, start_tick=12, duration_s=8,
        scenario_id="v2-synthetic-replay",
    )
    return build_replay_package(list(events), output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, default=Path("outputs/v2_demo"))
    parser.add_argument("--approve-synthetic", action="store_true",
                        help="Acknowledge that this creates only a hypothetical scenario")
    args = parser.parse_args()
    item = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_demo(item, args.outdir, approved=args.approve_synthetic)
    print(f"PASS: created {result['event_count']} synthetic, reviewed and approved scenario events")
    print(f"Output directory: {args.outdir}")
    print("These are NOT real camera or city observation data.")


if __name__ == "__main__":
    main()
