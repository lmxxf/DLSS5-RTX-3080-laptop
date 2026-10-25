#!/usr/bin/env bash
set -euo pipefail
unset DLSS5_BENCH_WIDTH
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo"
phase=Development/hip-port/phase7
python "$phase/check_primitives.py"
python -u Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip "$phase/artifacts/step12/modules" > "$phase/step12-build.log" 2>&1
python -u "$phase/build_variant.py" hoist --parent "$phase/artifacts/step12/modules" --modules c32-wave1-fast --hoist-input > "$phase/hoist-build.log" 2>&1
mkdir -p "$phase/artifacts/outputs"
g++ -O2 -std=c++17 Development/hip-port/Development/HIP/benchmark_cuda_nn.cpp -ldl -pthread -o "$phase/artifacts/benchmark_cuda_nn"
for variant in baseline step12 hoist; do bash "$phase/bench_variant.sh" "$variant" 50 80; done
python "$phase/analyze.py"
python "$phase/count_ptx.py"
