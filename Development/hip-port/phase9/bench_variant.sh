#!/usr/bin/env bash
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
variant="${1:?variant name required}"
warmup="${2:-10}"
iterations="${3:-40}"
phase="$task_root/Development/hip-port/phase9"
if [[ "$variant" == baseline* || "$variant" == graph-only ]]; then
  modules="$task_root/Development/hip-port/phase8/artifacts/selected/modules"
else
  module_variant="${variant%-repeat}"
  case "$variant" in v-graph) module_variant=v-bridge;; q63-graph) module_variant=q63-lowreg;; q63-fast-graph) module_variant=q63-fast;; q31-graph) module_variant=q31-lowreg;; q63-policy-graph) module_variant=q63-policy;; q63-peel-graph) module_variant=q63-peel;; selected-graph) module_variant=selected;; esac
  modules="$phase/artifacts/$module_variant/modules"
fi
date --iso-8601=seconds > "$phase/$variant-time.txt"
DLSS5_BENCH_GRAPH="${DLSS5_BENCH_GRAPH:-0}" DLSS5_AMPERE_WEIGHTS=1 DLSS5_LAB_COMPACT_ALL=1 DLSS5_LAB_C256_900=1 \
  DLSS5_BENCH_SMALL_ONLY=1 DLSS5_BENCH_PROFILE=1 DLSS5_BENCH_DUMP="$phase/artifacts/outputs/$variant" \
  "$phase/artifacts/benchmark_cuda_nn" "${DLSS5_ASSETS:-/home/lmxxf/work/dlss5-assets/native-game-tiled-assets}" \
  "$modules" "$warmup" "$iterations" > "$phase/$variant-bench.log" 2>&1
date --iso-8601=seconds >> "$phase/$variant-time.txt"
rg '\[RESULT\]|Validity|GPU  |PROFILE_TOTAL' "$phase/$variant-bench.log"
