#!/usr/bin/env bash
set -euo pipefail
unset DLSS5_BENCH_WIDTH
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$task_root"
hip_root="$task_root/Development/hip-port"
phase="$hip_root/phase3"
artifacts="$phase/artifacts"
assets="${DLSS5_ASSETS:-/home/lmxxf/work/dlss5-assets/native-game-tiled-assets}"
warmup="${1:-50}"
iterations="${2:-80}"
python "$hip_root/hip/build_sm86_modules.py" "$hip_root/hip" "$artifacts/modules"
python "$phase/build_c32_control.py" > "$phase/c32-control-build.log" 2>&1
python "$phase/check_primitives.py" > "$phase/primitives.log" 2>&1
g++ -O2 -std=c++17 "$hip_root/Development/HIP/benchmark_cuda_nn.cpp" -ldl -pthread -o "$artifacts/benchmark_cuda_nn"
python - "$artifacts" <<'PY'
from pathlib import Path
import shutil,sys
p=Path(sys.argv[1]);dst=p/'deferred-shared-q';dst.mkdir(exist_ok=True)
for f in (p/'modules').glob('*.hsaco'):shutil.copy2(f,dst/f.name)
shutil.copy2(p/'c32-control-build/c32-wave1-fast.hsaco',dst/'c32-wave1-fast.hsaco')
shutil.copy2(p/'modules/AMPERE_WEIGHTS_V2',dst/'AMPERE_WEIGHTS_V2')
PY
for mode in phase2 shared-q phase3; do
  compact=1
  c256=1
  if [[ "$mode" == phase2 ]]; then
    modules="$hip_root/phase2/artifacts/modules"
    compact=0
    c256=0
    prefix=phase2
  elif [[ "$mode" == shared-q ]]; then
    modules="$artifacts/deferred-shared-q"
    prefix=shared_q
  else
    modules="$artifacts/modules"
    prefix=phase3
  fi
  DLSS5_AMPERE_WEIGHTS=1 DLSS5_LAB_COMPACT_ALL="$compact" DLSS5_LAB_C256_900="$c256" \
    DLSS5_BENCH_SMALL_ONLY=1 DLSS5_BENCH_PROFILE=1 DLSS5_BENCH_DUMP="$artifacts/outputs/$prefix" \
    "$artifacts/benchmark_cuda_nn" "$assets" "$modules" "$warmup" "$iterations" \
    > "$phase/$mode-bench.log" 2>&1
done
python "$phase/analyze.py" --warmup "$warmup" --iterations "$iterations"
