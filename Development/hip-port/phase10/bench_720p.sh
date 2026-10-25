#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$repo"
phase=Development/hip-port/phase10
mkdir -p "$phase/artifacts/outputs"
g++ -O2 -std=c++17 Development/hip-port/Development/HIP/benchmark_cuda_nn.cpp -ldl -pthread -o "$phase/artifacts/benchmark_cuda_nn.new"
mv "$phase/artifacts/benchmark_cuda_nn.new" "$phase/artifacts/benchmark_cuda_nn"
unset DLSS5_BENCH_SYNC_KERNELS
DLSS5_BENCH_WIDTH=1280 DLSS5_BENCH_GRAPH=0 DLSS5_AMPERE_WEIGHTS=1 \
DLSS5_LAB_COMPACT_ALL=1 DLSS5_LAB_C256_720=1 DLSS5_LAB_C256_900=1 DLSS5_BENCH_SMALL_ONLY=1 \
DLSS5_BENCH_PROFILE=1 DLSS5_BENCH_DUMP="$repo/$phase/artifacts/outputs/selected-720p" \
"$phase/artifacts/benchmark_cuda_nn" "${DLSS5_ASSETS:-/home/lmxxf/work/dlss5-assets/native-game-tiled-assets}" \
"$phase/artifacts/selected/modules" 50 80 > "$phase/selected-720p-bench.log" 2>&1
python "$phase/three_tier_report.py"
