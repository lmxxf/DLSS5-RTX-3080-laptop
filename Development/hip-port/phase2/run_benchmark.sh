#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
hip_root="$task_root/Development/hip-port"
phase_dir="$hip_root/phase2"
artifacts="$phase_dir/artifacts"
assets="${DLSS5_ASSETS:-/home/lmxxf/work/dlss5-assets/native-game-tiled-assets}"
warmup="${1:-50}"
iterations="${2:-80}"
mkdir -p "$artifacts/outputs"
python "$hip_root/hip/build_sm86_modules.py" "$hip_root/hip" "$artifacts/modules"
python "$phase_dir/check_primitives.py" > "$phase_dir/primitives.log" 2>&1
g++ -O2 -std=c++17 "$hip_root/Development/HIP/benchmark_cuda_nn.cpp" -ldl -pthread -o "$artifacts/benchmark_cuda_nn"
for mode in phase1 phase2; do
  if [[ "$mode" == phase1 ]]; then
    module_dir="$hip_root/phase1/artifacts/f16-modules"
    layout=0
  else
    module_dir="$artifacts/modules"
    layout=1
  fi
  DLSS5_AMPERE_WEIGHTS="$layout" DLSS5_BENCH_SMALL_ONLY=1 DLSS5_BENCH_PROFILE=1 \
    DLSS5_BENCH_DUMP="$artifacts/outputs/$mode" \
    "$artifacts/benchmark_cuda_nn" "$assets" "$module_dir" "$warmup" "$iterations" \
    > "$phase_dir/$mode-bench.log" 2>&1
  cp "$phase_dir/$mode-bench.log" "$artifacts/outputs/$mode-bench.log"
done
python "$phase_dir/analyze.py" "$artifacts/outputs/phase1" "$artifacts/outputs/phase2" "$phase_dir"
