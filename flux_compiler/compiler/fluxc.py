#!/usr/bin/env python3
"""fluxc.py - The Flux compiler / runner.

Usage:
    fluxc <file.flux> [--dump] [--run] [--seed N]

  --dump     Print the compiled bytecode.
  --run      Execute the program on the Temporal VM.
  --seed N   Seed the VM's random number generator (for reproducible runs).
"""
import argparse
import sys

from flux_lexer import Lexer, LexerError
from flux_parser import Parser, ParseError
from flux_semantic import SemanticAnalyzer
from flux_codegen import BytecodeGenerator, disassemble
from tvm import TemporalVM, FluxRuntimeError


def compile_source(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    sem = SemanticAnalyzer()
    diagnostics = sem.analyze(program)
    return program, diagnostics


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="fluxc")
    ap.add_argument("file")
    ap.add_argument("--dump", action="store_true", help="print bytecode")
    ap.add_argument("--run", action="store_true", help="execute on the TVM")
    ap.add_argument("--seed", type=int, default=None, help="VM RNG seed")
    ap.add_argument("--quiet", action="store_true", help="hide warnings")
    args = ap.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"cannot read {args.file}: {e}", file=sys.stderr)
        return 2

    try:
        program, diagnostics = compile_source(source)
    except LexerError as e:
        print(f"lexer error: {e}", file=sys.stderr)
        return 1
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 1

    errors = [d for d in diagnostics if d.kind == "error"]
    warnings = [d for d in diagnostics if d.kind == "warning"]
    if not args.quiet:
        for w in warnings:
            print(f"warning: {w.message}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e.message}", file=sys.stderr)
        return 1

    module = BytecodeGenerator().generate(program)

    if args.dump:
        print(disassemble(module))

    if args.run:
        vm = TemporalVM(module, rng_seed=args.seed)
        vm.install(module)
        try:
            vm.run_module()
        except FluxRuntimeError as e:
            print(f"runtime error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
