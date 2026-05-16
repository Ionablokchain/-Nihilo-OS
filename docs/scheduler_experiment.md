# Nihilo OS — Scheduler Experiment v2

## What changed from v1

v1 established the baseline: a priority tick scheduler with condition
re-evaluation produces max dispatch latency of 1 tick across four
simple scenarios. Two questions were left open:

> 3. *Starvation with many intentions.* With 50 intentions of varying
>    priorities and conditions, which ones are effectively never scheduled?

This version answers that question (**Part B**) by running 50 intentions
without and with aging, and measures the difference. It also completes
the connection between the scheduler and the Flux language (**Part C**):
conditions and bodies are now evaluated by the real TVM rather than
Python lambdas.

---

## Part B — Starvation and aging

### Setup

**50 intentions.** Two "system" intentions (priority 0.9 and 0.8) and
48 "user" intentions with priorities uniformly spaced from 0.01 to 0.49.
All always-eligible, cooldown = 1.

**Two runs:** `B1` no aging; `B2` aging rate 0.01 per tick on the 48 user
intentions (effective priority = base + waiting_ticks × 0.01; resets on
dispatch).

**Starvation threshold:** 10 consecutive ticks eligible but not dispatched.

### Results (1000 ticks)

| Metric | B1 No aging | B2 Aging 0.01 |
|--------|------------|--------------|
| Never-ran intentions | **48** | **0** |
| Total starvation events | 47,520 | 40,664 |
| Max dispatch latency | 1 | **94** |
| Fairness index | 0.0400 | 0.2444 |

### Interpretation

**B1:** The two system intentions alternate every tick. Neither ever has
cooldown overlap, so user intentions never get a slot. 48 of 50
intentions fire 0 times. Fairness index = 0.04.

**B2:** A user intention with base priority 0.49 needs to wait
`(0.80 - 0.49) / 0.01 = 31 ticks` to beat System-B. The lowest-
priority user intention (0.01) needs `(0.80 - 0.01) / 0.01 = 79 ticks`.
Observed max latency = 94 (close to the prediction; jitter from the
ordering of events on the same tick accounts for the difference).

**The trade-off:** Aging eliminates never-ran (48 → 0) but introduces
latency spikes (1 → 94 ticks). Fairness improves (0.04 → 0.24) but
remains well below 1. The aging rate is the design parameter:

    time_to_fire = (dominant_priority - base_priority) / aging_rate

Higher rate = faster breakthrough, more Monitor interruptions.
Lower rate = slower breakthrough, more starvation risk.

---

## Part C — Flux TVM integration

### What changed

`FluxIntentionScheduler` now calls `vm._eval_ast()` at every tick to
evaluate each intention's `condition` field as a real Flux expression.
The TVM's state (mosaics, clock, timelines) persists across ticks.
Bodies are also executed by the TVM.

### Scenarios

**C1 — Single always-eligible intention (heartbeat)**

`causal_void.exists()` always returns true. Identical behavior to A1:
1000 dispatches, latency 0. Wall-clock: 18.8 ms for 1000 ticks vs
1.2 ms for the Python-lambda equivalent — the cost of `_eval_ast`.

**C2 — Two intentions, no aging**

`HighPriority` (0.9) runs all 1000 ticks. `LowPriority` (0.2) runs 0
times and accumulates 990 starvation events. This is the fundamental
priority inversion demonstrated with real Flux code.

**C3 — Three intentions, aging on Worker**

```
Monitor: priority 0.80, no aging
Worker:  priority 0.15, aging_rate 0.02 (set by driver)
Idle:    priority 0.05, no aging
```

After `(0.80 - 0.15) / 0.02 = 32.5` ticks, Worker's effective priority
beats Monitor. Observed: Worker fires every ~33 ticks (29 times in
1000 ticks, max latency 33). Idle never fires — Worker's continuous
aging accumulation always keeps it above Idle's 0.05.

### Overhead

| Scenario | Intentions | Wall-clock | µs per condition eval |
|----------|-----------|-----------|----------------------|
| C1 | 1 | 18.8 ms | ~18.8 |
| C2 | 2 | 29.3 ms | ~14.7 |
| C3 | 3 | 40.8 ms | ~13.6 |

~13–19 µs per `_eval_ast` call. This is interpreter overhead; compiled
conditions would be orders of magnitude faster.

---

## Summary across all parts

| Scenario | Dispatches | Max latency | Fairness | Starvations |
|----------|-----------|------------|---------|-------------|
| A1 Baseline | 500 | 0 | 1.0000 | 0 |
| A2 Priority contention | 667 | 1 | 0.8005 | 0 |
| A3 Late eligibility | 1000 | 1 | 0.7937 | 789 |
| A4 Periodic | 281 | 0 | 0.8217 | 0 |
| B1 50 intentions, no aging | 1000 | 1 | 0.0400 | 47,520 |
| B2 50 intentions, aging 0.01 | 1000 | 94 | 0.2444 | 40,664 |
| C1 Single Flux (TVM) | 1000 | 0 | 1.0000 | 0 |
| C2 Two Flux, no aging | 1000 | 0 | 0.5000 | 990 |
| C3 Three Flux, aging 0.02 | 1000 | 33 | 0.3532 | 1,690 |

---

## Conclusions

**1. Starvation is real and severe at scale.** 48 of 50 intentions
never run in B1. Fairness index 0.04 means scheduling power is almost
entirely concentrated in 2 intentions.

**2. Aging fixes starvation at the cost of latency spikes.** B2:
every intention runs at least once; max latency grows from 1 to 94.

**3. The aging rate encodes a concrete design trade-off:**
`time_to_fire = (dominant_priority - base_priority) / aging_rate`.
Designers can reason about worst-case latency before deployment.

**4. Flux conditions work as scheduler predicates.** Real TVM
expressions (`causal_void.exists()`, mosaic reads, distribution
collapses) drive scheduling decisions. The overhead is ~14 µs per
condition in the Python interpreter.

**5. The priority inversion problem is unsolved.** C2 shows that
without aging, a lower-priority Flux intention starves completely.
Aging (C3) helps one intention but not the lowest. A full solution
requires either aging for all, or a different scheduling discipline
(e.g. lottery scheduling, EDF, or a hybrid).

---

## Remaining open questions

**Priority assignment policy.** All priorities are hand-assigned. A
real system needs a default starting priority and a mechanism for
elevating or lowering it dynamically.

**Aging and shared mosaic state.** If an aging-boosted intention fires
and writes to a mosaic, it may invalidate other intentions' conditions.
The interaction between aging and shared state is untested.

**Aging reset policy.** Resetting the accumulator to zero on dispatch
creates asymmetry: a low-priority intention re-accumulates from scratch.
Alternative: decay gradually (`accum *= 0.9` after each dispatch).

**Tick-to-wall-clock mapping.** The model uses logical ticks. A real
system must choose: fixed-frequency scheduler (predictable latency,
overhead when idle) vs event-driven scheduler (lower idle overhead,
harder to bound latency). The two models have different starvation
properties.

---

## Reproducing the experiment

```bash
cd nihilo-os
python3 experiment.py --ticks 1000           # all parts
python3 experiment.py --ticks 1000 --part b  # aging only
python3 experiment.py --ticks 50  --part c --verbose  # Flux, with trace
```

Output: `results.txt`, `results.csv`.

Implementation: `flux_compiler/compiler/scheduler.py` (~250 lines).
Flux programs: `examples/sched_c*.flux`.
