"""Export real Python DES event traces for the Cyclistics visual lab.

This is a replay of the Python reference, not a DEVS-Suite coordinator log.
Policy runs share arrivals so changing the obstruction is the experiment.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .simulation import Scenario, sample_arrivals, simulate

SCHEMA = "cyclistics.visual_lab.v1"
EVENT_MEANING = {
    "arrival": "A cyclist reaches the bottleneck; service starts if the lane is available.",
    "obstruction_start": "The lane closes to new service; service already in progress may finish.",
    "obstruction_end": "The lane reopens; the next waiting cyclist may begin service.",
    "service_complete": "A cyclist completes bottleneck service; the next rider may start.",
}


def build_visual_lab(
    *,
    rate: float = 900,
    horizon: float = 300,
    seed: int = 754,
    blockage_start: float = 45,
    blockage_duration: float = 120,
    early_clearance_duration: float = 30,
    arrivals: list[float] | None = None,
) -> dict:
    """Compare three scenarios using one sampled or explicitly supplied arrival list."""
    parameters = (rate, horizon, blockage_start, blockage_duration, early_clearance_duration)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in parameters):
        raise ValueError("All numeric scenario parameters must be finite.")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer.")
    if not (0 <= rate <= 7200 and horizon > 0):
        raise ValueError("rate must be 0..7200 cyclists/hour and horizon must be positive.")
    if not (0 <= blockage_start < horizon):
        raise ValueError("blockage_start must fall inside the simulation horizon.")
    if not (0 < early_clearance_duration <= blockage_duration):
        raise ValueError("Early clearance must be positive and no longer than the blockage.")
    if blockage_start + blockage_duration > horizon:
        raise ValueError("The full blockage must end inside the simulation horizon.")

    input_arrivals = (
        sample_arrivals(rate, horizon, seed)
        if arrivals is None else list(arrivals)
    )
    if len(input_arrivals) > 30000:
        raise ValueError("Too many arrivals for the visual trace; use a shorter horizon.")

    cases = (
        ("clear_lane", "No obstruction", ()),
        (
            "blocked_lane",
            "Standard clearance",
            ((blockage_start, blockage_start + blockage_duration),),
        ),
        (
            "early_clearance",
            "Early clearance",
            ((blockage_start, blockage_start + early_clearance_duration),),
        ),
    )
    scenarios = []
    for key, label, intervals in cases:
        summary, trace, _ = simulate(
            Scenario(key, intervals, horizon_s=horizon),
            input_arrivals,
        )
        arrived = completed = 0
        events = []
        for index, row in enumerate(trace):
            if row["event"] == "arrival":
                arrived += 1
            elif row["event"] == "service_complete":
                completed += 1
            in_service = int(row["server_busy"])
            waiting = int(row["queue_waiting"])
            state = "blocked" if row["blocked"] else ("serving" if in_service else "idle")
            conserved = arrived == completed + waiting + in_service
            if not conserved:
                raise AssertionError("Cyclist accounting failed while exporting event trace.")
            events.append({
                "index": index,
                "time_s": row["time_s"],
                "event": row["event"],
                "description": EVENT_MEANING[row["event"]],
                "phase": state,
                "blocked": bool(row["blocked"]),
                "server_busy": bool(in_service),
                "queue_waiting": waiting,
                "arrived_so_far": arrived,
                "completed_so_far": completed,
                "conservation_ok": conserved,
            })
        scenarios.append({
            "id": key,
            "label": label,
            "blockage_intervals_s": [list(pair) for pair in intervals],
            "metrics": summary,
            "events": events,
        })
    return {
        "schema": SCHEMA,
        "engine": "python_des_reference",
        "data_status": "synthetic",
        "method": "paired_scenarios_shared_arrival_times",
        "limitations": [
            "This browser playback uses Python DES output, not the DEVSJAVA coordinator.",
            "It is a single FIFO bottleneck without cyclist geometry, merging, or crash risk.",
            "Queue delays and policy outcomes have not been validated against NYC observations.",
            "Trace timestamps are rounded to milliseconds by the reference model.",
        ],
        "parameters": {
            "rate_per_hour": rate,
            "arrival_horizon_s": horizon,
            "seed": seed,
            "blockage_start_s": blockage_start,
            "blockage_duration_s": blockage_duration,
            "early_clearance_duration_s": early_clearance_duration,
            "arrival_count": len(input_arrivals),
            "arrival_source": "seeded_poisson" if arrivals is None else "explicit_synthetic_test",
        },
        "event_ordering": {
            "description": "Python DES event-heap ordering at identical exact timestamps.",
            "priority": ["obstruction_end", "obstruction_start", "service_complete", "arrival"],
            "tie_breaker": "insertion_sequence",
        },
        "scenarios": scenarios,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export paired Python DES policy traces for the Cyclistics event inspector."
    )
    parser.add_argument("--rate", type=float, default=900)
    parser.add_argument("--horizon", type=float, default=300)
    parser.add_argument("--seed", type=int, default=754)
    parser.add_argument("--blockage-start", type=float, default=45)
    parser.add_argument("--blockage-duration", type=float, default=120)
    parser.add_argument("--early-clearance-duration", type=float, default=30)
    parser.add_argument("--output", type=Path, default=Path("outputs/visual_lab.json"))
    args = parser.parse_args()

    payload = build_visual_lab(
        rate=args.rate,
        horizon=args.horizon,
        seed=args.seed,
        blockage_start=args.blockage_start,
        blockage_duration=args.blockage_duration,
        early_clearance_duration=args.early_clearance_duration,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Exported {len(payload['scenarios'])} paired Python DES scenarios to {args.output}")
    print("Synthetic model output only; not NetLogo, Java, or observed NYC traffic.")


if __name__ == "__main__":
    main()
