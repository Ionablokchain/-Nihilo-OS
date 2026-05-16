#!/usr/bin/env python3
"""
visualize.py -- ASCII timeline of who ran at each tick.

Usage:
    python3 visualize.py [--ticks N] [--scenario 1|2|3|4] [--width W]

Prints a compact timeline where each column is one tick and each row
is one intention. A filled block (█) means the intention ran that tick;
a dot (·) means it was idle or cooling; a dash (–) means not yet
eligible.
"""
import argparse
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "flux_compiler", "compiler"))

from scheduler import IntentionSpec, IntentionScheduler, DispatchEvent


def build_scenario(n: int, ticks: int):
    if n == 1:
        return [
            IntentionSpec("Heartbeat", 0.5, lambda t: True, lambda t: None, cooldown=1)
        ]
    if n == 2:
        return [
            IntentionSpec("Urgent",     0.9, lambda t: True, lambda t: None, cooldown=5),
            IntentionSpec("Background", 0.1, lambda t: True, lambda t: None, cooldown=1),
        ]
    if n == 3:
        return [
            IntentionSpec("Fast", 0.8, lambda t: True,      lambda t: None, cooldown=1),
            IntentionSpec("Slow", 0.7, lambda t: t >= 30,   lambda t: None, cooldown=1),
            IntentionSpec("Idle", 0.05, lambda t: True,     lambda t: None, cooldown=1),
        ]
    if n == 4:
        return [
            IntentionSpec("Period7",  0.6, lambda t: t % 7 == 0,  lambda t: None),
            IntentionSpec("Period11", 0.4, lambda t: t % 11 == 0, lambda t: None),
            IntentionSpec("Period13", 0.3, lambda t: t % 13 == 0, lambda t: None),
            IntentionSpec("Overlap",  0.8,
                lambda t: (t%7==0 and t%11==0) or (t%7==0 and t%13==0) or (t%11==0 and t%13==0),
                lambda t: None),
        ]
    raise ValueError(f"unknown scenario {n}")


def draw(scenario: int, ticks: int, width: int):
    specs = build_scenario(scenario, ticks)
    sched = IntentionScheduler(specs, max_ticks=ticks)
    metrics = sched.run()

    # Build a set of (name, tick) for dispatched events.
    fired: set = {(e.intention_name, e.dispatch_tick) for e in metrics.dispatch_log}

    # Truncate to `width` columns.
    display_ticks = min(ticks, width)
    step = max(1, ticks // width)

    names = [s.name for s in specs]
    col_w = max(len(n) for n in names) + 2

    print(f"\nScenario {scenario} — first {display_ticks * step} ticks "
          f"(each column = {step} ticks)\n")

    # Header: tick numbers
    header = " " * col_w
    for t in range(0, display_ticks * step, step):
        header += str(t % 100).rjust(1) if display_ticks <= 80 else "."
    print(header)
    print(" " * col_w + "─" * display_ticks)

    for name in names:
        row = f"{name:<{col_w}}"
        for t in range(0, display_ticks * step, step):
            # Aggregate: did this intention fire in [t, t+step)?
            did_fire = any((name, t2) in fired for t2 in range(t, min(t+step, ticks)))
            row += "█" if did_fire else "·"
        # Per-intention stats on the right.
        d = metrics.per_intention[name]
        row += f"  runs={d['runs']:4d}  maxlat={d['max_latency']}"
        print(row)

    print(" " * col_w + "─" * display_ticks)
    print(f"\nFairness: {metrics.fairness_index:.4f}  "
          f"Total dispatches: {metrics.total_dispatches}  "
          f"Idle ticks: {metrics.idle_ticks}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=100)
    ap.add_argument("--scenario", type=int, default=2, choices=[1, 2, 3, 4])
    ap.add_argument("--width", type=int, default=80,
                    help="max columns in the timeline")
    args = ap.parse_args()
    draw(args.scenario, args.ticks, args.width)


if __name__ == "__main__":
    main()
