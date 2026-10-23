# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植开发历史与实测回执 (`DevHistory.md`)

**硬件环境**：NVIDIA GeForce RTX 3080 Laptop GPU（GA104，`sm_86`，48 SMs，16,383.5 MiB GDDR6，101,376 B Shared Memory/SM，CUDA Driver `13040`）  
**基线来源**：`DLSS5-AMD 0.44`（含 71-block `1x Original` 模型与 31-block `0.5x Small` 模型）

---

## 2026-10-24：全栈移植、零 `lmem` 栈溢出优化与全档位基准验收

### 1. 仓库初始化与外部资产解耦
- 将 639 个模型权重与资产文件（根目录 71-block `1x Original` 权重 + `small/` 31-block `0.5x Small` 93 个权重文件）从 `OptiScaler-REFramework-DLSS5-AMD-0.44.zip` 提取至 `/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/`，与 Git 源码仓分离，保持 Git 仓库轻量纯净。
- 配置 `.gitignore` 忽略二进制权重（`*.f16`, `*.f32`, `*.bin`）、编译产物（`*.hsaco`, `*.cubin`, `*.ptx`, `*.dll`, `*.addon64`, `*.exe`）及第三方头文件缓存（`third_party/`）。

### 2. RDNA4 Wave32 -> Ampere `sm_86` 设备端兼容层 (`hip/sm86_compat.h`) 与 40 模块编译
- **构建管线 (`hip/build_sm86_modules.py` + `hip/ptx2cubin.cpp`)**：
  - 使用 `clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -Xclang -fnative-half-type -Xclang -fallow-half-arguments-and-returns -nocudainc -nocudalib -std=c++20 -O3` 编译全部 40 个 `.hip`/`.inc` 模块为 PTX；
  - 使用 `hip/ptx2cubin`（调用 `libcuda.so.1` 的 `cuLinkCreate_v2` / `cuLinkAddData_v2` / `cuLinkComplete`）编译为 `sm_86` ELF `.cubin` 并原位保存为 `.hsaco`，全量 **40/40 模块、1,970 个 Kernel 入口**一次性通过 `cuModuleLoadData` 与 `cuModuleGetFunction` 实机校验。
- **WMMA 16x16x16 (`gfx12`) -> Ampere Tensor Core `mma.sync.aligned.m16n8k16` 映射**：
  - 实现 `sm86_frag_butterfly`、`sm86_rdna4_c_to_ampere` 与 `sm86_ampere_d_to_rdna4`，将 RDNA4 Wave32 每 Lane 8 元素的 16x16x16 矩阵布局精确双向映射到两条 `mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` 指令。
  - 实现 IEEE 754 精确舍入的 `sm86_f32_to_e4m3_byte` 与无分支单周期 `prmt.b32` 硬件字节查表的 `sm86_e4m3_to_f16_bits`。

### 3. 宿主运行时与 D3D12-CUDA 桥接层 (`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`, `hip_reference_network.h`)
- **动态加载与跨平台支持**：
  - Windows 下加载 `nvcuda.dll`，Linux/WSL 下加载 `libcuda.so.1`（提供 `OutputDebugStringA` 与 `GetAsyncKeyState` Linux 桩函数，支持在 Linux 下直接用 `g++` 编译 `hip_reference_network.h` 跑纯 GPU 基准测试）。
- **Primary Context 与多线程守卫**：
  - `WrapHipInit` 与 `WrapHipSetDevice` 通过 `cuDeviceGet` + `cuDevicePrimaryCtxRetain` + `cuCtxSetCurrent` 绑定主上下文，并通过 `thread_local` `EnsureCurrentContext()` 确保后台线程（如 `PollWatch`）自动绑定当前设备 `CUcontext`。
- **设备属性、LUID 与架构快速路径激活**：
  - `WrapHipGetDevicePropertiesR0600` 查询 `cuDeviceGetLuid`（8 字节 LUID 与 D3D12 适配器精确匹配）、SM 数量（48）、计算能力（`8.6`）、Opt-in Shared Memory（`101,376 B`），默认报告 `gcnArchName = "gfx1201"`。
  - 更新 `hip_reference_network.h` 中的 `CompactVitTailDeviceEligible()` 与 `hip_d3d12_bridge.h` 的架构/VendorId (`0x10de`) 检查，使 RTX 3080 Laptop GPU 默认开启全部 `W16`（`C32_W16=1`, `C512_W16=2`, `C512_FFN_W16=1`, `VIT_W16=7`）、`compactw` 与 `VIT_INTER_BYTE=15` 跨核 1B E4M3 字节流快速路径。
- **桥接与编译验证 (`Development/HIP/test_cuda_bridge.cpp`)**：
  - 验证 PTX 模块加载、全局常量写入 (`dlss5_style_feature`)、异步流与事件计时（`0.0061 ms`）、`hipMemsetD32Async` 与 `hipMemcpy2DAsync`（12B -> 16B 跨距拷贝）全部通过。
  - 交叉编译产出 Windows `LmxxfNrRuntime.dll`（4.9 MB）与 `dlss5-amd.addon64`（5.1 MB，SHA256 `0e0c7006786979c2...`）。

### 4. 性能剖析与 NVPTX Local Memory (`__local_depot`) 零溢出优化
- **瓶颈定位**：
  - 初版 40 模块跑通后，通过 `cuFuncGetAttribute(CU_FUNC_ATTRIBUTE_LOCAL_SIZE_BYTES)` 与逐核 `opt.profile = true` 剖析发现：
    - `c32_wave1` 全系内核（`c32_wave1_prefix_b8d`, `c32_wave1_post_b8`, `c32_wave1_up_b8`, `c32_wave1_finish_dcrop_b8d` 等）每个线程存在 **`1,872 ~ 2,032 B` 的 Local Memory (`__local_depot`) 栈分配**，单帧耗时高达 `145.9 ms`（占全网一半以上）！
    - 根因是 `wave_owned_c32.inc` 中 `cw_i16 keys{}, values{}, queries{};` 在未展开的 `for(uint qt=0; qt<4; qt++)` 循环中被动态下标 `qt*4+ci*2` 访问；NVPTX 缺乏通用寄存器动态下标寻址，导致每次读写单个元素都将 16 个 32-bit 寄存器全量 `st.local` 到显存栈再 `ld.local` 读回，同时内层未标记 `_Pragma("unroll")` 的 `for(uint ci=0; ci<2; ci++)` 与 `for(uint e=0; e<8; e++)` 循环阻碍了 LLVM SROA pass 将 `ffn[2]`、`input[2]`、`feature[2]` 提升至寄存器。
- **三项无损优化（`0 bit-diff`）**：
  1. **`wave_owned_c32.inc` Shared Memory QKV Staging + 内层循环显式展开**：将 `keys`、`values`、`queries` 移入 `6 KB` L1 Shared Memory (`__attribute__((shared)) i2 cw_qkv_smem[3][8][32]`) 并对内层 `ci<2`、`e<8`、`kt<2` 循环添加 `_Pragma("unroll")`。实测 `c32_wave1` 内核 `lmem` 从 **`1,872 ~ 2,032 B` 直接降至 `0 B`**，寄存器占用从 `250` 降至 `210 ~ 216`。
  2. **`sm86_compat.h` 单周期 `prmt.b32` E4M3->FP16 转换**：用 1 条单周期 `prmt.b32 %0, 0x1e1c1800, 0x23222120, %1` 替代 E4M3 subnormal 的 64-bit 移位分支查表。
  3. **`sm86_compat.h` 零累加器编译期短路与纯函数 `shfl.sync`**：移除 `sm86_shfl_*` 上的冗余 `volatile` 限制，并在 `__builtin_amdgcn_wmma_f32_16x16x16_f16_w32_gfx12` 中通过 `__builtin_constant_p` 检测零初值累加器 `f8{}`，直接省去每轮首步 WMMA 的 20 条 `sm86_rdna4_c_to_ampere` `shfl.sync` 指令。

### 5. RTX 3080 Laptop GPU 全档位实测结果 (`Development/HIP/benchmark_cuda_nn.cpp`)

#### 5.1 全网端到端耗时与逐位一致性对照表（20 帧稳态，Warmup 5 帧）

| 模型与分辨率档位 | 块数 | 优化前 GPU Median | 优化后 GPU Median | 优化后 GPU Mean / p99 | 净减耗时 / 提速比 | 输出范围 `[min, max]` (mean) | 输出 FNV1a-64 Hash (优化前 -> 优化后) | 逐位差异 |
|:---|---:|---:|---:|---:|---:|:---|:---|:---|
| **`0.5x Small 900p`** (`1600×1024`) | 31 | `208.749 ms` | **`144.220 ms`** | `144.298 / 145.805 ms` | **`-64.53 ms` (`1.45×`)** | `[0.000, 1.000]` (`0.500062`) | `48eed0c7f7b18978` -> `48eed0c7f7b18978` | **`0 bit-diff`** |
| **`0.5x Small 1080p`** (`1920×1152`) | 31 | `278.075 ms` | **`187.861 ms`** | `188.102 / 189.337 ms` | **`-90.21 ms` (`1.48×`)** | `[0.000, 1.000]` (`0.496550`) | `d463648c43236f7d` -> `d463648c43236f7d` | **`0 bit-diff`** |
| **`1x Original 900p`** (`1600×960`) | 71 | `362.415 ms` | **`254.476 ms`** | `254.021 / 255.284 ms` | **`-107.94 ms` (`1.42×`)** | `[0.000, 1.000]` (`0.505724`) | `2902af99e603e14d` -> `2902af99e603e14d` | **`0 bit-diff`** |
| **`1x Original 1080p`** (`1920×1152`) | 71 | `493.640 ms` | **`354.928 ms`** | `354.246 / 355.587 ms` | **`-138.71 ms` (`1.39×`)** | `[0.000, 1.000]` (`0.503984`) | `17469c9b18bbbc8a` -> `17469c9b18bbbc8a` | **`0 bit-diff`** |

- 全部 4 组测试 `invalid (NaN/Inf) = 0`，首帧与末帧 `bit_diff = 0`，`SP_STATS fallback = 0, errors = 0`。

#### 5.2 `0.5x Small 1080p` (`1920×1152`) 逐核 GPU 耗时分解对照（单位：ms）

| 内核名称 (Kernel) | 优化前耗时 | 优化后耗时 | 加速比 |
|:---|---:|---:|---:|
| `c32_wave1_prefix_b8d` | `51.622 ms` | **`22.194 ms`** | **`2.33×`** |
| `c32_wave1_post_b8` | `46.829 ms` | **`21.994 ms`** | **`2.13×`** |
| `c32_wave1_up_b8` | `12.447 ms` | **`5.860 ms`** | **`2.12×`** |
| `c32_wave1_finish_dcrop_b8d` | `12.209 ms` | **`5.738 ms`** | **`2.13×`** |
| `c32_wave1_finish_b8` | `11.833 ms` | **`5.718 ms`** | **`2.07×`** |
| `c32_wave1_mapped_b8` | `10.964 ms` | **`5.401 ms`** | **`2.03×`** |
| `c512_qkv_attention_compact_w16` | `8.032 ms` | **`4.222 ms`** | **`1.90×`** |
| `vit_stream_contract_frag_bstream_bout` | `14.638 ms` | **`11.070 ms`** | **`1.32×`** |
| `vit_expand_blocked_fp8_frag_bytein_w16` | `11.984 ms` | **`9.602 ms`** | **`1.25×`** |
| `vit_stream_qkv_frag_bin_w5f8` | `11.487 ms` | **`9.753 ms`** | **`1.18×`** |
| `split_ffn_one_w2f8_w16_bin` | `3.396 ms` | **`2.767 ms`** | **`1.23×`** |
| **全网 Kernel 总计 (`TOTAL`)** | **`280.715 ms`** | **`186.439 ms`** | **`1.51×`** |
