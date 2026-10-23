# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植版

本项目将原本运行于 AMD RDNA4 (`gfx1201`) 的完整 DLSS 5 神经渲染管线（包含 71-block `1x Original` 模型与 31-block `0.5x Small` 模型、D3D12 编解码器、时序历史融合、OptiScaler/REFramework 实时插件与独立 Runtime DLL）完整移植到 **NVIDIA GeForce RTX 3080 Laptop GPU (`sm_86` Ampere 架构)**。

---

## 核心特性

1. **全栈 RDNA4 Wave32 -> NVIDIA Ampere `sm_86` 内核移植 (`hip/sm86_compat.h`)**：
   - 将全部 **40 个计算模块（共 1,970 个 Kernel 入口）** 通过 `clang++ --cuda-gpu-arch=sm_86` + `ptx2cubin` 编译为原生 `sm_86` Tensor Core 二进制模块（`.cubin`，按原 `.hsaco` 文件名原位部署）。
   - 将 RDNA4 `__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12` 与 `__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12` 精确映射到 Ampere `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` Tensor Core 指令，配合单周期 `prmt.b32` 硬件字节查表实现无损 OCP E4M3 (FP8) <-> IEEE FP16 转换。
   - 针对 NVPTX 后端架构特性，消除 `wave_owned_c32.inc` 与 `wave_owned_mh.inc` 中跨循环向量的动态下标栈分配（`__local_depot`），将 `c32_wave1` 与 `c256_wave2` 的 Local Memory 溢出从 `1,616 ~ 2,032 B/thread` 降至 **`0 B`**。

2. **NVIDIA CUDA Driver API 零改动桥接层 (`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`)**：
   - 保持 `hip_probe::Api` 接口不变，底层直接对接 Windows `nvcuda.dll` 与 Linux/WSL `libcuda.so.1`。
   - 自动管理 `cuDevicePrimaryCtxRetain` 与 `thread_local` 上下文绑定（支持多线程 `PollWatch` 与异步队列）。
   - 完整接通 D3D12 <-> CUDA 共享显存缓冲 (`cuImportExternalMemory`)、D3D12 共享 Fence (`cuImportExternalSemaphore` / `cuWaitExternalSemaphoresAsync` / `cuSignalExternalSemaphoresAsync`) 以及 D3D12 适配器 8 字节 LUID 自动匹配 (`cuDeviceGetLuid`)。

3. **双模型支持（`0.5x Small` 31-block & `1x Original` 71-block）**：
   - 默认启用 `DLSS5_MULTI_PASS=0.5`（31-block `0.5x Small` 模型），支持游戏内按 `F9` 热切换 `0.5x -> 1x -> 2x -> 3x -> 0.5x`。

---

## 快速构建指南

### 1. 编译 40 个 `sm_86` 内核模块
```bash
g++ -O2 -std=c++17 hip/ptx2cubin.cpp -L/usr/lib/wsl/lib -lcuda -o hip/ptx2cubin
python3 hip/build_sm86_modules.py
```

### 2. 编译并运行 CUDA + D3D12 桥接自检与神经网络基准测试
```bash
# Linux 原生 CUDA Driver API 桥接测试
g++ -O2 -std=c++17 Development/HIP/test_cuda_bridge.cpp -ldl -lpthread -o /tmp/test_cuda_bridge_linux
/tmp/test_cuda_bridge_linux

# Linux 原生全网 0.5x Small / 1x Original (1080p & 900p) 基准测试
g++ -O2 -std=c++17 Development/HIP/benchmark_cuda_nn.cpp -IDevelopment/HIP -ldl -lpthread -o /tmp/benchmark_cuda_nn
/tmp/benchmark_cuda_nn
```

### 3. 交叉编译 Windows 插件（`LmxxfNrRuntime.dll` & `dlss5-amd.addon64`）
```bash
bash scripts/build-runtime.sh /tmp/dlss5-win-bin
bash scripts/build-addon-oneclick.sh /tmp/dlss5-win-bin/dlss5-amd.addon64 --hip
```

---

## 详细开发文档
- [架构设计与工作计划 (`Development/WorkingPlan.md`)](Development/WorkingPlan.md)
- [移植开发日志与实测数据 (`Development/DevHistory.md`)](Development/DevHistory.md)
