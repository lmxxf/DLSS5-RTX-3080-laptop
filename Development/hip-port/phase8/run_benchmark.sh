#!/usr/bin/env bash
set -euo pipefail
unset DLSS5_BENCH_WIDTH
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo"
phase=Development/hip-port/phase8
python "$phase/check_primitives.py"
mkdir -p "$phase/artifacts/outputs"
python -u Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip "$phase/artifacts/selected/modules" > "$phase/selected-full-rebuild.log" 2>&1
g++ -O2 -std=c++17 Development/hip-port/Development/HIP/benchmark_cuda_nn.cpp -ldl -pthread -o "$phase/artifacts/benchmark_cuda_nn"
for variant in baseline-final selected; do bash "$phase/bench_variant.sh" "$variant" 50 80; done
python "$phase/analyze.py"
python "$phase/count_ptx.py"
