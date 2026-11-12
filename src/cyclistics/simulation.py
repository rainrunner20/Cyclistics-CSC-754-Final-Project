"""Transparent discrete-event reference for a single bike-lane bottleneck.

This is NOT a DEVSJAVA model: it is the baseline to test event semantics before
porting atomic/coupled components into Dr. Gu's required Java framework.
"""
from __future__ import annotations

import argparse
import csv
import heapq
import math
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


PRIORITY = {"obstruction_end": 0, "obstruction_start": 1, "service_complete": 2, "arrival": 3}


@dataclass(order=True)
class Event:
    time_s: float
    priority: int
    sequence: int
    kind: str = field(compare=False)


@dataclass(frozen=True)
class Scenario:
    name: str
    blockage_intervals: tuple[tuple[float, float], ...] = ()
    horizon_s: float = 1800
    service_headway_s: float = 3
    freeflow_travel_s: float = 20

    def __post_init__(self) -> None:
        if (
            not all(math.isfinite(v) for v in (self.horizon_s, self.service_headway_s, self.freeflow_travel_s))
            or self.horizon_s <= 0
            or self.service_headway_s <= 0
            or self.freeflow_travel_s < 0
        ):
            raise ValueError("Time parameters must be positive (freeflow can be zero).")
        last_end = float('-inf')
        for start, end in self.blockage_intervals:
            if (
                not math.isfinite(start)
                or not math.isfinite(end)
                or not (0 <= start < end <= self.horizon_s)
                or start < last_end
            ):
                raise ValueError("Blockages must be sorted, non-overlapping, and within the horizon.")
            last_end = end


def sample_arrivals(rate_per_hour: float, horizon_s: float, seed: int) -> list[float]:
    """Poisson arrivals: synthetic unless the rate is calibrated against actual counts."""
    if (
        not math.isfinite(rate_per_hour)
        or not math.isfinite(horizon_s)
        or rate_per_hour < 0
        or horizon_s <= 0
    ):
        raise ValueError("Arrival rate must be >=0 and horizon >0.")
    if rate_per_hour == 0:
        return []
    rng = random.Random(seed)
    times: list[float] = []
    t = 0.0
    while True:
        t += rng.expovariate(rate_per_hour / 3600)
        if t > horizon_s:
            break
        times.append(t)
    return times


def simulate(scenario: Scenario, arrivals: list[float]) -> tuple[dict, list[dict], list[dict]]:
    """One server with FIFO waiting, disabled during an obstruction.

    Assumption: cyclists already being served finish that headway when blockage begins;
    no *new* cyclist can enter the bottleneck until blockage ends. The headway models
    a passage bottleneck, not the full 100m travel time.
    """
    if (
        any(not math.isfinite(t) or t < 0 or t > scenario.horizon_s for t in arrivals)
        or arrivals != sorted(arrivals)
    ):
        raise ValueError("Arrival timestamps must be sorted and within the horizon.")
    heap: list[Event] = []
    sequence = 0

    def schedule(t: float, kind: str) -> None:
        nonlocal sequence
        heapq.heappush(heap, Event(t, PRIORITY[kind], sequence, kind))
        sequence += 1

    for time_s in arrivals:
        schedule(time_s, "arrival")
    for start, end in scenario.blockage_intervals:
        schedule(start, "obstruction_start")
        schedule(end, "obstruction_end")

    queue: deque[float] = deque()
    blocked = False
    server_busy = False
    current_arrival: float | None = None
    wait_times: list[float] = []
    completed_within_horizon = 0
    max_queue = 0
    trace: list[dict] = []
    exported_events: list[dict] = []

    def start_next(t: float) -> None:
        nonlocal server_busy, current_arrival
        if blocked or server_busy or not queue:
            return
        current_arrival = queue.popleft()
        server_busy = True
        schedule(t + scenario.service_headway_s, "service_complete")

    while heap:
        event = heapq.heappop(heap)
        t = event.time_s
        kind = event.kind
        if kind == "obstruction_start":
            blocked = True
        elif kind == "obstruction_end":
            blocked = False
            start_next(t)
        elif kind == "arrival":
            queue.append(t)
            start_next(t)
        elif kind == "service_complete":
            if current_arrival is None or not server_busy:
                raise AssertionError("Service completion without an in-progress cyclist")
            wait_times.append(max(0.0, t - scenario.service_headway_s - current_arrival))
            if t <= scenario.horizon_s:
                completed_within_horizon += 1
            current_arrival = None
            server_busy = False
            start_next(t)
        else:
            raise AssertionError(f"Unknown event {kind}")

        max_queue = max(max_queue, len(queue))
        trace.append({"time_s": round(t, 3), "event": kind,
                      "queue_waiting": len(queue), "blocked": int(blocked),
                      "server_busy": int(server_busy)})
        if kind in ("arrival", "obstruction_start", "obstruction_end"):
            exported_events.append({"time_s": round(t, 3), "event_type": kind, "value": 1})

    if len(wait_times) != len(arrivals):
        raise AssertionError("Every arrival must eventually finish; check model assumptions.")
    sorted_wait = sorted(wait_times)
    p95_index = max(0, math.ceil(0.95 * len(sorted_wait)) - 1)
    summary = {
        "scenario": scenario.name,
        "arrivals": len(arrivals),
        "completed_all": len(wait_times),
        "completed_by_horizon": completed_within_horizon,
        "mean_wait_s": round(sum(wait_times) / len(wait_times), 3) if wait_times else 0.0,
        "p95_wait_s": round(sorted_wait[p95_index], 3) if wait_times else 0.0,
        "max_waiting_queue": max_queue,
        "throughput_per_hour_during_horizon": round(completed_within_horizon * 3600 / scenario.horizon_s, 3),
        "assumed_freeflow_travel_s": scenario.freeflow_travel_s,
        "mean_estimated_travel_s": round(scenario.freeflow_travel_s + (sum(wait_times) / len(wait_times)), 3) if wait_times else 0.0,
    }
    return summary, trace, exported_events


def save_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_suite(output_dir: Path, arrival_rate_per_hour: float = 300,
              horizon_s: float = 1800, seed: int = 754) -> list[dict]:
    if horizon_s < 870 or not math.isfinite(horizon_s):
        raise ValueError("The default scenario suite requires --horizon >= 870 seconds.")
    arrivals = sample_arrivals(arrival_rate_per_hour, horizon_s, seed)
    scenarios = [
        Scenario("clear_lane", horizon_s=horizon_s),
        Scenario("blocked_5min", ((300, 600),), horizon_s=horizon_s),
        Scenario("faster_clearance_1min", ((300, 360),), horizon_s=horizon_s),
        Scenario("repeat_blockages", ((300, 420), (750, 870)), horizon_s=horizon_s),
    ]
    metrics: list[dict] = []
    for scenario in scenarios:
        summary, trace, exported = simulate(scenario, arrivals)
        metrics.append(summary)
        save_csv(output_dir / f"trace_{scenario.name}.csv", trace,
                 ["time_s", "event", "queue_waiting", "blocked", "server_busy"])
        save_csv(output_dir / f"netlogo_events_{scenario.name}.csv", exported,
                 ["time_s", "event_type", "value"])
    save_csv(output_dir / "scenario_metrics.csv", metrics, list(metrics[0].keys()))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Cyclistics single-segment DES reference experiments")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--rate", type=float, default=300, help="synthetic cyclists/hour")
    parser.add_argument("--horizon", type=float, default=1800, help="seconds of arrivals")
    parser.add_argument("--seed", type=int, default=754)
    args = parser.parse_args()
    results = run_suite(Path(args.output_dir), args.rate, args.horizon, args.seed)
    for r in results:
        print(f"{r['scenario']:24s} | arrivals={r['arrivals']:3d} | "
              f"mean wait={r['mean_wait_s']:7.2f}s | p95={r['p95_wait_s']:7.2f}s | "
              f"max queue={r['max_waiting_queue']:3d}")


if __name__ == "__main__":
    main()
