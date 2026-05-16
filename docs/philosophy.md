# Nihilo OS — Philosophy

## What this document is

A speculative design exercise. Nihilo OS is not a working operating
system. It is a set of programs and notes that imagine what an OS
might look like if some of the foundational choices were different.
The Flux programs in this repository compile and run on the Flux 1.2
interpreter, but only as illustrations of the ideas described here.
They do not boot hardware, schedule real processes, or persist data.

## The starting question

Modern operating systems are descended from a single design tradition:
processes that compete for CPU time, files that persist data as
named byte sequences, system calls that mediate every interaction with
the kernel. The tradition is older than most of the hardware it runs
on. It works. It also constrains the kinds of programs people write.

Nihilo asks: **if the abstractions were different, what would programs
look like?** Not "what would be faster" — that's a different question.
What would *change about how we describe what a computer is doing*?

## Four substitutions

Nihilo replaces four traditional concepts with deliberately strange
alternatives. Each is a thought experiment, not an engineering
proposal.

### 1. Intentions, not processes

A traditional process is a unit of execution. It has memory, a stack,
a scheduler entry, and is preempted by the kernel. An intention is a
unit of *purpose*: a named block of code attached to a trigger, a
priority, and a condition. It runs when its condition is true and
its priority allows it. It has no inherent lifetime.

The substitution is more semantic than technical. A scheduler over
intentions could be implemented as a priority queue, no different
from a process scheduler. The change is in how programs are written:
"do X every time Y happens, weighted against the rest" rather than
"start a process, wait for it, kill it."

### 2. Mosaic, not filesystem

A traditional file is a named byte sequence with a single current
value. Writes overwrite; reads return the latest. A mosaic is a
named map whose values are *weighted distributions*. Writes add new
branches; reads collapse the distribution by a configurable method
(max-weight, mean, weighted-random, first).

The change is in what "remembering" means. A mosaic remembers all
versions, weighted by confidence. The most likely value is recovered
by default, but the others are still there, and a different
collapse method gives a different answer.

### 3. Distributions, not values

In a traditional language, `x = 0.7` binds `x` to the number 0.7.
In Flux, `let p = dist { "heads": 0.6, "tails": 0.4 }` binds `p` to
a *belief* about a coin. The collapse operator turns belief into
commitment: `collapse(p, weighted_random)` samples one outcome,
`collapse(p, max_weight)` picks the most likely one. The shape of
the value matches the shape of the question.

### 4. Timelines, not a single clock

A traditional OS has one clock. Time moves forward; the past is
fixed. Nihilo's vocabulary admits multiple named *timelines*, each
of which has its own forward direction. `create_timeline()`,
`set_current_timeline()`, and `merge_timelines()` are the verbs.

This is the most fictional of the four. In the demo runtime, a
timeline is just a label; switching changes which label is current,
and merging discards a label. There is no causal-merge algorithm in
the implementation. Whether such an algorithm could exist for any
useful semantics is an open question that this project does not
attempt to answer.

## What is honest

The Flux programs in `kernel/` and `examples/` compile and run.
They use only the vocabulary that the Flux 1.2 interpreter actually
supports: `intention`, `send`, `listen`, `collapse`, `dist`,
`causal_mosaic`, `current_timeline`, `create_timeline`, and the
documented built-ins.

The hardware design in `hardware/` is real Verilog. It does not
"accelerate paradoxes." It generates pseudo-random tokens by
indexing a small prime table with an LFSR. The file calls this a
"paradox accelerator" because that is the vocabulary of the project,
but the circuit is mundane.

## What is not honest

This is a small list of things the previous design document (now
removed) claimed and which do not exist anywhere in this repository:
quantum memory, neural interfaces, fractal kernel, temporal
scheduler in any meaningful sense, paradox engine with causal
properties, FPGA bitstreams, debugger, optimizer, full standard
library, tests, CI. Some of those are interesting things to think
about. None of them is implemented.

## Inspirations

The four substitutions did not come from nowhere.

- **Intentions over processes** echoes early work on agent systems
  and behaviour trees, and shares its mood with the
  ambient-computing literature.
- **Mosaic over filesystem** is a small step from databases that
  retain history (Datomic, Noms) and from probabilistic programming.
- **Distributions as first-class values** is the central idea of
  probabilistic programming (Pyro, Stan, Church, Anglican).
- **Timelines** owe a debt to revision control (each commit is a
  micro-timeline), to functional reactive programming, and — more
  loosely — to physics-of-computation speculation that has been
  rehearsed in fiction for fifty years.

Nihilo combines them into one vocabulary. The combination is the
contribution, such as it is.

## What this project is for

Reading. Talking about. Maybe stealing one or two ideas for a real
system. Not running production workloads. Not booting on hardware.
Not claiming any of the things the title or vocabulary might suggest.

If after reading the Flux programs you find yourself thinking
"hmm, what if a real scheduler did that," then the project has
done its job.
