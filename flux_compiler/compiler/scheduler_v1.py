# scheduler.py - Priority scheduler with condition re-evaluation.
#
# This is the experiment.
#
# The stock Flux TVM runs intentions once, sorted by priority. This scheduler
# runs a tick loop: at every tick it evaluates every intention's condition and
# fires the highest-priority eligible one. It measures the gap between when a
# condition becomes true ("eligibility tick") and when the intention is
# actually executed ("dispatch tick"). That gap is the dispatch latency.
#
# DESIGN DECISIONS
# ----------------
# - A tick is a logical unit of time, not wall-clock. One tick = one scheduler
#   iteration. This keeps the experiment deterministic and measurable.
# - An intention can have a `cooldown` (number of ticks that must pass before
#   it can fire again). Default is 0 (fire every eligible tick).
# - Conditions are arbitrary Python callables supplied by the experiment
#   script. The Flux runtime evaluates them via _eval_ast; the scheduler
#   also accepts plain lambdas for test scenarios that don't need a full
#   program.
# - The scheduler runs in a single thread. There is no preemption between
#   ticks; one intention runs to completion per tick.
# - "Fairness" is measured as the coefficient of variation (CV) of waiting
#   times across all intentions that ran. Low CV = more uniform treatment.

from __future__ import annotations

import statistics
import sys
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))
from tvm import TemporalVM, OutputSink, InputProvider, NIL, FluxRuntimeError


# ---------- data structures ----------

@dataclass
class IntentionSpec:
    """Everything the scheduler needs to know about one intention."""
    name: str
    priority: float          # higher = more important
    condition: Callable[[int], bool]  # tick -> bool
    body: Callable[[int], Any]        # tick -> Any; the "work"
    cooldown: int = 0        # minimum ticks between consecutive firings

    # Internal scheduler state (not set by caller).
    _last_fired: int = field(default=-1, repr=False)
    _eligible_since: int = field(default=-1, repr=False)


@dataclass
class DispatchEvent:
    """One record in the dispatch log."""
    intention_name: str
    eligible_tick: int   # tick when condition first became true
    dispatch_tick: int   # tick when intention began executing
    priority: float

    @property
    def latency(self) -> int:
        return self.dispatch_tick - self.eligible_tick


@dataclass
class SchedulerMetrics:
    """Aggregate metrics computed after the run."""
    total_ticks: int
    total_dispatches: int
    dispatch_log: List[DispatchEvent]
    idle_ticks: int          # ticks where nothing was eligible

    # Per-intention summaries
    per_intention: Dict[str, Dict]

    # Overall latency stats
    mean_latency: float
    median_latency: float
    max_latency: int
    min_latency: int
    latency_cv: float        # coefficient of variation; lower = more uniform

    # Fairness: how evenly did different-priority intentions get CPU?
    fairness_index: float    # Jain's fairness index [0,1]; 1 = perfectly fair

    def report(self) -> str:
        lines = [
            f"Scheduler experiment results",
            f"============================",
            f"Ticks run       : {self.total_ticks}",
            f"Total dispatches: {self.total_dispatches}",
            f"Idle ticks      : {self.idle_ticks} "
            f"({100*self.idle_ticks/max(self.total_ticks,1):.1f}%)",
            f"",
            f"Dispatch latency (ticks from condition-true to execution)",
            f"  mean   : {self.mean_latency:.2f}",
            f"  median : {self.median_latency:.2f}",
            f"  min    : {self.min_latency}",
            f"  max    : {self.max_latency}",
            f"  CV     : {self.latency_cv:.3f}  (lower = more consistent)",
            f"",
            f"Fairness index  : {self.fairness_index:.4f}  (1.0 = perfectly fair)",
            f"",
            f"Per-intention breakdown",
            f"-----------------------",
        ]
        for name, d in sorted(self.per_intention.items(),
                               key=lambda kv: -kv[1]["priority"]):
            lines.append(
                f"  {name:<30}  priority={d['priority']:.2f}  "
                f"runs={d['runs']:4d}  "
                f"mean_lat={d['mean_latency']:.2f}  "
                f"max_lat={d['max_latency']}"
            )
        return "\n".join(lines)


# ---------- the scheduler ----------

class IntentionScheduler:
    """Tick-based, priority-ordered scheduler with condition re-evaluation."""

    def __init__(self, intentions: List[IntentionSpec], *,
                 max_ticks: int = 1000,
                 verbose: bool = False):
        self.intentions = sorted(intentions, key=lambda i: -i.priority)
        self.max_ticks = max_ticks
        self.verbose = verbose

        self._log: List[DispatchEvent] = []
        self._idle = 0

    def run(self) -> SchedulerMetrics:
        for tick in range(self.max_ticks):
            # Evaluate conditions, update eligibility windows.
            eligible = []
            for spec in self.intentions:
                # Respect cooldown: `cooldown` is the *minimum number of ticks
                # that must pass* after a firing before the next one. A cooldown
                # of 1 means "skip at least one tick." A cooldown of 0 means
                # "fire every eligible tick."
                if spec._last_fired >= 0 and spec.cooldown > 0:
                    if tick - spec._last_fired <= spec.cooldown:
                        continue

                cond_true = spec.condition(tick)

                if cond_true:
                    if spec._eligible_since < 0:
                        # First tick the condition is true.
                        spec._eligible_since = tick
                    eligible.append(spec)
                else:
                    # Condition is false — reset eligibility window.
                    spec._eligible_since = -1

            # Pick the highest-priority eligible intention.
            # `eligible` is already sorted (we sorted `self.intentions` once).
            if not eligible:
                self._idle += 1
                if self.verbose:
                    print(f"  tick {tick:4d}: idle")
                continue

            chosen = eligible[0]   # highest priority (list is sorted desc)
            event = DispatchEvent(
                intention_name=chosen.name,
                eligible_tick=chosen._eligible_since,
                dispatch_tick=tick,
                priority=chosen.priority,
            )
            self._log.append(event)

            if self.verbose:
                print(f"  tick {tick:4d}: dispatch {chosen.name!r} "
                      f"(priority={chosen.priority:.2f}, "
                      f"latency={event.latency})")

            # Execute the body.
            chosen.body(tick)

            # Update state.
            chosen._last_fired = tick
            chosen._eligible_since = -1   # reset; condition must become true again

        return self._compute_metrics()

    # ---------- metrics ----------

    def _compute_metrics(self) -> SchedulerMetrics:
        log = self._log
        n = len(log)
        latencies = [e.latency for e in log]

        if not latencies:
            mean_lat = median_lat = max_lat = min_lat = lat_cv = 0.0
        else:
            mean_lat   = statistics.mean(latencies)
            median_lat = statistics.median(latencies)
            max_lat    = max(latencies)
            min_lat    = min(latencies)
            lat_cv     = (statistics.stdev(latencies) / mean_lat
                          if mean_lat > 0 and len(latencies) > 1 else 0.0)

        # Per-intention summary.
        per: Dict[str, Dict] = {}
        for spec in self.intentions:
            events = [e for e in log if e.intention_name == spec.name]
            lats = [e.latency for e in events]
            per[spec.name] = {
                "priority": spec.priority,
                "runs": len(events),
                "mean_latency": statistics.mean(lats) if lats else 0.0,
                "max_latency": max(lats) if lats else 0,
            }

        # Jain's fairness index on run counts.
        counts = [d["runs"] for d in per.values()]
        if counts:
            s = sum(counts)
            sq = sum(c * c for c in counts)
            k = len(counts)
            fairness = (s * s) / (k * sq) if sq > 0 else 1.0
        else:
            fairness = 1.0

        return SchedulerMetrics(
            total_ticks=self.max_ticks,
            total_dispatches=n,
            dispatch_log=log,
            idle_ticks=self._idle,
            per_intention=per,
            mean_latency=mean_lat,
            median_latency=median_lat,
            max_latency=int(max_lat),
            min_latency=int(min_lat),
            latency_cv=lat_cv,
            fairness_index=fairness,
        )


# ---------- Flux-native scheduler ----------

class FluxIntentionScheduler:
    """Wraps the existing TVM to run intentions in a tick loop.

    Compiles and installs a Flux module once; at each tick re-evaluates
    every intention's condition via TVM._eval_ast and dispatches the
    highest-priority eligible one.
    """

    def __init__(self, module, *, max_ticks: int = 1000,
                 rng_seed: int = 42, capture: bool = True,
                 verbose: bool = False):
        self.module = module
        self.max_ticks = max_ticks
        self.verbose = verbose

        sink = OutputSink(capture=capture)
        self.vm = TemporalVM(module, sink=sink, rng_seed=rng_seed)
        self.vm.install(module)
        self.sink = sink

        # Scheduler state per intention.
        self._eligible_since: Dict[str, int] = {}
        self._last_fired: Dict[str, int] = {}

        self._log: List[DispatchEvent] = []
        self._idle = 0

    def run(self) -> SchedulerMetrics:
        intentions = sorted(self.module.intentions, key=lambda i: -i.priority)

        for tick in range(self.max_ticks):
            # Advance the VM's logical clock by one tick.
            self.vm.clock_ns += 1
            self.vm._step += 1

            eligible = []
            for intent in intentions:
                # Evaluate trigger.
                if intent.trigger is not None:
                    try:
                        trig = self.vm._eval_ast(intent.trigger)
                    except FluxRuntimeError:
                        trig = False
                    if not trig:
                        self._eligible_since.pop(intent.name, None)
                        continue

                # Evaluate condition.
                if intent.condition is not None:
                    try:
                        cond = self.vm._eval_ast(intent.condition)
                    except FluxRuntimeError:
                        cond = False
                else:
                    cond = True

                if cond:
                    if intent.name not in self._eligible_since:
                        self._eligible_since[intent.name] = tick
                    eligible.append(intent)
                else:
                    self._eligible_since.pop(intent.name, None)

            if not eligible:
                self._idle += 1
                continue

            # Dispatch highest-priority eligible intention.
            chosen = eligible[0]
            event = DispatchEvent(
                intention_name=chosen.name,
                eligible_tick=self._eligible_since.get(chosen.name, tick),
                dispatch_tick=tick,
                priority=chosen.priority,
            )
            self._log.append(event)

            if self.verbose:
                print(f"  tick {tick:4d}: {chosen.name!r} "
                      f"(lat={event.latency})")

            try:
                self.vm._execute(chosen, args=[])
            except FluxRuntimeError:
                pass

            self._last_fired[chosen.name] = tick
            self._eligible_since.pop(chosen.name, None)

        return self._compute_metrics(intentions)

    def _compute_metrics(self, intentions) -> SchedulerMetrics:
        log = self._log
        latencies = [e.latency for e in log]

        if not latencies:
            mean_lat = median_lat = lat_cv = 0.0
            max_lat = min_lat = 0
        else:
            mean_lat   = statistics.mean(latencies)
            median_lat = statistics.median(latencies)
            max_lat    = max(latencies)
            min_lat    = min(latencies)
            lat_cv     = (statistics.stdev(latencies) / mean_lat
                          if mean_lat > 0 and len(latencies) > 1 else 0.0)

        per: Dict[str, Dict] = {}
        for intent in intentions:
            events = [e for e in log if e.intention_name == intent.name]
            lats = [e.latency for e in events]
            per[intent.name] = {
                "priority": intent.priority,
                "runs": len(events),
                "mean_latency": statistics.mean(lats) if lats else 0.0,
                "max_latency": max(lats) if lats else 0,
            }

        counts = [d["runs"] for d in per.values()]
        if counts:
            s = sum(counts)
            sq = sum(c * c for c in counts)
            k = len(counts)
            fairness = (s * s) / (k * sq) if sq > 0 else 1.0
        else:
            fairness = 1.0

        return SchedulerMetrics(
            total_ticks=self.max_ticks,
            total_dispatches=len(log),
            dispatch_log=log,
            idle_ticks=self._idle,
            per_intention=per,
            mean_latency=mean_lat,
            median_latency=median_lat,
            max_latency=int(max_lat),
            min_latency=int(min_lat),
            latency_cv=lat_cv,
            fairness_index=fairness,
        )
