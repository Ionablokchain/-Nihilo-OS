# Flux – The Temporal Programming Language for Ex Nihilo OS

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/exnihilo/flux)
[![TVM](https://img.shields.io/badge/TVM-compatible-purple)](https://github.com/exnihilo/tvm)

> **"Every line of code is an intention. Every intention creates a world."**

Flux is the first **temporal-causal programming language**, designed exclusively for the *Ex Nihilo* operating system – a world without files, processes, or irreversible errors. Instead of classical execution, Flux programs express **intentions** that **become reality** across parallel **timelines**, with probabilities and paradoxes as first-class citizens.

---

## ✨ Why Flux?

- **No files, no processes** – just intentions and causal mosaics.
- **Mistakes are not errors** – they become parallel timelines you can explore or abandon.
- **Probabilities are persistent** – every value can exist in multiple states with different weights.
- **Paradoxes as security** – authentication through temporally impossible patterns.
- **Causal hardening** – make intervals of time truly irreversible (like `commit` for reality).

## 🚀 Quick Example

```flux
intentie HelloWorld {
    declansare: la_primul_semn_cognitiv()
    prioritate: 0.9
    executa: {
        trimite_senzatie("imagine mentală", 
            "✨ Welcome to a world without files! ✨", 
            3s);
        
        raspuns = asculta_intentie(utilizator, 10s, "silence");
        
        daca raspuns != "silence" : {
            colapseaza(raspuns, "pondere_maximă");
            trimite_senzatie("vorbire interioară", 
                "You said: " ++ raspuns, 
                1s);
        }
    }
}
This program doesn't "run" – it becomes real in the temporal consensus of Ex Nihilo.

📦 Installation
Flux requires Python 3.12+ for the compiler toolchain (the production TVM runs natively on Ex Nihilo hardware).

bash
git clone https://github.com/exnihilo/flux.git
cd flux
pip install -r requirements.txt
sudo make install   # installs fluxc and tvm
Verify installation:

bash
fluxc --version
tvm --version
🧠 Core Concepts
Concept	Description
Intention	An atomic unit of execution that triggers on an event, with priority and condition.
Timeline	A parallel causal branch. Every decision or mistake creates a new timeline.
Probability	A value between 0 and 1 representing existence weight across timelines.
Collapse	The act of turning a probabilistic expression into a concrete value.
Causal Mosaic	A file‑system without files – a sparse temporal matrix.
Causal Hardening	Making a time interval irreversible (expensive, requires consensus).
Paradox	A controlled logical inconsistency used for security or creativity.
📖 Language Guide
Basic Syntax
flux
# Comments start with '#'

x = 42 cu_probabilitate 0.85;   # x is 42 in 85% of timelines

durata = 10s;                   # time units: s, ms, ns, cycles

interval = [1s, 5s];            # closed temporal interval
Intentions
flux
intentie MyIntent {
    declansare: la fiecare 5s
    prioritate: 0.7
    conditie: vid_cauzal.exista()
    executa: {
        # ... actions
    }
}
Control Structures
flux
daca conditie : {
    # then branch
} altfel : {
    # else branch
}

pentru i in [1, 10] : {
    # loop over a collection
}

in_timp_ce conditie : {
    # use with care – may create paradoxes
}
Built‑in Functions
Function	Description
trimite_senzatie(tip, continut, durata?)	Send a cognitive sensation (image, inner voice, tactile)
asculta_intentie(sursa, timeout, fallback)	Listen for user/system intention
colapseaza(expr, metoda)	Collapse probability (pondere_maximă, medie, aleator)
creaza_timeline(din, pondere)	Fork a new timeline
inchegare_cauzala(interval, cost_maxim)	Make time interval irreversible
declanseaza_paradox(tip, interval)	Generate a controlled paradox
Causal Mosaic (Files without files)
flux
mozaic_cauzal user_data {
    componente: matrice_sparsa_temporala(),
    politici: { scriere: "adăugă_ramură", citire: "cea_mai_probabilă" }
}

# Write
user_data.acces(cheie: "last_thought").scrie("I forgot something", pondere=0.9);

# Read
memory = user_data.acces(cheie: "last_thought").citeste();
🛠️ Toolchain
Compiler fluxc
bash
fluxc program.flux                # compiles to program.fluxb
fluxc program.flux --dump-ast     # show abstract syntax tree
fluxc program.flux --dump-bytecode
fluxc program.flux --run          # compile and run on TVM
fluxc repl                        # interactive REPL
Temporal Virtual Machine tvm
bash
tvm program.fluxb --timeline main --prob-threshold 0.5
Debugger fluxdbg
bash
fluxdbg program.fluxb
Debugger commands:

timeline list – show all active timelines

switch <id> – change current timeline

colapseaza prob – force a probability collapse

rescrie [interval] – undo last actions (if not hardened)

📚 Full Documentation
User Manual – complete language reference

Ex Nihilo OS Book – design philosophy

API Reference – built‑ins and standard library

🧪 Examples
Check the examples/ directory:

Example	Description
hello.flux	Basic "Hello World" using cognitive sensations
probabilities.flux	Working with probabilistic values and collapse
mosaic.flux	Using the causal mosaic as persistent storage
paradox_security.flux	Authentication through temporal paradoxes
timeline_fork.flux	Creating and merging timelines
Run an example:

bash
fluxc examples/hello.flux --run
🧰 Requirements for Building from Source
Python 3.12+

antlr4 (optional, for grammar development)

Ex Nihilo hardware (for native execution) – or use the TVM emulator on Linux/macOS/Windows

🤝 Contributing
We welcome contributions! Flux is still a young language – there are many paradoxes waiting to be discovered.

Fork the repository

Create your feature branch (git checkout -b feature/amazing-paradox)

Commit your changes (git commit -m 'Add a new collapse method')

Push to the branch (git push origin feature/amazing-paradox)

Open a Pull Request

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

📄 License
Distributed under the MIT License. See LICENSE for more information.

🙏 Acknowledgements
The Ex Nihilo OS team – for building a world without files

Early adopters who weren't afraid to break causality

Every user who has ever said: "I wish I could undo that mistake"

📞 Contact & Community
Discord Server

Mailing List

GitHub Issues

Flux is not just a programming language – it's a way to reshape reality, one intention at a time.
Ex Nihilo, development team – anytime, never.

text
poti face un redemme pentru nihilo os pentru github
We need to create a README for "Nihilo OS" (presumably Ex Nihilo OS) for GitHub. The user asked: "poti face un redemme pentru nihilo os pentru github" - meaning can you make a README for Nihilo OS for GitHub. Based on previous conversation, the OS is called Ex Nihilo, a fictional operating system built from scratch, with Flux language. So I will produce a README.md for the OS repository. It should be in Romanian? The user asked in Romanian, but README could be in English (standard for GitHub). I'll provide both? The instruction says "poti face un redemme" - probably want English for GitHub but I can make it bilingual or just English. I'll create an English README with a Romanian option or just English. I'll assume English as it's typical. I'll produce a comprehensive README for Ex Nihilo OS.

markdown
# Ex Nihilo OS – The Operating System from Another World

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Flux](https://img.shields.io/badge/Flux-Language-purple)](https://github.com/exnihilo/flux)
[![TVM](https://img.shields.io/badge/TVM-Temporal%20VM-orange)](https://github.com/exnihilo/tvm)
[![Concepts](https://img.shields.io/badge/Concepts-Causality%2C%20Paradoxes%2C%20Timelines-green)](https://github.com/exnihilo/exnihilo)

> **"There are no files. There is no permanent error. Only intentions and timelines."**

**Ex Nihilo** (Latin for "out of nothing") is a revolutionary operating system designed **from scratch** – no UNIX heritage, no Windows legacy, no classical file system. It is built around **temporal causality**, **probabilistic state**, and **user intentions** instead of processes.

In Ex Nihilo, you don't run programs – you **express intentions** that **become real** across parallel timelines. Mistakes are not bugs; they are alternative realities you can explore, merge, or abandon. Security is enforced through **paradoxes** that are impossible to reproduce. And storage is not files but a **causal mosaic** – a sparse matrix of possibilities.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **No Files, No Folders** | Everything is a *flow of intentions* across time. Data exists only as differences between successive timeline states. |
| **Temporal Memory** | Non‑volatile quantum memory – no distinction between RAM and storage. Every bit can be read, written, and erased simultaneously. |
| **Fractal Kernel** | The kernel rewrites itself at boot, analyzing hardware as a puzzle and generating drivers on the fly. |
| **Intentions over Processes** | Instead of threads and processes, Ex Nihilo schedules *durations* – time intervals with their own geometry. |
| **Causal Mosaic (Filesystem)** | A distributed, timeline‑aware structure where every object exists in multiple pasts and futures. Reading collapses probabilities into a single present. |
| **Paradox Security** | Authentication requires reproducing a *temporally impossible event* (e.g., typing a specific sequence of prime‑spaced intervals). Unauthorized access resets the user's timeline. |
| **Causal Hardening** | Make any time interval irreversible – the only way to create permanent, shared reality (like `commit` for existence). |
| **Neural Interface** | No command line, no GUI. The OS reads thought patterns (via wave‑particle interference) and responds with sensations, colors, or subsonic tones. |

---

## 🧠 Core Concepts

### Intention
An atomic declarative unit: *"Under certain conditions, with a given probability, let this sequence of actions happen."* Intentions never terminate – they either **realize** or become **phantom branches**.

### Timeline
A parallel causal branch. Every decision or mistake creates a new timeline. All timelines coexist in the **causal mosaic**.

### Probability
Any value or state can be expressed as a probability (0..1). For example, `x = 0.8` means "x exists in 80% of relevant timelines". Values collapse when concrete output is needed.

### Collapse
The act of turning a probabilistic expression into a concrete result (max weight, average, or random).

### Causal Mosaic
The replacement for a file system. It stores **components** (not files) indexed by keys, with policies for writing (add a branch, never overwrite) and reading (most probable, all, random).

### Paradox
A controlled logical inconsistency. Used for:
- **Security** – authentication through irreproducible events.
- **Creativity** – generate unique temporal signatures.
- **Education** – demonstrate causality without harm.

### Causal Hardening
An expensive, consensus‑requiring operation that makes a time interval **irreversible** – even for the user who created it.

---

## 🚀 Quick Start

Ex Nihilo requires **quantum‑temporal hardware**. However, you can experience a **simulated environment** using the TVM (Temporal Virtual Machine) on classical computers.

### Simulated Environment (Linux/macOS/Windows)

```bash
git clone https://github.com/exnihilo/exnihilo.git
cd exnihilo/tvm
make
./tvm --demo
This starts a REPL where you can type intentions and see timelines branch and collapse.

First Intention
flux
intentie Hello {
    declansare: la_primul_semn_cognitiv()
    executa: {
        trimite_senzatie("imagine mentală", "✨ Welcome to Ex Nihilo ✨", 3s);
    }
}
Save as hello.flux, then:

bash
fluxc hello.flux --run
You will feel the message as an inner image and a soft tactile vibration.

📖 Documentation
Document	Description
User Manual	Complete guide to using Ex Nihilo (intentions, mosaic, paradoxes)
Flux Language Reference	Syntax and semantics of the Flux programming language
Internals	Kernel architecture, temporal scheduler, causal hardening protocol
Security Model	Paradox‑based authentication, timeline isolation, consensus
FAQ	Common questions about causality, mistakes, and real‑world hardware
🛠️ Building from Source (for Quantum Hardware)
Note: Full Ex Nihilo requires a quantum‑temporal processor. The source tree includes hardware description files (Chisel/Verilog) for FPGA emulation.

bash
git clone https://github.com/exnihilo/exnihilo.git
cd exnihilo/hw
make fpga-image   # generates bitstream for Xilinx/Altera
make load         # loads onto supported FPGA board
For the software toolchain (compiler, TVM, debugger) on classical machines, see the Flux repository.

🧪 Examples
Example	Location	What it demonstrates
hello.flux	examples/	Basic intention with cognitive sensation
timeline_fork.flux	examples/	Creating and switching between timelines
causal_mosaic.flux	examples/	Storing and retrieving data without files
paradox_auth.flux	examples/	Using a paradox as a password
hardening.flux	examples/	Making a time interval irreversible
Run any example:

bash
fluxc examples/timeline_fork.flux --run
🤝 Contributing
Ex Nihilo is an open source project. We welcome contributors who are not afraid to rethink computing from the ground up.

Areas where help is needed:

Temporal scheduler – optimising the selection of intentions.

Causal garbage collection – pruning abandoned timelines without breaking consensus.

Paradox resolution algorithms – new methods for collapsing inconsistencies.

Neural interface drivers – adapting EEG/ECoG hardware to Flux sensations.

Documentation – more tutorials, translations, and examples.

Please read CONTRIBUTING.md before submitting a pull request.

📄 License
Distributed under the MIT License. See LICENSE for details.

The hardware designs are released under the CERN OHL v2.0.

🙏 Acknowledgements
The Ex Nihilo team – for daring to ask "What if we started over?"

Early testers who willingly broke causality for science.

Every computer scientist who ever wrote rm -rf / and wished for an undo.

📞 Contact
Discord: Ex Nihilo Community

Mailing list: dev@exnihilo.org

Issues: GitHub Issues

Ex Nihilo is not just an operating system. It is a proof that mistakes are not failures – they are the raw material of parallel universes.
– The Ex Nihilo Collective, anytime, never.
