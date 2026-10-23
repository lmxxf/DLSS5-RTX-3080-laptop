# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) Port

This repository ports the complete DLSS 5 neural rendering pipeline (both the 71-block `1x Original` model and the 31-block `0.5x Small` model, D3D12 codec passes, temporal history fusion, OptiScaler/REFramework add-on, and standalone Runtime DLL) from AMD RDNA4 (`gfx1201`) to the **NVIDIA GeForce RTX 3080 Laptop GPU (`sm_86` Ampere architecture)**.

**[中文说明 (`README.zh-CN.md`)](README.zh-CN.md)** | **[Working Plan (`Development/WorkingPlan.md`)](Development/WorkingPlan.md)** | **[Development History (`Development/DevHistory.md`)](Development/DevHistory.md)**

---

## Key Highlights

1. **RDNA4 Wave32 -> NVIDIA Ampere `sm_86` Kernel Port (`hip/sm86_compat.h`)**:
   - All **40 compute modules (1,970 kernel entry points)** compile cleanly to native `sm_86` `.cubin` ELF binaries (deployed in-place as `.hsaco` files) using `clang++ --cuda-gpu-arch=sm_86` + `hip/ptx2cubin`.
   - Maps RDNA4 Wave32 16x16x16 WMMA (`__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12` and `__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12`) to Ampere Tensor Core `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` instructions with single-cycle `prmt.b32` branchless OCP E4M3 (FP8) <-> IEEE FP16 conversion.
   - Eliminates NVPTX local memory stack allocations (`__local_depot`) in `wave_owned_c32.inc` and `wave_owned_mh.inc` by staging cross-loop QKV fragments in shared memory and replacing dynamic vector indexing with branchless constant-index selectors (`0 B` local memory spill).

2. **Drop-In NVIDIA CUDA Driver API Runtime & D3D12 Bridge (`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`)**:
   - Preserves the `hip_probe::Api` interface while dynamically loading `nvcuda.dll` on Windows and `libcuda.so.1` on Linux/WSL.
   - Automatically manages primary context retention (`cuDevicePrimaryCtxRetain`) and `thread_local` context binding across threads.
   - Full D3D12 <-> CUDA interop via `cuDeviceGetLuid`, `cuImportExternalMemory`, `cuExternalMemoryGetMappedBuffer`, `cuImportExternalSemaphore`, `cuWaitExternalSemaphoresAsync`, and `cuSignalExternalSemaphoresAsync`.

3. **Dual Model Support (`0.5x Small` 31-Block & `1x Original` 71-Block)**:
   - Defaults to `DLSS5_MULTI_PASS=0.5` (31-block `0.5x Small` model) with in-game `F9` hot-switching (`0.5x -> 1x -> 2x -> 3x -> 0.5x`).

---

## Quick Build & Benchmark

```bash
# 1. Build all 40 sm_86 kernel modules
g++ -O2 -std=c++17 hip/ptx2cubin.cpp -L/usr/lib/wsl/lib -lcuda -o hip/ptx2cubin
python3 hip/build_sm86_modules.py

# 2. Run CUDA Driver API & full neural network benchmarks (Linux/WSL)
g++ -O2 -std=c++17 Development/HIP/test_cuda_bridge.cpp -ldl -lpthread -o /tmp/test_cuda_bridge_linux
/tmp/test_cuda_bridge_linux

g++ -O2 -std=c++17 Development/HIP/benchmark_cuda_nn.cpp -IDevelopment/HIP -ldl -lpthread -o /tmp/benchmark_cuda_nn
/tmp/benchmark_cuda_nn

# 3. Cross-compile Windows binaries (LmxxfNrRuntime.dll & dlss5-amd.addon64)
bash scripts/build-runtime.sh /tmp/dlss5-win-bin
bash scripts/build-addon-oneclick.sh /tmp/dlss5-win-bin/dlss5-amd.addon64 --hip
```
