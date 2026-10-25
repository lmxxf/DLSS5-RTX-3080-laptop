#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
variant="${1:?variant name required}"
warmup="${2:-10}"
iterations="${3:-40}"
phase="$task_root/Development/hip-port/phase5"
if [[ "$variant" == baseline ]]; then
  modules="$task_root/Development/hip-port/phase4/artifacts/selected/modules"
else
  modules="$phase/artifacts/$variant/modules"
fi
DLSS5_AMPERE_WEIGHTS=1 DLSS5_LAB_COMPACT_ALL=1 DLSS5_LAB_C256_900=1 \
  DLSS5_BENCH_SMALL_ONLY=1 DLSS5_BENCH_PROFILE=1 DLSS5_BENCH_DUMP="$phase/artifacts/outputs/$variant" \
  "$phase/artifacts/benchmark_cuda_nn" "${DLSS5_ASSETS:-/home/lmxxf/work/dlss5-assets/native-game-tiled-assets}" \
  "$modules" "$warmup" "$iterations" > "$phase/$variant-bench.log" 2>&1
rg '\[RESULT\]|Validity|GPU  |PROFILE_TOTAL' "$phase/$variant-bench.log"
