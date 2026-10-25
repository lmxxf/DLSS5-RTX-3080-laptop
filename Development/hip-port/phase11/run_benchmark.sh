#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo"
phase=Development/hip-port/phase11
python -m unittest discover -s Development/hip-port/hip -p test_phase11.py
python "$phase/check_half_pack.py"
python -u Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip "$phase/artifacts/selected/modules" > "$phase/rebuild.log" 2>&1
python "$phase/verify_modules.py"
g++ -O2 -std=c++17 Development/hip-port/Development/HIP/benchmark_cuda_nn.cpp -ldl -pthread -o "$phase/artifacts/benchmark_cuda_nn.new"
mv "$phase/artifacts/benchmark_cuda_nn.new" "$phase/artifacts/benchmark_cuda_nn"
run_tag="$(date +%Y%m%dT%H%M%S)"
nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.mem,power.draw,temperature.gpu,utilization.gpu --format=csv,noheader,nounits --loop-ms=500 > "$phase/telemetry-$run_tag.csv" &
telemetry_pid=$!
trap 'kill "$telemetry_pid" 2>/dev/null || true' EXIT
for width in 1280 1600 1920; do
 python "$phase/bench.py" "baseline-repro-$run_tag" --width "$width"
 python "$phase/bench.py" "candidate-repro-$run_tag" --modules "$phase/artifacts/selected/modules" --width "$width"
done
python "$phase/analyze.py"
