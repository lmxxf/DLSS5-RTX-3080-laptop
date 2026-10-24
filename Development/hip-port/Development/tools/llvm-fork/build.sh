#!/usr/bin/env bash
set -euo pipefail
# Native aarch64 build; generated AMDGPU objects are platform independent.
src=${LLVM_SOURCE:-/home/lmxxf/work/llvm-project}
out=${LLVM_BUILD:-/home/lmxxf/work/llvm-build-dlss5-gfx12}
jobs=${LLVM_JOBS:-16}
mkdir -p "$out"
git -C "$src" rev-parse HEAD > "$out/source-commit.txt"
cmake -S "$src/llvm" -B "$out" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_PROJECTS='clang;lld' \
  -DLLVM_TARGETS_TO_BUILD=AMDGPU -DLLVM_ENABLE_ASSERTIONS=OFF \
  -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF \
  -DLLVM_INCLUDE_BENCHMARKS=OFF -DCLANG_INCLUDE_TESTS=OFF \
  -DLLVM_PARALLEL_LINK_JOBS=2 -DLLVM_ENABLE_TERMINFO=OFF
start=$(date +%s)
cmake --build "$out" -j "$jobs" --target clang lld llvm-objdump llvm-readobj llvm-nm llvm-objcopy llvm-dis llvm-link opt llc
end=$(date +%s)
printf 'build_seconds=%s\n' "$((end-start))" | tee "$out/build-duration.txt"
"$out/bin/clang" --version
