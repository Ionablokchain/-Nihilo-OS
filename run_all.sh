#!/usr/bin/env bash
# run_all.sh -- Compile and run every Flux program in this repository.
#
# This script demonstrates that the Flux files in kernel/ and examples/
# actually compile and run on the bundled Flux 1.2 interpreter. If you
# run it and see a clean run for each file, the demos work. If you see
# any errors, the project has drifted and the documentation no longer
# matches the code.

set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
FLUXC="$HERE/flux_compiler/compiler/fluxc.py"

if [[ ! -f "$FLUXC" ]]; then
    echo "error: Flux compiler not found at $FLUXC" >&2
    exit 2
fi

run_one() {
    local file="$1"
    echo "===================================================="
    echo "$file"
    echo "----------------------------------------------------"
    python3 "$FLUXC" "$file" --run --seed 1 --quiet
}

for f in "$HERE"/kernel/*.flux "$HERE"/examples/*.flux; do
    run_one "$f"
done

echo "===================================================="
echo "all programs ran successfully"
