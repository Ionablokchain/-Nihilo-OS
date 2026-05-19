#!/usr/bin/env python3
"""
timeline_visualizer.py - Generate a graph of timeline branches.

Usage:
    timeline_visualizer.py [--input LOGFILE] [--output OUTPUT] [--format png|svg|dot]

The tool reads a timeline event log (created by the Nihilo OS kernel) and
produces a visual graph of timeline creation, switching, and merging.
If no log file is given, it generates a sample graph.
"""

import sys
import argparse
import subprocess
import tempfile
import os

SAMPLE_EVENTS = [
    ('create', 'primary', None),
    ('create', 'timeline_1', 'primary'),
    ('create', 'timeline_2', 'primary'),
    ('switch', 'timeline_1', None),
    ('create', 'timeline_1a', 'timeline_1'),
    ('merge', 'timeline_1a', 'timeline_1'),
    ('switch', 'primary', None),
    ('merge', 'timeline_1', 'primary'),
]

def parse_log(log_content: str) -> list:
    events = []
    for line in log_content.strip().split('\n'):
        parts = line.split()
        if not parts:
            continue
        cmd = parts[0]
        if cmd == 'create' and len(parts) >= 2:
            name = parts[1]
            parent = parts[2] if len(parts) > 2 else None
            events.append(('create', name, parent))
        elif cmd == 'switch' and len(parts) >= 2:
            events.append(('switch', parts[1], None))
        elif cmd == 'merge' and len(parts) >= 2:
            events.append(('merge', parts[1], None))
    return events

def build_dot(events) -> str:
    dot = ['digraph G {', '    rankdir=TB;', '    node [shape=box];']
    nodes = set()
    edges = []
    current = None
    for event in events:
        if event[0] == 'create':
            name, parent = event[1], event[2]
            nodes.add(name)
            if parent:
                edges.append((parent, name))
        elif event[0] == 'switch':
            current = event[1]
        elif event[0] == 'merge':
            src = event[1]
            if current:
                edges.append((src, current))
    for node in nodes:
        dot.append(f'    "{node}";')
    for src, dst in edges:
        dot.append(f'    "{src}" -> "{dst}";')
    dot.append('}')
    return '\n'.join(dot)

def render_dot(dot_source: str, output: str, fmt: str):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
        f.write(dot_source)
        tmp_dot = f.name
    cmd = ['dot', f'-T{fmt}', tmp_dot, '-o', output]
    subprocess.run(cmd, check=True)
    os.unlink(tmp_dot)

def main():
    parser = argparse.ArgumentParser(description='Timeline visualizer')
    parser.add_argument('--input', '-i', help='Timeline log file')
    parser.add_argument('--output', '-o', default='timeline_graph.png', help='Output file')
    parser.add_argument('--format', '-f', default='png', choices=['png', 'svg', 'dot'], help='Output format')
    args = parser.parse_args()

    if args.input:
        with open(args.input, 'r') as f:
            events = parse_log(f.read())
    else:
        events = SAMPLE_EVENTS

    dot_source = build_dot(events)
    if args.format == 'dot':
        with open(args.output, 'w') as f:
            f.write(dot_source)
    else:
        render_dot(dot_source, args.output, args.format)
        print(f"Graph saved to {args.output}")

if __name__ == '__main__':
    main()