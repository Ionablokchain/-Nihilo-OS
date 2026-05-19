#!/usr/bin/env python3
"""
flux_format.py - Flux code formatter.

Usage:
    flux_format.py <input.flux> [--output OUTPUT] [--indent N]

Options:
    --output OUTPUT   Write formatted code to OUTPUT (default: stdout)
    --indent N        Number of spaces per indent level (default: 4)
"""

import sys
import re
import argparse

def format_flux(code: str, indent_size: int = 4) -> str:
    lines = code.split('\n')
    result = []
    indent = 0
    for line in lines:
        stripped = line.strip()
        # Decrease indent before closing braces
        if stripped in ('}', '};') or stripped.startswith('}'):
            indent = max(0, indent - 1)
        # Add current indentation
        result.append(' ' * (indent * indent_size) + stripped)
        # Increase indent after opening braces
        if stripped.endswith('{') or (stripped.endswith('{') and not stripped.endswith('}}')):
            indent += 1
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(description='Flux code formatter')
    parser.add_argument('input', help='Input .flux file')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--indent', type=int, default=4, help='Indent spaces (default: 4)')
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        source = f.read()
    formatted = format_flux(source, args.indent)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(formatted)
    else:
        print(formatted)

if __name__ == '__main__':
    main()