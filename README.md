# Nihilo OS – The Operating System Written in Flux

> *"There are no files. No permanent mistakes. Only intentions and timelines."*

**Nihilo OS** is a radical rethinking of operating systems. It is built **from scratch** – no UNIX, no Windows, no POSIX. Every part of the system, from the bootloader to the shell, is written in the **Flux language**.

Flux is a **temporal‑causal language** designed for Nihilo OS. It replaces traditional concepts with **intentions**, **probabilities**, and **parallel timelines**.

---

## What makes it unique?

| Traditional concept | In Nihilo OS |
|---------------------|---------------|
| Files and folders | **Causal Mosaic** – a distributed, timeline‑aware key‑value store. Every write adds a weighted branch; reads collapse to the most probable value. |
| RAM / Storage | **Non‑volatile quantum memory** (conceptual) – every bit can be read, written, and erased simultaneously. In practice: the mosaic persists to disk. |
| Processes / Threads | **Intentions** – declarative units triggered by events, with priorities and conditions. They run when their condition becomes true. |
| Errors (segfault, panic) | **Phantom branches** – mistakes create alternative timelines that can be explored or abandoned. No runtime errors. |
| Passwords / Keys | **Paradox security** – authentication requires reproducing a temporally impossible pattern (e.g., a sequence of prime‑spaced intervals). |
| Commit (git, database) | **Causal hardening** – makes a time interval irreversible, requiring consensus and energy. (Current implementation: symbolic.) |
| Command line / GUI | **Neural interface** (conceptual) – simulated today as a REPL that reads commands from stdin and prints sensations. |

---

## Core Concepts (implemented)

### 1. Intentions
An intention is a named block of code attached to `trigger`, `priority`, and `condition`.  
It does not “run” once – the **scheduler** evaluates all intentions repeatedly and executes the highest‑priority eligible one.

### 2. Causal Mosaic
A persistent key‑value store where each key holds a **weighted set of values**.  
Reading collapses the set (default: `max_weight`). Writes add a new `(value, weight)` branch.

### 3. Timelines
Named parallel realities. You can `create_timeline`, `set_current_timeline`, and `merge_timelines`.  
Each timeline has its own causal history.

### 4. Probabilities & Collapse
Any expression can be a weighted distribution. `collapse(dist, method)` turns belief into commitment.  
Supported methods: `max_weight`, `mean`, `weighted_random`, `first`.

### 5. Paradox Engine
`generate_paradox(type, seed, length)` creates a token from a hardware‑accelerated LFSR (or software fallback).  
`resolve_paradox(type, challenge, response)` verifies it. Used for authentication and creative challenges.

---

## Quick Example – Hello World in Flux

```flux
intention HelloWorld {
    trigger: on_boot()
    priority: 0.9
    execute: {
        send("mental_image", "✨ Welcome to Nihilo OS ✨", 3s);
        let response = listen(user, 10s, "silence");
        if response != "silence" then {
            send("inner_voice", "You said: " ++ response, 1s);
        }
    }
}
This program doesn't “run” – it becomes reality when the scheduler picks it.

Repository Structure (current)
text
nihilo-os/
├── kernel/                 # 100% Flux – the entire OS
│   ├── boot.flux
│   ├── scheduler.flux
│   ├── mosaic_service.flux
│   ├── paradox_engine.flux
│   ├── shell.flux
│   └── main.flux
├── tvm/                    # Temporal Virtual Machine (Python)
│   ├── tvm.py              # bytecode interpreter
│   └── fluxc.py            # Flux compiler (Python, used only at build time)
├── examples/               # Example Flux programs
├── docs/                   # Philosophy, language reference, internals
└── README.md               # This file
Code statistics: Over 90% of the system is written in Flux. The Python layer (TVM + compiler) is a build‑time / development dependency – it will eventually be replaced by a tiny C runtime.

Getting Started (Simulated Environment)
bash
git clone https://github.com/exnihilo/nihilo-os.git
cd nihilo-os

# Compile the kernel into bytecode
python3 tvm/fluxc.py kernel/main.flux -o nihilo.fluxb

# Run the OS in REPL mode
python3 tvm/tvm.py nihilo.fluxb --repl
Once running, type help to see available commands: status, mosaic write/read, timeline list/new/switch, paradox challenge, exit.

Documentation
User Manual – How to use Nihilo OS and write Flux programs.

Flux Language Reference – Complete syntax and semantics.

Internals – Kernel architecture, scheduler, mosaic, paradox engine.

Security Model – Paradox authentication and timeline isolation.

Contributing
We welcome contributions that write more Flux – new services, better scheduler policies, more built‑in functions.
The eventual goal is to remove Python entirely by replacing the TVM with a small C interpreter.

See CONTRIBUTING.md for details.

License
Apache License – see LICENSE.

Nihilo OS is not just an operating system. It is a proof that mistakes are not failures – they are the raw material of parallel universes.

– The Nihilo Collective, anytime, never.
