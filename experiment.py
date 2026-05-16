#!/usr/bin/env python3
"""
experiment.py -- Intention scheduler experiment for Nihilo OS.

Runs:
  Part A (original 4 scenarios)  -- basic latency and fairness
  Part B (aging / starvation)    -- 50 intentions, with and without aging
  Part C (Flux integration)      -- real Flux programs, conditions via TVM

Usage:
    python3 experiment.py [--ticks N] [--part a|b|c|all] [--verbose]
"""
import argparse, csv, os, sys, time, statistics
from typing import List

HERE = os.path.dirname(__file__)
COMPILER = os.path.join(HERE, "flux_compiler", "compiler")
sys.path.insert(0, COMPILER)

from flux_lexer import Lexer
from flux_parser import Parser
from flux_codegen import BytecodeGenerator
from scheduler import (IntentionSpec, IntentionScheduler,
                        FluxIntentionScheduler, SchedulerMetrics)


def sep(title="", width=64):
    if title:
        pad = (width - len(title) - 2) // 2
        return "=" * pad + f" {title} " + "=" * pad
    return "=" * width


# ─────────────────────────────────────────────────────────────────────────────
# Part A  (original scenarios, kept for reference)
# ─────────────────────────────────────────────────────────────────────────────

def run_a1(ticks): return IntentionScheduler([
    IntentionSpec("Heartbeat", 0.5, lambda t: True, lambda t: None, cooldown=1),
], max_ticks=ticks).run()

def run_a2(ticks): return IntentionScheduler([
    IntentionSpec("Urgent",     0.9, lambda t: True, lambda t: None, cooldown=5),
    IntentionSpec("Background", 0.1, lambda t: True, lambda t: None, cooldown=1),
], max_ticks=ticks).run()

def run_a3(ticks): return IntentionScheduler([
    IntentionSpec("Fast", 0.8, lambda t: True,    lambda t: None, cooldown=1),
    IntentionSpec("Slow", 0.7, lambda t: t >= 200,lambda t: None, cooldown=1),
    IntentionSpec("Idle", 0.05,lambda t: True,    lambda t: None, cooldown=1),
], max_ticks=ticks).run()

def run_a4(ticks): return IntentionScheduler([
    IntentionSpec("Period7",  0.6, lambda t: t%7==0,  lambda t: None),
    IntentionSpec("Period11", 0.4, lambda t: t%11==0, lambda t: None),
    IntentionSpec("Period13", 0.3, lambda t: t%13==0, lambda t: None),
    IntentionSpec("Overlap",  0.8,
        lambda t: (t%7==0 and t%11==0)or(t%7==0 and t%13==0)or(t%11==0 and t%13==0),
        lambda t: None),
], max_ticks=ticks).run()


# ─────────────────────────────────────────────────────────────────────────────
# Part B  -- Starvation and aging
# ─────────────────────────────────────────────────────────────────────────────

def _build_50(aging_rate: float) -> List[IntentionSpec]:
    """50 intentions: one at 0.9, one at 0.8, ..., 48 at very low priority.
    All always-eligible, cooldown 1.  The low-priority ones get starved
    without aging; with aging they eventually accumulate enough to fire.
    """
    specs = []
    # 2 high-priority "system" intentions
    for i, (name, pri) in enumerate([("System-A", 0.9), ("System-B", 0.8)]):
        specs.append(IntentionSpec(name, pri,
                                   lambda t: True, lambda t: None,
                                   cooldown=1, aging_rate=0.0))
    # 48 low-priority "user" intentions, evenly spread 0.01..0.49
    for i in range(48):
        pri = round(0.01 + i * (0.48 / 47), 4)
        specs.append(IntentionSpec(
            f"User-{i:02d}", pri,
            lambda t: True, lambda t: None,
            cooldown=1, aging_rate=aging_rate,
        ))
    return specs

def run_b_no_aging(ticks):
    return IntentionScheduler(_build_50(0.0), max_ticks=ticks).run()

def run_b_aging(ticks, rate=0.01):
    return IntentionScheduler(_build_50(rate), max_ticks=ticks).run()


# ─────────────────────────────────────────────────────────────────────────────
# Part C  -- Flux TVM integration
# ─────────────────────────────────────────────────────────────────────────────

def _compile(path: str):
    with open(path) as f:
        src = f.read()
    prog = Parser(Lexer(src).tokenize()).parse()
    return BytecodeGenerator().generate(prog)

def run_c1(ticks, verbose=False):
    """Single always-eligible Flux intention via TVM."""
    mod = _compile(os.path.join(HERE, "examples", "sched_c1_heartbeat.flux"))
    sched = FluxIntentionScheduler(mod, max_ticks=ticks,
                                    verbose=verbose, capture=True)
    return sched.run(), sched.sink

def run_c2(ticks, verbose=False):
    """Two Flux intentions (high/low priority) with mosaic-based condition."""
    mod = _compile(os.path.join(HERE, "examples", "sched_c2_priority.flux"))
    sched = FluxIntentionScheduler(mod, max_ticks=ticks,
                                    verbose=verbose, capture=True)
    return sched.run(), sched.sink

def run_c3(ticks, verbose=False):
    """Three Flux intentions: aging enabled for the low-priority one."""
    mod = _compile(os.path.join(HERE, "examples", "sched_c3_aging.flux"))
    aging = {"Worker": 0.02}   # Worker ages at 0.02/tick
    sched = FluxIntentionScheduler(mod, max_ticks=ticks,
                                    aging_rates=aging,
                                    verbose=verbose, capture=True)
    return sched.run(), sched.sink


# ─────────────────────────────────────────────────────────────────────────────
# Reporting helpers
# ─────────────────────────────────────────────────────────────────────────────

def _starv_summary(m: SchedulerMetrics) -> str:
    never_ran = [n for n, d in m.per_intention.items() if d["runs"] == 0]
    starved   = [n for n, d in m.per_intention.items()
                 if d["starvation_events"] > 0 and d["runs"] > 0]
    return (f"never-ran={len(never_ran)}  "
            f"starved-but-ran={len(starved)}  "
            f"total-starvation-events={m.starvation_events}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks",   type=int, default=1000)
    ap.add_argument("--part",    default="all",
                    choices=["a","b","c","all"])
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--output",  default="results")
    args = ap.parse_args()

    T = args.ticks
    V = args.verbose
    txt: List[str] = [
        "Nihilo OS — Scheduler Experiment v2",
        f"Ticks per scenario: {T}",
        "",
    ]
    csv_rows = []

    # ── Part A ────────────────────────────────────────────────────────────
    if args.part in ("a", "all"):
        print(sep("PART A — Baseline Scenarios"))
        for label, runner in [
            ("A1 Baseline",          run_a1),
            ("A2 Priority contention",run_a2),
            ("A3 Late eligibility",   run_a3),
            ("A4 Periodic",           run_a4),
        ]:
            t0 = time.perf_counter()
            m = runner(T)
            elapsed = time.perf_counter() - t0
            print(f"\n{sep(label)}")
            print(m.report(show_aging=False))
            print(f"Wall-clock: {elapsed*1000:.1f} ms")
            txt += [sep(label), m.report(), f"Wall-clock: {elapsed*1000:.1f} ms", ""]
            for n, d in m.per_intention.items():
                csv_rows.append(["A", label, n, d["priority"], d["runs"],
                                  round(d["mean_latency"],4), d["max_latency"],
                                  d["starvation_events"],
                                  0.0, round(m.fairness_index,4)])

    # ── Part B ────────────────────────────────────────────────────────────
    if args.part in ("b", "all"):
        print(f"\n{sep('PART B — Starvation and Aging (50 intentions)')}")

        print(f"\n{sep('B1 No aging')}")
        t0 = time.perf_counter()
        m_no = run_b_no_aging(T)
        elapsed = time.perf_counter() - t0
        # Truncated report for 50 intentions: just summary + starvation
        print(f"Dispatches  : {m_no.total_dispatches}")
        print(f"Fairness    : {m_no.fairness_index:.4f}")
        print(f"Max latency : {m_no.max_latency}")
        print(f"Starvation  : {_starv_summary(m_no)}")
        never_ran_no = [n for n, d in m_no.per_intention.items() if d["runs"] == 0]
        print(f"Never-ran   : {never_ran_no[:5]}{'...' if len(never_ran_no)>5 else ''}")
        print(f"Wall-clock  : {elapsed*1000:.1f} ms")
        txt += [sep("B1 No aging"),
                f"Dispatches: {m_no.total_dispatches}",
                f"Fairness: {m_no.fairness_index:.4f}",
                f"Max latency: {m_no.max_latency}",
                f"Starvation: {_starv_summary(m_no)}", ""]
        for n, d in m_no.per_intention.items():
            csv_rows.append(["B-noaging", "B1", n, d["priority"], d["runs"],
                              round(d["mean_latency"],4), d["max_latency"],
                              d["starvation_events"],
                              0.0, round(m_no.fairness_index,4)])

        print(f"\n{sep('B2 Aging rate=0.01')}")
        t0 = time.perf_counter()
        m_ag = run_b_aging(T, rate=0.01)
        elapsed = time.perf_counter() - t0
        print(f"Dispatches  : {m_ag.total_dispatches}")
        print(f"Fairness    : {m_ag.fairness_index:.4f}")
        print(f"Max latency : {m_ag.max_latency}")
        print(f"Starvation  : {_starv_summary(m_ag)}")
        never_ran_ag = [n for n, d in m_ag.per_intention.items() if d["runs"] == 0]
        print(f"Never-ran   : {never_ran_ag[:5] or 'none'}")
        print(f"Wall-clock  : {elapsed*1000:.1f} ms")
        txt += [sep("B2 Aging rate=0.01"),
                f"Dispatches: {m_ag.total_dispatches}",
                f"Fairness: {m_ag.fairness_index:.4f}",
                f"Max latency: {m_ag.max_latency}",
                f"Starvation: {_starv_summary(m_ag)}", ""]
        for n, d in m_ag.per_intention.items():
            csv_rows.append(["B-aging", "B2", n, d["priority"], d["runs"],
                              round(d["mean_latency"],4), d["max_latency"],
                              d["starvation_events"],
                              d["aging_rate"], round(m_ag.fairness_index,4)])

        # Comparison
        print(f"\n{'Metric':<30} {'No aging':>12} {'Aging 0.01':>12}")
        print("-" * 56)
        for label, v1, v2 in [
            ("Never-ran intentions", len(never_ran_no), len(never_ran_ag)),
            ("Starvation events",    m_no.starvation_events, m_ag.starvation_events),
            ("Max latency (ticks)",  m_no.max_latency, m_ag.max_latency),
            ("Fairness index",
             round(m_no.fairness_index,4), round(m_ag.fairness_index,4)),
        ]:
            print(f"{label:<30} {str(v1):>12} {str(v2):>12}")

    # ── Part C ────────────────────────────────────────────────────────────
    if args.part in ("c", "all"):
        print(f"\n{sep('PART C — Flux TVM Integration')}")

        for label, runner in [
            ("C1 Single Flux intention (heartbeat)", run_c1),
            ("C2 Two Flux intentions (priority)",    run_c2),
            ("C3 Three Flux intentions (aging)",     run_c3),
        ]:
            print(f"\n{sep(label)}")
            t0 = time.perf_counter()
            m, sink = runner(T, verbose=V)
            elapsed = time.perf_counter() - t0
            print(m.report(show_aging=True))
            if sink.events:
                sample = sink.events[:3]
                print(f"Sample sensations: "
                      + ", ".join(f"[{k}]{v}" for k,v,_ in sample))
            print(f"Wall-clock: {elapsed*1000:.1f} ms")
            txt += [sep(label), m.report(show_aging=True),
                    f"Wall-clock: {elapsed*1000:.1f} ms", ""]
            for n, d in m.per_intention.items():
                csv_rows.append(["C", label, n, d["priority"], d["runs"],
                                  round(d["mean_latency"],4), d["max_latency"],
                                  d["starvation_events"],
                                  d["aging_rate"], round(m.fairness_index,4)])

    # ── Write output ───────────────────────────────────────────────────────
    txt_path = args.output + ".txt"
    with open(txt_path, "w") as f:
        f.write("\n".join(txt))
    print(f"\nReport → {txt_path}")

    csv_path = args.output + ".csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["part","scenario","intention","priority","runs",
                    "mean_latency","max_latency","starvation_events",
                    "aging_rate","fairness_index"])
        w.writerows(csv_rows)
    print(f"CSV    → {csv_path}")


if __name__ == "__main__":
    main()
