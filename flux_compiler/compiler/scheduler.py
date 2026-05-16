# scheduler.py - Priority scheduler with aging, condition re-evaluation, metrics.
#
# v2: adds priority aging (anti-starvation) and FluxIntentionScheduler
# that drives the real TVM for condition evaluation.
#
# AGING MODEL
# -----------
# Every tick that an intention is eligible but not dispatched, its
# *effective* priority increases by `aging_rate`. The effective priority
# is used only for the current dispatch decision; the base priority is
# never modified. When an intention fires, its aging accumulator resets
# to zero. This prevents high-frequency high-priority intentions from
# permanently starving low-priority ones.
#
# Effective priority formula:
#   effective = base_priority + aging_ticks * aging_rate
# where aging_ticks = current_tick - eligible_since (ticks waiting).
#
# STARVATION METRIC
# -----------------
# An intention is "starved" on tick T if:
#   - its condition has been continuously true for >= STARVATION_THRESHOLD ticks
#   - it has not been dispatched in that window
# We record the maximum consecutive wait (the "starvation depth") per intention.

from __future__ import annotations

import statistics
import sys, os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))

STARVATION_THRESHOLD = 10   # ticks before we call something "starved"


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IntentionSpec:
    """Everything the scheduler needs about one intention."""
    name: str
    priority: float             # base priority; never modified
    condition: Callable[[int], bool]
    body: Callable[[int], Any]
    cooldown: int = 0           # min ticks between consecutive firings
    aging_rate: float = 0.0     # priority gain per tick of waiting

    # Internal scheduler state.
    _last_fired: int       = field(default=-1,   repr=False)
    _eligible_since: int   = field(default=-1,   repr=False)
    _aging_accum: float    = field(default=0.0,  repr=False)


@dataclass
class DispatchEvent:
    intention_name: str
    eligible_tick: int
    dispatch_tick: int
    base_priority: float
    effective_priority: float   # base + aging at dispatch time

    @property
    def latency(self) -> int:
        return self.dispatch_tick - self.eligible_tick


@dataclass
class SchedulerMetrics:
    total_ticks: int
    total_dispatches: int
    dispatch_log: List[DispatchEvent]
    idle_ticks: int
    per_intention: Dict[str, Dict]

    mean_latency: float
    median_latency: float
    max_latency: int
    min_latency: int
    latency_cv: float

    fairness_index: float       # Jain's index on run counts
    starvation_events: int      # times any intention waited >= threshold

    def report(self, show_aging: bool = False) -> str:
        lines = [
            f"Scheduler experiment results",
            f"============================",
            f"Ticks run          : {self.total_ticks}",
            f"Total dispatches   : {self.total_dispatches}",
            f"Idle ticks         : {self.idle_ticks} "
            f"({100*self.idle_ticks/max(self.total_ticks,1):.1f}%)",
            f"Starvation events  : {self.starvation_events} "
            f"(waited >= {STARVATION_THRESHOLD} ticks)",
            f"",
            f"Dispatch latency (ticks from condition-true to execution)",
            f"  mean   : {self.mean_latency:.2f}",
            f"  median : {self.median_latency:.2f}",
            f"  min    : {self.min_latency}",
            f"  max    : {self.max_latency}",
            f"  CV     : {self.latency_cv:.3f}",
            f"",
            f"Fairness index  : {self.fairness_index:.4f}  (1.0 = perfectly fair)",
            f"",
            f"Per-intention breakdown",
            f"-----------------------",
        ]
        for name, d in sorted(self.per_intention.items(),
                               key=lambda kv: -kv[1]["priority"]):
            aging_str = ""
            if show_aging and d.get("aging_rate", 0) > 0:
                aging_str = f"  aging={d['aging_rate']}"
            lines.append(
                f"  {name:<30}  pri={d['priority']:.2f}"
                f"  runs={d['runs']:4d}"
                f"  mean_lat={d['mean_latency']:6.2f}"
                f"  max_lat={d['max_latency']:4d}"
                f"  starved={d['starvation_events']:3d}"
                + aging_str
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# The scheduler
# ─────────────────────────────────────────────────────────────────────────────

class IntentionScheduler:
    """Tick-based priority scheduler with optional aging."""

    def __init__(self, intentions: List[IntentionSpec], *,
                 max_ticks: int = 1000,
                 verbose: bool = False):
        # Sort by base priority descending; aging changes effective priority
        # each tick, so we re-sort eligible list at runtime.
        self.intentions = list(intentions)
        self.max_ticks = max_ticks
        self.verbose = verbose

        self._log: List[DispatchEvent] = []
        self._idle = 0
        self._starvation_events = 0
        # per-intention starvation counter
        self._starv: Dict[str, int] = {s.name: 0 for s in intentions}

    def run(self) -> SchedulerMetrics:
        for tick in range(self.max_ticks):
            eligible: List[Tuple[float, IntentionSpec]] = []   # (eff_pri, spec)

            for spec in self.intentions:
                # Cooldown gate.
                if spec._last_fired >= 0 and spec.cooldown > 0:
                    if tick - spec._last_fired <= spec.cooldown:
                        continue

                cond_true = spec.condition(tick)

                if cond_true:
                    if spec._eligible_since < 0:
                        spec._eligible_since = tick

                    waiting = tick - spec._eligible_since
                    # Aging: effective priority grows with wait time.
                    eff_pri = spec.priority + waiting * spec.aging_rate
                    spec._aging_accum = waiting * spec.aging_rate

                    # Starvation detection.
                    if waiting >= STARVATION_THRESHOLD:
                        self._starvation_events += 1
                        self._starv[spec.name] = self._starv.get(spec.name, 0) + 1

                    eligible.append((eff_pri, spec))
                else:
                    spec._eligible_since = -1
                    spec._aging_accum = 0.0

            if not eligible:
                self._idle += 1
                if self.verbose:
                    print(f"  tick {tick:4d}: idle")
                continue

            # Pick highest *effective* priority.
            eligible.sort(key=lambda t: -t[0])
            eff_pri, chosen = eligible[0]

            event = DispatchEvent(
                intention_name=chosen.name,
                eligible_tick=chosen._eligible_since,
                dispatch_tick=tick,
                base_priority=chosen.priority,
                effective_priority=eff_pri,
            )
            self._log.append(event)

            if self.verbose:
                aging_delta = eff_pri - chosen.priority
                aging_str = f" +{aging_delta:.3f}" if aging_delta > 0 else ""
                print(f"  tick {tick:4d}: {chosen.name!r:20s} "
                      f"eff={eff_pri:.3f}{aging_str}  lat={event.latency}")

            chosen.body(tick)
            chosen._last_fired = tick
            chosen._eligible_since = -1
            chosen._aging_accum = 0.0

        return self._compute_metrics()

    def _compute_metrics(self) -> SchedulerMetrics:
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
        for spec in self.intentions:
            events = [e for e in log if e.intention_name == spec.name]
            lats   = [e.latency for e in events]
            per[spec.name] = {
                "priority":          spec.priority,
                "aging_rate":        spec.aging_rate,
                "runs":              len(events),
                "mean_latency":      statistics.mean(lats) if lats else 0.0,
                "max_latency":       max(lats) if lats else 0,
                "starvation_events": self._starv.get(spec.name, 0),
            }

        counts = [d["runs"] for d in per.values()]
        s  = sum(counts)
        sq = sum(c*c for c in counts)
        k  = len(counts)
        fairness = (s*s) / (k*sq) if sq > 0 else 1.0

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
            starvation_events=self._starvation_events,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Flux-native scheduler  (Part C)
# ─────────────────────────────────────────────────────────────────────────────

class FluxIntentionScheduler:
    """Wraps the TVM: re-evaluates Flux conditions each tick, dispatches
    the highest-effective-priority eligible intention.

    Aging is supported: pass aging_rates={intention_name: rate}.
    """

    def __init__(self, module, *,
                 max_ticks: int = 1000,
                 rng_seed: int = 42,
                 capture: bool = True,
                 verbose: bool = False,
                 aging_rates: Optional[Dict[str, float]] = None):
        from tvm import TemporalVM, OutputSink, InputProvider, FluxRuntimeError
        self._FluxRuntimeError = FluxRuntimeError

        self.module = module
        self.max_ticks = max_ticks
        self.verbose = verbose
        self.aging_rates = aging_rates or {}

        sink = OutputSink(capture=capture)
        self.vm = TemporalVM(module, sink=sink, rng_seed=rng_seed)
        self.vm.install(module)
        self.sink = sink

        # Per-intention scheduler state.
        self._eligible_since: Dict[str, int] = {}
        self._last_fired: Dict[str, int] = {}
        self._aging_accum: Dict[str, float] = {}
        self._starv: Dict[str, int] = {}
        self._starvation_events = 0

        self._log: List[DispatchEvent] = []
        self._idle = 0

    def run(self) -> SchedulerMetrics:
        intentions = sorted(self.module.intentions, key=lambda i: -i.priority)

        for tick in range(self.max_ticks):
            self.vm.clock_ns += 1
            self.vm._step  += 1

            eligible: List[Tuple[float, Any]] = []

            for intent in intentions:
                # Trigger check.
                if intent.trigger is not None:
                    try:
                        trig = self.vm._eval_ast(intent.trigger)
                    except self._FluxRuntimeError:
                        trig = False
                    if not trig:
                        self._eligible_since.pop(intent.name, None)
                        continue

                # Condition check.
                cond = True
                if intent.condition is not None:
                    try:
                        cond = self.vm._eval_ast(intent.condition)
                    except self._FluxRuntimeError:
                        cond = False

                if cond:
                    if intent.name not in self._eligible_since:
                        self._eligible_since[intent.name] = tick
                    waiting = tick - self._eligible_since[intent.name]
                    rate = self.aging_rates.get(intent.name, 0.0)
                    eff_pri = intent.priority + waiting * rate

                    if waiting >= STARVATION_THRESHOLD:
                        self._starvation_events += 1
                        self._starv[intent.name] = \
                            self._starv.get(intent.name, 0) + 1

                    eligible.append((eff_pri, intent))
                else:
                    self._eligible_since.pop(intent.name, None)

            if not eligible:
                self._idle += 1
                continue

            eligible.sort(key=lambda t: -t[0])
            eff_pri, chosen = eligible[0]

            event = DispatchEvent(
                intention_name=chosen.name,
                eligible_tick=self._eligible_since.get(chosen.name, tick),
                dispatch_tick=tick,
                base_priority=chosen.priority,
                effective_priority=eff_pri,
            )
            self._log.append(event)

            if self.verbose:
                delta = eff_pri - chosen.priority
                aging_str = f" +{delta:.3f}" if delta > 0 else ""
                print(f"  tick {tick:4d}: {chosen.name!r:20s} "
                      f"eff={eff_pri:.3f}{aging_str}  lat={event.latency}")

            try:
                self.vm._execute(chosen, args=[])
            except self._FluxRuntimeError as e:
                if self.verbose:
                    print(f"    [runtime error: {e}]")

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
            lats   = [e.latency for e in events]
            per[intent.name] = {
                "priority":          intent.priority,
                "aging_rate":        self.aging_rates.get(intent.name, 0.0),
                "runs":              len(events),
                "mean_latency":      statistics.mean(lats) if lats else 0.0,
                "max_latency":       max(lats) if lats else 0,
                "starvation_events": self._starv.get(intent.name, 0),
            }

        counts = [d["runs"] for d in per.values()]
        s  = sum(counts)
        sq = sum(c*c for c in counts)
        k  = len(counts)
        fairness = (s*s)/(k*sq) if sq > 0 else 1.0

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
            starvation_events=self._starvation_events,
        )
