# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植工程工作计划与架构说明

**项目仓库**：`https://github.com/lmxxf/DLSS5-RTX-3080-laptop`  
**目标硬件**：NVIDIA GeForce RTX 3080 Laptop GPU（GA104，`sm_86` Ampere 架构，48 SMs，16 GB GDDR6，101,376 B Shared Memory/SM，65,536 Registers/SM）  
**基线版本**：基于 `DLSS5-AMD 0.44`（含 71-block `1x Original` 模型与 31-block `0.5x Small` 模型）

---

## 1. 核心架构与三层移植设计

本项目将原本针对 AMD RDNA4 (`gfx1201`) Wave32 + WMMA 构建的完整 DLSS 5 神经渲染管线（OptiScaler / REFramework 插件 + D3D12 编解码 + 71-block / 31-block Swin-ViT 混合神经网络）完整移植到 NVIDIA Ampere (`sm_86`) 架构：

### 1.1 设备端算子与指令集兼容层（`hip/sm86_compat.h`）
- **编译管线**：使用 `clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -Xclang -fnative-half-type -Xclang -fallow-half-arguments-and-returns -nocudainc -nocudalib -std=c++20 -O3` 直接将无 SDK 依赖的 `.hip` / `.inc` 源码编译为 PTX，再由 `hip/ptx2cubin`（基于 NVIDIA Driver JIT Linker API `cuLinkCreate_v2` / `cuLinkAddData_v2`）编译为原生 `sm_86` ELF `.cubin`（以 `.hsaco` 文件名原位部署，宿主零改动）。
- **Wave32 16x16x16 WMMA -> Ampere `mma.sync.aligned.m16n8k16` 精确映射**：
  - RDNA4 的 `__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12` 与 `__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12` 每条 Lane 持有 8 个输入/累加元素；
  - `sm86_compat.h` 通过无分支 `prmt.b32` 硬件字节查表将 OCP E4M3 (FP8) 精确无损转换为 IEEE FP16，经 `sm86_frag_butterfly` 寄存器洗牌对齐到 Ampere `m16n8k16` 矩阵片段布局，发射两条 `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` Tensor Core 指令完成 16x16x16 矩阵乘累加，并在累加器初值为零 (`__builtin_constant_p`) 时编译期短路跳过 `c_to_ampere` 的 20 条 `shfl.sync` 指令。
- **AMDGPU 硬件指令精确对偶**：
  - `v_med3_f32` (`__builtin_amdgcn_fmed3f`)：精确复现 NaN 输入向 `min(lo, hi)`（如 `-448.f` / `-4.f`）坍缩的硬件语义；
  - `v_sin_f32` / `v_cos_f32`：保留 AMDGPU 以圈数（$2\pi$ 弧度为 1 周期）为单位的输入约定；
  - `v_log_f32`：`lg2.approx.ftz.f32`；
  - `__builtin_amdgcn_ds_bpermute` / `readlane` / `readfirstlane`：映射到 `shfl.sync.idx.b32`；
  - `s_barrier` / `wave_barrier` / `__hip_atomic_*`：映射到 `bar.sync 0`、`bar.warp.sync 0xffffffff` 与 PTX `.cg`/`.wb` 全局原子操作（支撑 `swin-persistent` 跨 WG 任务队列）。

### 1.2 NVPTX Local Memory (`__local_depot`) 零溢出优化（`wave_owned_c32.inc`, `wave_owned_mh.inc`）
- **根因诊断**：在 AMDGPU 上，LLVM 可对 `ext_vector_type(16)` (`cw_i16`, `w2_i16`) 使用 VGPR 相对寻址或跨循环保持寄存器；但在 NVPTX 后端中，任何被未展开外层循环变量 `qt` 动态索引的向量/数组都会被降级到 `.local` DRAM 栈帧（`__local_depot`），导致每个线程产生 `1,872 ~ 2,032 B` 的 Local Memory 溢出与数千条 `st.local`/`ld.local` 指令。
- **根治方案**：
  - 在 `wave_owned_c32.inc` 中，将跨 `qt` 阶段存活的 `queries`、`keys`、`values` 移入 `10 KB` L1 Shared Memory (`__attribute__((shared)) i2 cw_qkv_smem[3][8][32]`)，并对内层 `ci<2`、`e<8`、`kt<2` 循环强制 `_Pragma("unroll")`：使 `c32_wave1` 全系内核的 `lmem` 从 **`1,872 ~ 2,032 B` 降至 `0 B`**，寄存器占用从 `250` 降至 `210 ~ 216`，`c32_wave1` 耗时直接减半（`-70.4 ms/frame`）。
  - 在 `wave_owned_mh.inc` 中，使用无分支常量下标选择器 `w2_set_pair` / `w2_get_pair` (`selp.b32`) 替代 `query_words[qt*4+ci*2]` 动态下标，并将 `qkv[part][qt][ci]` 按常量 `part=0/1/2` 分支展开，使 `c256_wave2_bi_bo_w16` 的 `lmem` 从 **`1,616 B` 降至 `0 B`**。

### 1.3 宿主运行时与 D3D12-CUDA 桥接层（`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`）
- **零改动 ABI 兼容**：`hip_api.h` 保持 `hip_probe::Api` 的全部方法名与函数指针签名，底层动态加载 Windows `nvcuda.dll` 或 Linux/WSL `libcuda.so.1`。
- **Primary Context 与多线程自动绑定**：
  - `hipInit` / `hipSetDevice` 通过 `cuDeviceGet` + `cuDevicePrimaryCtxRetain` + `cuCtxSetCurrent` 绑定主上下文；
  - 内置 `thread_local` 快速上下文守卫 `EnsureCurrentContext()`，确保后台线程（如 `D3D12Bridge::PollWatch`）首次调用 CUDA Driver API 时自动绑定当前设备的 `CUcontext`。
- **D3D12 共享资源与 Fence 同步**：
  - 通过 `cuDeviceGetLuid` 获取 8 字节 LUID 与 `ID3D12Device::GetAdapterLuid()` 精确匹配；
  - 通过 `cuImportExternalMemory` (`type=5`, `CU_EXTERNAL_MEMORY_HANDLE_TYPE_D3D12_RESOURCE`)、`cuExternalMemoryGetMappedBuffer`、`cuImportExternalSemaphore` (`type=4`, `CU_EXTERNAL_SEMAPHORE_HANDLE_TYPE_D3D12_FENCE`)、`cuWaitExternalSemaphoresAsync`、`cuSignalExternalSemaphoresAsync` 实现 D3D12 <-> CUDA 零拷贝显存共享与 GPU 侧 Fence 同步。
- **>48 KB Shared Memory 自动 Opt-in**：在 `WrapHipModuleGetFunction` 与 `WrapHipModuleLaunchKernel` 中自动检测并设置 `CU_FUNC_ATTRIBUTE_MAX_DYNAMIC_SHARED_SIZE_BYTES` 与 `CU_FUNC_ATTRIBUTE_PREFERRED_SHARED_MEMORY_CARVEOUT = 100`。

---

## 2. 目录结构与外部资产约定

- **代码仓库**：`/home/lmxxf/work/DLSS5-RTX-3080-laptop`（保持轻量纯源码，大二进制权重与 `.hsaco`/`.cubin` 均在 `.gitignore` 中忽略）
  - `hip/sm86_compat.h`：RDNA4 -> Ampere `sm_86` 设备端兼容头
  - `hip/ptx2cubin.cpp`：调用 `libcuda.so.1` JIT Linker 的 PTX -> cubin 编译与符号校验工具
  - `hip/build_sm86_modules.py`：并行编译全部 40 个模块（1,970 个内核入口）的构建脚本
  - `Development/HIP/hip_api.h`：NVIDIA CUDA Driver API (`nvcuda.dll` / `libcuda.so.1`) 适配层
  - `Development/HIP/hip_d3d12_bridge.h`：D3D12 <-> CUDA 互操作桥接层
  - `Development/HIP/hip_reference_network.h`：支持 31-block `0.5x Small` 与 71-block `1x Original` 的宿主执行图
  - `Development/HIP/test_cuda_bridge.cpp`：Linux/Windows 双端 CUDA Driver API 与 D3D12 互操作自检程序
  - `Development/HIP/benchmark_cuda_nn.cpp`：Linux 原生纯神经网络全档位（1080p/900p × 0.5x/1x）精度与性能基准工具
- **外部权重与编译产物目录**：`/home/lmxxf/work/dlss5-assets/native-game-tiled-assets`
  - 根目录：71-block `1x Original` 权重资产
  - `small/`：31-block `0.5x Small` 权重资产（93 个文件）
  - `HIP/`（含 `gfx1201/`, `gfx1200/`, `sm_86/`）：40 个 `sm_86` 编译模块（`.hsaco` ELF cubin）

---

## 3. 后续优化路线图

1. **WMMA 累加器跨 K 步保持 Ampere 布局**：
   - 目前每次 `wmma_f32_16x16x16` 调用内部执行 `sm86_rdna4_c_to_ampere`（20 条 `shfl.sync`）与 `sm86_ampere_d_to_rdna4`（20 条 `shfl.sync`）。在 `c32_wave1`、`c64_wave2`、`c512_m32`、`vit_stream` 的内层 K 循环中，若将累加器在 K 循环期间保持为 Ampere 原生布局、仅在 K 循环结束后做一次 `sm86_ampere_d_to_rdna4`，可消去 80% 以上的跨 lane 洗牌指令。
2. **权重量化预重排（Host-side Ampere Fragment Packing）**：
   - 在宿主侧上传权重时直接按 `mma.sync.m16n8k16` 的 Lane 布局预打包 `FragmentPackedMatrixW16`，即可省去内核中的 `sm86_frag_butterfly`（每次 WMMA 再省 16 条 `shfl.sync`）以及实时 `FP8 -> FP16` 解包，将 `sm_86` Tensor Core 吞吐推至硬件极限。
3. **《鬼武者》(Onimusha) / RE9 实机集成验证**：
   - 使用已交叉编译的 `LmxxfNrRuntime.dll` 与 `dlss5-amd.addon64` 配合 40 个 `sm_86` 模块在 Windows 实机游戏中验证端到端帧率与画质。
