set -e
cd /home/lmxxf/work
[ -d llvm-src-23 ] || git clone -q --depth 1 --branch llvmorg-23.1.2 https://github.com/llvm/llvm-project llvm-src-23
cmake -G Ninja -S llvm-src-23/llvm -B llvm-build-23 -DCMAKE_BUILD_TYPE=Release -DLLVM_ENABLE_ASSERTIONS=OFF -DLLVM_ENABLE_PROJECTS="clang;lld" -DLLVM_TARGETS_TO_BUILD=AMDGPU -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF -DLLVM_INCLUDE_EXAMPLES=OFF > llvm-build-23.cmake.log
ninja -C llvm-build-23 -j 12 clang lld llvm-objdump llvm-readobj llvm-dis > llvm-build-23.log 2>&1
echo BUILD23_OK
