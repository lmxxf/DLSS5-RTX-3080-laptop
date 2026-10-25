#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
# Fresh run names are mandatory: bench.py refuses to overwrite archived evidence.
p=Development/hip-port/phase13
stamp="${1:-retest-$(date +%Y%m%d-%H%M%S)}"
for w in 1280 1600 1920; do
 python3 "$p/bench.py" "baseline-$stamp-forward" --width "$w"
 python3 "$p/bench.py" "$stamp-forward" --width "$w" --modules "$p/artifacts/selected/modules"
done
for w in 1280 1600 1920; do
 python3 "$p/bench.py" "$stamp-reverse" --width "$w" --modules "$p/artifacts/selected/modules"
 python3 "$p/bench.py" "baseline-$stamp-reverse" --width "$w"
done
python3 "$p/analyze.py"

python3 "$p/final_quality.py" --forward "$stamp-forward" --reverse "$stamp-reverse" --baseline "baseline-$stamp-forward"
