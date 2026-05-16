# Nihilo OS — Architecture Sketch

This document describes the *imagined* architecture of Nihilo OS. The
words "kernel," "scheduler," and "service" below are used as shorthand
for the parts a real implementation would need. None of them exists as
running code; what exists is six small Flux programs that illustrate
the vocabulary.

## Layers

```
+--------------------------------------------------------------+
|  user intentions   (commands, sessions, applications)        |
+--------------------------------------------------------------+
|  system intentions (boot, scheduling, authentication)        |
+--------------------------------------------------------------+
|  Flux runtime      (intention dispatch, mosaic, collapse,    |
|                     timeline labels, sensation emission)     |
+--------------------------------------------------------------+
|  hypothetical hardware abstraction (not implemented)         |
+--------------------------------------------------------------+
```

In a real system the bottom two layers would be C or Rust. In this
project the bottom layer is the Flux 1.2 interpreter (`flux_compiler/`
in this repo), which is itself a tree-walking Python VM. The "kernel"
above it is whatever set of intentions you launch first.

## Programs in this repository

### `kernel/boot.flux`

The first intention. It writes a couple of facts into a shared
mosaic (`boot_time`, `timeline`) and emits two sensations
(`inner_voice` and `mental_image`) to announce readiness. In a real
system this is where driver initialization would happen; here it is
purely symbolic.

### `kernel/session.flux`

A single intention that models a "shell." It listens for one user
command, dispatches on the value, emits a response. In Nihilo's model
a shell is not a loop with a prompt — it is one intention with a
condition that says "I should fire whenever the user has an
intention to express." The demo runs the body once; a real
implementation would re-fire the intention whenever its condition
became true.

### `examples/paradox_auth.flux`

Authentication modeled as a recall protocol. The runtime generates
a token (`generate_paradox()`), shows it to the user, and accepts
the same token back as proof of identity. The token generator is
deterministic in this runtime; the demo therefore "succeeds" by
default. In a real system the generator would have cryptographic
properties.

### `examples/causal_mosaic.flux`

Three writes to the same key with different weights, then one read.
The read collapses by max-weight, so it returns the most
probable value. This is the mosaic's whole story in one program.

### `examples/weighted_decision.flux`

A `dist { ... }` literal that describes what a scheduler "thinks"
the right next intention is, plus two collapse operations:
`max_weight` (deterministic) and `weighted_random` (stochastic).
The `weight_of` built-in inspects an individual probability mass.

### `examples/timeline_fork.flux`

Create a branch, switch to it, do work, merge back. The mechanics
are real; the semantics of "merge" in the runtime are symbolic.

## What the runtime actually does

The Flux 1.2 VM gives each program:

- A scope-correct interpreter for `let`, `if`, `while`, `for`,
  function calls, and method calls on structs and mosaics.
- A priority-ordered scheduler that runs every declared intention
  in descending priority order, evaluating `trigger` and `condition`
  before each.
- A pluggable `listen()` that returns scripted input or a fallback.
- A pluggable `send()` that prints to stdout or accumulates events.
- A seeded RNG for `collapse(..., weighted_random)`.
- A label-based timeline model: `current_timeline()`,
  `create_timeline()`, `set_current_timeline()`, `merge_timelines()`.
  Each function does exactly what its name suggests in the simplest
  way that makes the vocabulary consistent.

That is the whole runtime. There is no preemption, no concurrency,
no I/O, no persistence across program runs. Each Flux program is a
single sequential execution that prints sensations and stops.

## What is missing for a "real" Nihilo

If someone wanted to take this further, the implementation gap is
roughly:

- **A real scheduler:** intentions firing on actual events, with
  preemption between them, with budgets and quotas.
- **Persistent mosaic storage:** the in-memory dict needs to be
  durable, journaled, queryable across runs.
- **Concurrency model:** two intentions in different timelines
  writing the same key — what does merge do, and is it deterministic?
- **A sensation transport:** something more than print to stdout.
- **A trust model:** what does it mean for `generate_paradox()`
  to be unforgeable?

None of those is small. Each is a research project on its own. This
repository is a vocabulary exercise, not a blueprint for any of them.
