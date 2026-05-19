#!/bin/bash
# Simple demo script to run each tool

echo "=== Flux Formatter ==="
echo "Formatting kernel/boot.flux to formatted.flux"
python3 flux_format.py ../kernel/boot.flux --output formatted.flux --indent 2
head -20 formatted.flux

echo -e "\n=== Timeline Visualizer (sample) ==="
python3 timeline_visualizer.py --output sample_timeline.png

echo -e "\n=== Paradox Generator ==="
python3 paradox_generator.py --type prime --seed 12345 --length 3
python3 paradox_generator.py --type causal --seed 42 --loop 7
python3 paradox_generator.py --type self --seed 999

echo "Tools demonstration complete."