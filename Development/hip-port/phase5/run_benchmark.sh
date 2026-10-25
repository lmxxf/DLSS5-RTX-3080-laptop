#!/usr/bin/env bash
set -euo pipefail
unset DLSS5_BENCH_WIDTH
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
hip_root="$task_root/Development/hip-port"
phase="$hip_root/phase5"
warmup="${1:-50}"
iterations="${2:-80}"
python "$hip_root/hip/build_sm86_modules.py" "$hip_root/hip" "$phase/artifacts/selected/modules" > "$phase/build.log" 2>&1
python "$phase/check_layout.py" > "$phase/layout-validation.log" 2>&1
g++ -O2 -std=c++17 "$hip_root/Development/HIP/benchmark_cuda_nn.cpp" -ldl -pthread -o "$phase/artifacts/benchmark_cuda_nn"
bash "$phase/bench_variant.sh" baseline "$warmup" "$iterations"
bash "$phase/bench_variant.sh" selected "$warmup" "$iterations"
python "$phase/analyze.py" --warmup "$warmup" --iterations "$iterations"
