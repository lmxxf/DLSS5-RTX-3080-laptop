# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植开发历史与实测回执 (`DevHistory.md`)

> **当前正式版本：v0.2.0（2026-10-26）**，三包统一PTX V2.1，模型6.66/9.70/12.78ms；正式包下载：`https://gofile.io/d/OOeOcxn6`，RTX 3080 Laptop 实机《鬼武者》2K性能档 **43 FPS**（原30 FPS）、《剑星》2K性能档**接近 60 FPS**；本机部署/新ZIP/SHA见[发布回执](ptx-patcher/release-rtx30/v020/README.md)。下文0.1.0与各Phase保留历史原值。

**硬件环境**：NVIDIA GeForce RTX 3080 Laptop GPU（GA104，`sm_86`，48 SMs，16,383.5 MiB GDDR6，101,376 B Shared Memory/SM，Boost `P0: 1725 MHz SM / 7001 MHz Mem / 132.1 W`，CUDA Driver `13040`）  
**基线来源**：`DLSS5-AMD 0.44` 独立引擎 + NVIDIA 原版 `nvngx_dlssnr.dll` (`v310.9.16.0`)  
**模型范围**：RTX 30 系仅保留并维护 **31 块 `0.5x Small` 轻量新模型（`Preset 2`）**，不再折腾 71 块旧模型。  
**⚠️ Git 提交铁律（必须严格执行）**：**每完成一个功能或一个优化阶段并通过实测验证后，必须立即清理临时二进制大文件（`*.rgb32`, `*.hsaco`, `*.cubin`, `*.ptx`, `artifacts/` 等不进 Git 的构建产物）并执行一次 `git commit`（严禁加 `Co-Authored-By`）**，绝不能攒好几个阶段一宿不提交！朱雀每次派单给闇时必须在 prompt 中显式附带此提交要求。

---

## 0. 双技术路线总览与 `v0.1.0` 最终定版状态速查

本项目在 RTX 3080 Laptop (`sm_86`) 上完整跑通并同机对决了 **两条技术路线**（均跑同一 31 块 `0.5x Small` 新模型），最终发布的 **`v0.1.0` 三个完整包（`OptiScaler`、`OptiScaler-REFramework`、`Magpie`）全部统一采用速度最快的路线 B（`ptx-patcher`）**：

| 路线 | 核心路径与代码位置 | `1280×720` (720p) | `1600×900` (900p) | `1920×1080` (1080p) | 优劣势与定位 |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **路线 B（主推 / `v0.1.0` 全系采用）：直接改写原版 `nvngx_dlssnr.dll` 内置 PTX（15/15 满血 `O4`）** | `Development/ptx-patcher/`：提取 `310.9.16.0` `nvngx_dlssnr.dll` 内置的 15 个 Fatbin PTX，降级 `fence.acquire.gpu;`，用独创的 **两条 IEEE 754 `f16x2` 硬件指令恒等式** 替换 `e4m3x2 <-> f16x2` 转换，并通过全函数定义扫描剔除 `%r1352` 等向量加载多定义 `mapped` 误判（消除上游 `dlssnr-patcher` 的 106 条天空红绿横带），使 15/15 个 Fatbin 全部以满血 **`O4`** 原槽位编译（比上游 `O1` 的 `37.13 / 49.89 / 67.69 ms` 快 **`2.08×~2.35×`**） | **`15.83 ms`** | **`24.47 ms`** | **`32.04 ms`** | **`v0.1.0` 三个发布包统一路线**：原生使用 Full Rate **FP16 累加 Tensor Core (`.f16.f16.f16.f16`)** 且 0 跨线程洗牌；《鬼武者》实机 `480p` **`8.2 ms`（46 FPS）**、`720p` **`17.1 ms`（30 FPS）**；《剑星》4K `720p` **`18.4 ms`**；Magpie《光环》720p→4K 模型耗时 **`15.95 ms`** |
| **路线 A（附加 / 实验归档）：`RDNA4 -> Ampere` 独立引擎移植** | `Development/hip-port/`：将 AMD RDNA4 (`gfx1201`) 的 HIP C++ 独立推理引擎（`LmxxfNrRuntime.dll` / `dlss5-amd.addon64` + 40 个内核模块）通过 `hip/sm86_compat.h` 与 `hip/build_sm86_modules.py`（V6 8B 全激活预洗牌 + 32/32 零 `LMem` 栈溢出）移植到 CUDA Driver API 与 `sm_86` Tensor Core | `~31.0 ms` | `43.10 ms` (`23.2 FPS`) | `57.13 ms` (`17.5 FPS`) | 证明跨架构全栈可移植且与 Exact 黄金基准 `0 bit-diff`；但受限于 GeForce 30 系硬件对 **FP32 累加 Tensor Core (`.f32.f16.f16.f32`) 砍半（Half Rate）** 及 Wave32↔Warp32 洗牌开销，速度慢于路线 B，归档作为研究与备用路线 |

### `v0.1.0` 最终定版产物与坐标速查（2026-10-24）
- **正式发布包下载（Gofile）**：`https://gofile.io/d/s9cpHYH9`（本地位于 `C:\DLSS5-5090-dll\发布打包\`）：
  1. `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`（`376,272,150 B`，SHA256 `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67`）——《鬼武者：剑之道》《生化 9》等 RE Engine 游戏（路线 B）
  2. `OptiScaler-DLSS5-RTX30-0.1.0.zip`（`319,200,566 B`，SHA256 `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac`）——《剑星》等常规 DX12 游戏（路线 B）
  3. `Magpie-DLSS5-RTX30-0.1.0.zip`（`324,124,886 B`，SHA256 `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb`）—— 通用窗口缩放，启用 `Magpie.exe` 原生 `DLSSNR` `Preset 2` 补丁 + 路线 B
- **核心二进制 SHA256**：
  - 最终生产版 `nvngx_dlssnr.dll`（15/15 `O4` + 多定义 `mapped` 修复）：`3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`（本地备份于 `C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_fast.dll`）
  - 原版未改 `nvngx_dlssnr.dll`（`310.9.16.0` 输入源）：`2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f`（位于 `C:\DLSS5-5090-dll\nvngx_dlssnr.dll`）
  - `Preset 2` 补丁版 `Magpie.exe`：`b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea`
- **公众号与用户使用说明固定入口**：[`Development/doc/使用说明.md`](doc/使用说明.md)

---

## 2026-10-24 (路线 A / Phase 1~6)：`RDNA4 -> Ampere` 独立引擎全栈移植、V6 全激活预洗牌 + 32/32 零 `LMem` 栈溢出优化

### 1. 仓库初始化与外部资产解耦
- 将 639 个模型权重与资产文件（根目录 71-block `1x Original` 权重 + `small/` 31-block `0.5x Small` 93 个权重文件）从 `OptiScaler-REFramework-DLSS5-AMD-0.44.zip` 提取至 `/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/`，与 Git 源码仓分离，保持 Git 仓库轻量纯净。
- 配置 `.gitignore` 忽略二进制权重（`*.f16`, `*.f32`, `*.bin`）、编译产物（`*.hsaco`, `*.cubin`, `*.ptx`, `*.dll`, `*.addon64`, `*.exe`）及第三方头文件缓存（`third_party/`）。

### 2. RDNA4 Wave32 -> Ampere `sm_86` 设备端兼容层 (`hip/sm86_compat.h`) 与 V5 SSA 编译器优化管线 (`hip/build_sm86_modules.py`)
- **构建管线**：
  - `clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -Xclang -fnative-half-type -Xclang -fallow-half-arguments-and-returns -nocudainc -nocudalib -std=c++20 -O3 -S -emit-llvm` -> `opt-14 -instnamer -loop-simplify -lcssa` -> `cancel_wmma_shuffles_ir` (SSA Pass) -> `opt-14 -O3 -disable-loop-unrolling` -> `llc-14 -march=nvptx64 -mcpu=sm_86 --fp-contract=fast -O3` -> `hip/ptx2cubin`（生成 `sm_86` ELF `.cubin` 并原位保存为 `.hsaco`），全量 **40/40 模块、1,970 个 Kernel 入口**实机校验通过。
- **V5 六大核心指令与编译器优化**：
  1. **无分支单基本块 `sm86_f32_to_e4m3_byte` 与无分支向量化 `prmt.b32` + `mul.rn.f16x2 (0x5c005c00)` E4M3x8 -> FP16x8 解包 (`sm86_unpack_e4m3x8`)**：将 FP32->E4M3 量化全部收拢为单基本块 `selp` 无分支实现，并利用 IEEE FP16 次正规数乘以 $2^8$ (`0x5c00`) 在硬件内一步完成 E4M3 正规数与次正规数的精确转换，8 个 E4M3 字节仅需 4 条 `prmt.b32` + 4 条 `mul.rn.f16x2`。
  2. **Shuffle-Before-Unpack `__sm86_prep_fp8` 与 8-shfl XOR-Benes C/D 网络 (`__sm86_c_to_ampere` / `__sm86_d_to_rdna4`)**：先对两个 32 位 E4M3 打包字执行 4 条 `shfl.sync`（将 `selp` 从 16 条降至 6 条），再经奇偶 lane 选择器 `0x3424 / 0x1404` 一步 `prmt.b32` 展开为 4 个 `f16x2`。
  3. **8 字节全激活预洗牌 `sm86_preshuffle_fp8` + 零洗牌 `sm86_wmma_fp8_preshuffled_ab / _a / _b`**：
     - 在 `wave_owned_c32.inc` 中将 `input[0..1]`（跨 `h2=0..3` 循环复用）、`act[0..1]`、`feature[0..1]`、`Q`、`K`、`V`、`prob` 与 `av[0..1]` 全部预洗牌为 8 字节 Ampere 布局 (`i2`)，将 `c32_wave1` 寄存器从 `201~207` 降至 **`162~178`**；
     - 在 `wave_owned_mh.inc`（`c64_wave2`、`c128_wave2`、`c256_wave2`、`swin-persistent`）中将 `in0/in1/inputs`、`hidden`、Stage 1 写 `plane1`（供 Stage 2 Cross-head FFN 所有 `NW` 个 Warp 共享读取）、Stage 2 写 `plane0`（供 Stage 3 QKV 所有 `NW` 个 Warp 与 Stage 5 Diag Residual 读取）、`Q/K/V/prob` 及 Stage 4 Attention AV 写 `plane1`（供 Stage 5 Output Projection 所有 `NW` 个 Warp 读取）全部预洗牌为 8 字节 `i2`，使所有 WMMA 循环内部**完全省去激活跨线程洗牌 (`0 shfl.sync`)**，将 `sp_run256_w16` 降至 **`15.21 ms`**、`c128_wave2_bi_bo` 降至 **`13.61 ms`**、`c64_wave2_bi_bo` 降至 **`8.82 ms`**、`c256_wave2_bi_bo_w16` 降至 **`3.39 ms`**；
     - 在 `deep_fast.hip` 的 `vit_attention_transposed_score_body` 中将 `q[0..1]` 在 40 步 `key` 循环前预洗牌为 `i2`，将 `vit_attention_fused_640_bytein_bout` 降至 **`2.07 ms`**。
     - 修复全部多指令 `prmt.b32` 内联汇编的 `"=&r"` early-clobber 约束，避免高强度 CSE 下寄存器重用覆写源操作数。
  4. **`vit_stream_qkv_frag_bin_w5f8` 共享内存预解包/预洗牌 (`sm86_wmma_fp8_prepped_b`)**：在 `vit_stream.inc` 中由 4 个搬运 Warp (`t < 128`) 在写入 16 KB `lds` 时直接完成 `__sm86_prep_fp8`，使全部 5 个计算 Warp 在内层 K 循环中直接从 `lds` 加载 `sm86_u4` 送入 `mma.sync`（`vit_stream_qkv` 耗时从 `5.37 ms` 降至 **`4.02 ms`**）。
  5. **LLVM IR SSA 跨 K 循环 C/D 互逆洗牌代数抵消 (`cancel_wmma_shuffles_ir`) + K32 / 4-Partition `__sm86_c_to_ampere(sum)` 消洗牌 + 常量折叠 (`cse_and_hoist_prep_calls`)**：
     - 在 LCSSA 形式下自动消除 K 累加循环（含普通循环、完全展开循环、Diamond-PHI `if(live)` 循环以及 `mh_pool_project`、`vit_contract_blocked`、`vit_stream_project_tiles`、`decoder_project2x_h16w_wide_body` 的 K32 / 4-partition 分段归并循环）内部的 `@__sm86_d_to_rdna4` 与 `@__sm86_c_to_ampere` 互逆调用对，使累加器在整个 K 循环期间保持 Ampere `m16n8k16` 原生寄存器布局。
     - 对同一基本块内共享的 `@__sm86_prep_fp8`、`@__sm86_prep_f16` 自动执行 SSA 去重，并对 `zeroinitializer` 及全 `1.0h` (`0xH3C00`) 常量直接折叠为编译期常数。
  6. **32/32 活跃内核 NVPTX Local Memory (`__local_depot`) 100% 零溢出 (`LMem = 0 B`)**：
     - `wave_owned_c32.inc`：跨 `qt` 阶段存活的 QKV 片段移入 Shared Memory (`cw_qkv_smem`)；
     - `wave_owned_mh.inc`：将 Q 存入 `plane1[64*C]`、K 存入 `plane_k[64*C]`，`W2_FFN_QT_BATCH = 2`，并将非 `ByteOut` 尾部分支展开为 `float out_v[8]` 向量化写出（消除 `c64_wave2_bi` 与 `c256_wave2_bi_w16` 的 `64 B` `LMem`）；
     - `c512_qkv_attention_compact.inc`：将 `W16` 融合 QKV K 循环改为 `_Pragma("clang loop unroll(disable)") for(uint gs=0;gs<16;gs++)`，使 V5 SSA Pass 自动消掉回边 C/D 洗牌并将寄存器从 `255` 降至 `229`、**`LMem` 从 `232 B` 降至 `0 B`**，耗时从 `2.33 ms` (`0.5x`) / `7.90 ms` (`1x`) 暴降至 **`1.16 ms` (`0.5x`) / `4.59 ms` (`1x`)**；
     - **32/32 个 `0.5x Small` 活跃内核全部实现 `LMem = 0 B`！**

### 3. 宿主运行时与 D3D12-CUDA 桥接层 (`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`, `src/native_hip_network.h`)
- Windows 下加载 `nvcuda.dll`，Linux/WSL 下加载 `libcuda.so.1`，自动管理 `cuDevicePrimaryCtxRetain` 与 `thread_local` 上下文绑定。
- 完整实现 `cuDeviceGetLuid` D3D12 适配器 LUID 匹配、`cuImportExternalMemory`、`cuExternalMemoryGetMappedBuffer`、`cuImportExternalSemaphore`、`cuWaitExternalSemaphoresAsync`、`cuSignalExternalSemaphoresAsync`。
- 交叉编译产出 Windows `LmxxfNrRuntime.dll`（4.9 MiB）、`dlss5-amd.addon64`（5.1 MiB）与 `frame.exe`（2.3 MiB），并在 Windows 11 实机通过 `frame.exe` 端到端 D3D12 编解码 + CUDA 互操作全流程验证。

---

### 4. RTX 3080 Laptop GPU 全档位实测结果

#### 4.1 五个阶段端到端耗时演进对照表（GPU Median / Min `ms/frame`，Warmup 5 帧，测量 20 帧）

| 模型与分辨率档位 | 块数 | Baseline (Initial Port) | Phase 1 (`c32` 0-LMem) | Phase 2 (`w2` + Unroll) | Phase 3 (V3+ SSA) | **Phase 4 (V5 Preshuffle + 32/32 0-LMem)** | **总提速比 (vs. Baseline)** |
|:---|---:|---:|---:|---:|---:|---:|---:|
| **`0.5x Small 900p`** (`1600×1024`) | 31 | `208.749 ms` | `144.220 ms` | `144.220 ms` | `55.108 ms` | **`43.257 ~ 47.076 ms`** (min **`43.095 ms`**, **23.2 FPS**) | **`4.83×` (`-79.3%`)** |
| **`0.5x Small 1080p`** (`1920×1152`) | 31 | `278.075 ms` | `187.861 ms` | `169.508 ms` | `74.089 ms` | **`57.454 ~ 62.725 ms`** (min **`57.131 ms`**, **17.5 FPS**) | **`4.84×` (`-79.3%`)** |
| **`1x Original 900p`** (`1600×960`) | 71 | `362.415 ms` | `254.476 ms` | `254.476 ms` | `92.755 ms` | **`75.605 ~ 80.414 ms`** (min **`75.331 ms`**, **13.3 FPS**) | **`4.79×` (`-79.1%`)** |
| **`1x Original 1080p`** (`1920×1152`) | 71 | `493.640 ms` | `354.928 ms` | `314.841 ms` | `131.765 ms` | **`109.105 ~ 114.590 ms`** (min **`108.532 ms`**, **9.2 FPS**) | **`4.52×` (`-77.9%`)** |

- 全部 4 组测试 `invalid (NaN/Inf) = 0`，首尾帧 `bit_diff = 0`，`SP_STATS fallback = 0, errors = 0`，4 个档位输出 FNV-1a 64-bit 哈希（`48eed0c7f7b18978`、`d463648c43236f7d`、`2902af99e603e14d`、`17469c9b18bbbc8a`）与 Exact 黄金基准 **逐比特 100% 一致 (`0 bit-diff`)**。

#### 4.2 Windows 11 实机 `frame.exe`（D3D12 编解码 + D3D12-CUDA 共享显存/Fence 互操作 + 神经网络推理）端到端实测

| Windows D3D12 + CUDA 实测档位 | 块数 | 处理分辨率 | 稳态 Min Wall (`ms`) | 稳态 Median Wall (`ms`) | 帧率 (`FPS`) | `invalid` | 首尾帧 `changed` | 输出亮度 (`luma` / `roi`) |
|:---|---:|:---|---:|---:|---:|---:|---:|:---|
| **`0.5x Small 900p`** (`flags_900_05x.flags`) | 31 | `1600×1024` | **`46.257 ms`** | **`47.821 ms`** | **21.6 FPS** | `0` | `0` (`maxabs=0`) | `1.161911` / `1.149981` |
| **`0.5x Small 1080p`** (`same.flags`) | 31 | `1920×1152` | **`62.993 ms`** | **`64.230 ms`** | **15.9 FPS** | `0` | `0` (`maxabs=0`) | `1.161226` / `1.149793` |
| **`1x Original 1080p`** (`flags_1080_1x.flags`) | 71 | `1920×1152` | **`113.946 ms`** | **`115.254 ms`** | **8.8 FPS** | `0` | `0` (`maxabs=0`) | `1.168327` / `1.156113` |

- 含 D3D12 Encode、D3D12 Direct Input、CUDA Shared Resource/Fence Handoff、31/71-Block Neural Network、D3D12 Neural Texture、D3D12 Decode 与 Readback 完整链路，D3D12 编解码与跨 API 同步总开销仅 **`~1.5 ms/frame`**。

#### 4.3 `0.5x Small 1080p` (`1920×1152`) 完整 32 核属性与耗时普查表（32/32 核 `LMem = 0 B`，Total = `61.278 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
c32_wave1_prefix_b8d_w16                             1     8.368    8368.1  34560    32  178      0  10240     9
c32_wave1_post_b8_w16                                1     7.413    7412.7  34945    32  177      0  10240     9
vit_stream_qkv_frag_bin_w5f8                         8     4.244     530.5    768   160  135      0  16384    15
vit_stream_contract_frag_bstream_bout_compactw_w16   8     3.928     490.9    640    32  162      0   4096    12
c256_wave2_bi_bo_w16                                 3     3.390    1130.1    135   256  240      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.189     398.6   2560    32  119      0      0    16
c128_wave2_bi_bo                                     2     2.701    1350.7    540   128  248      0  24576     8
vit_attention_fused_640_bytein_bout                  8     2.072     258.9   1280    32  122      0      0    16
c64_wave2_bi                                         1     2.049    2048.9   2220    64  248      0  12288     8
c32_wave1_up_b8_w16                                  1     2.042    2041.9   8712    32  234      0  10240     8
c64_wave2_up_lb_sh                                   1     1.995    1994.8   2196    64  247      0  12288     8
c32_wave1_finish_dcrop_b8d_w16                       1     1.977    1977.3   8833    32  168      0  10240     9
c32_wave1_mapped_b8_w16                              1     1.883    1883.1   8640    32  170      0  10240     9
c64_wave2_bi_ho                                      1     1.850    1850.4   2257    64  247      0  12288     8
c32_wave1_finish_b8_w16                              1     1.804    1804.3   8760    32  168      0  10240     9
c64_wave2_bi_bo                                      1     1.741    1740.7   2160    64  248      0  12288     8
c128_wave2_up_lb_sh                                  1     1.533    1532.9    558   128  247      0  24576     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.503     187.9    640    32  218      0      0     9
c128_wave2_bi_ho                                     1     1.466    1466.4    589   128  247      0  24576     8
c256_wave2_bi_w16                                    1     1.443    1442.8    160   256  240      0  49152     8
c512_qkv_attention_compact_w16                       4     1.133     283.4    640    64  229      0   6144     8
split_ffn_one_w2f8_w16_bin                           4     0.896     224.0    544    64  149      0      0    12
mh_attention_project_frag_c512_w16_u4_bout           3     0.427     142.5   1080    32  133      0      0    15
split_projection_frag_w16_bskip                      4     0.398      99.5   1080    32  135      0   1024    15
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.376     187.9   1280    32   71      0   2176    16
mh_attention_project_frag_c512_w16_u4                1     0.143     143.4   1080    32  133      0      0    15
mh_pool_project_c32_b8_out8                          1     0.135     135.2  34560    32   44      0      0    16
mh_pool_project_group_c64_hin_out8_f8w16             1     0.116     115.7   2160    64  121      0   1152    16
mh_pool_project_group_c256_out8_f8w16                1     0.086      86.0    135   256  121      0   4224    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.084      84.0    540   128  121      0   2176    16
mh_pool_project_group_c512_out8_f8w16                1     0.077      76.8     40   512  121      0   8320    16
vit_gather_b8                                        2     0.025      12.3    640   256   16      0      0   128
```

#### 4.4 `1x Original 1080p` (`1920×1152`) 完整 35 核属性与耗时普查表（Total = `111.300 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
sp_run256_w16                                        2    15.208    7604.2    893   256  255    576  49152     8
c128_wave2_bi_bo                                    10    13.612    1361.2    540   128  248      0  24576     8
c64_wave2_bi_bo                                      5     8.818    1763.7   2160    64  248      0  12288     8
c32_wave1_prefix_b8d_w16                             1     8.702    8702.0  34560    32  178      0  10240     9
c32_wave1_post_b8_w16                                1     7.589    7588.9  34945    32  177      0  10240     9
c32_wave1_chain_w16                                  4     7.290    1822.4   8833    32  162      0  10240     9
c512_qkv_attention_compact_w16                      16     4.602     287.6    640    64  229      0   6144     8
vit_stream_qkv_frag_bin_w5f8                         8     4.315     539.4    768   160  135      0  16384    15
vit_stream_contract_frag_bstream_bout_compactw_w16   8     4.091     511.4    640    32  162      0   4096    12
split_ffn_one_w2f8_w16_bin                          16     3.593     224.6    544    64  149      0      0    12
c256_wave2_bi_bo_w16                                 3     3.462    1154.0    135   256  240      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.187     398.3   2560    32  119      0      0    16
c64_wave2_bi                                         1     2.162    2161.7   2220    64  248      0  12288     8
mh_attention_project_frag_c512_w16_u4_bout          15     2.157     143.8   1080    32  133      0      0    15
vit_attention_fused_640_bytein_bout                  8     2.071     258.8   1280    32  122      0      0    16
c32_wave1_up_b8_w16                                  1     2.052    2052.1   8640    32  234      0  10240     8
c32_wave1_finish_dcrop_b8d_w16                       1     2.029    2028.5   8760    32  168      0  10240     9
c64_wave2_up_lb_sh                                   1     1.990    1989.6   2160    64  247      0  12288     8
c32_wave1_mapped_b8_w16                              1     1.969    1969.2   8640    32  170      0  10240     9
c64_wave2_bi_ho                                      1     1.882    1882.1   2220    64  247      0  12288     8
c32_wave1_finish_b8_w16                              1     1.817    1816.6   8760    32  168      0  10240     9
split_projection_frag_w16_bskip                     16     1.597      99.8   1080    32  135      0   1024    15
c128_wave2_up_lb_sh                                  1     1.533    1532.9    558   128  247      0  24576     8
c256_wave2_bi_w16                                    1     1.507    1507.3    150   256  240      0  49152     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.502     187.7    640    32  218      0      0     9
c128_wave2_bi_ho                                     1     1.501    1501.2    589   128  247      0  24576     8
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.369     184.3   1280    32   71      0   2176    16
mh_attention_project_frag_c512_w16_u4                1     0.145     145.4   1080    32  133      0      0    15
mh_pool_project_c32_b8_out8                          1     0.135     134.9  34560    32   44      0      0    16
mh_pool_project_group_c64_hin_out8_f8w16             1     0.118     117.5   2160    64  121      0   1152    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.085      85.0    540   128  121      0   2176    16
mh_pool_project_group_c256_out8_f8w16                1     0.080      79.9    135   256  121      0   4224    16
mh_pool_project_group_c512_out8_f8w16                1     0.079      78.6     40   512  121      0   8320    16
vit_gather_b8                                        2     0.024      12.2    640   256   16      0      0   128
sp_recover256_w16                                    2     0.020      10.2      1   256  255    736  49152     8
sp_init                                              2     0.009       4.6     11   256   10      0      0   128
```


---

## 2026-10-24 (Phase 7: 原版 `310.9.16.0` `nvngx_dlssnr.dll` 满血 `O4` PTX 修补、同机对决与《鬼武者：剑之道》实机验证)

### 1. 范围收敛：RTX 30 系仅保留 31 层轻量新模型 (`0.5x Small` / `Preset 2`)
- 确定工程与发布方针：在 RTX 3080 Laptop (`sm_86`) 等 Ampere 移动/桌面显卡上，舍弃沉重的 71 层旧模型（`310.8.0.0`），全线仅保留并维护 `310.9.16.0` 的 **31 块 `0.5x Small` 新模型（`Preset 2`）**。

### 2. 原版 `310.9.16.0` (`nvngx_dlssnr.dll`) 的 `sm_86` 满血 `O4` PTX 修补 (`Development/ptx-patcher/`)
- **上游 `dev-camo/dlssnr-patcher` 在 `310.9.16.0` 上的两大缺陷**：
  1. `310.9.16.0` 的 Fatbin 5 新增了 `sm_90+` 专属指令 `fence.acquire.gpu;`，上游脚本未处理导致 `nvptxcompile` 在 `sm_86` 上直接报错退出；
  2. 上游脚本将每条 `cvt.rn.f16x2.e4m3x2` / `cvt.rn.satfinite.e4m3x2.f16x2` 展开为 45~48 行纯整数位运算 PTX，导致生成的 `.cubin` 体积暴涨 3.5 倍（`6.7 ~ 8.5 MB`），远超 PE 原始 Fatbin 槽位容量，被迫在全部主力网络核（Fatbin 00~06）上回退到 `--opt-level=1`（`O1`，禁用指令调度、循环展开与窥孔优化），导致推理性能腰斩。
- **我们的解决方案（`Development/ptx-patcher/build_sm86_dlls.py`）**：
  1. 将 `fence.acquire.gpu;` 自动降级为 Ampere `sm_86` 原生支持的 `fence.acq_rel.gpu;`；
  2. 提出并实现两条 **IEEE 754 `f16x2` 硬件指令恒等式（有限值域 `0 bit-diff`）**：
     - **`E4M3x2 -> FP16x2`（仅 4 条 SASS 指令）**：利用 IEEE FP16 指数为 0 的非正规数 $(-1)^s \cdot 2^{-14} \cdot (m/8)$ 乘以 $2^8 = 256.0_{\text{f16}}$ (`0x5c00`) 后由硬件 FPU 自动归一化并使正规数指数 $e - 15 + 8 = e - 7$ 的代数恒等式，用 `prmt.b32` + 位移掩码 + `mul.rn.f16x2 %d, %t, 0x5c005c00;` 替代 48 行位运算，覆盖全部 254/254 有限值 0 误差；
     - **`FP16x2 -> E4M3x2`（硬件 RNE 非正规数舍入）**：利用 FP16 中 `2.0h` (`0x4000`) 的最低有效位 $\text{ULP}(2.0_{\text{f16}}) = 2^1 \times 2^{-10} = 2^{-9}$ 恰好等于 E4M3 非正规数最低有效位 $2^{-9}$ 的性质，用单条 `add.rn.f16x2 sub2, sub_in, 0x40004000;` 同时完成两个通道的非正规数向偶舍入（63,488 个有限 FP16 输入值 100% 精确匹配）。
  3. 凭借紧凑的指令体积（`.cubin` 缩小至 `2.1 ~ 2.8 MB`），`310.9.16.0` 中的 **15/15 个 Fatbin 全部在 `--opt-level=4`（满血 `O4`）下一次编译通过并原位塞回 PE 槽位**。

### 3. 三套方案在 RTX 3080 Laptop (`sm_86`, 132W) 上的同口径实测对决（全为 31 层新模型）
通过 `Development/ptx-patcher/bench_nvngx.dll.cpp`（调用名 `nvngx.dll_runner` 满足 NGX 调用者校验，使用 D3D12 硬件 Timestamp Query 测量 `NVSDK_NGX_D3D12_EvaluateFeature(Feature 18, Preset 2)`）：

| 方案（同一 31 块 `0.5x Small` 模型） | 编译器优化 | `1600×900` (900p) 单帧耗时 | `1920×1080` (1080p) 单帧耗时 | 画面准确度 (`PSNR`) | 相对 `stock` 提速 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **① 网上 `dlssnr-patcher` 原版位运算改法 (`stock`)** | 被迫降级 `O1` | `49.89 ms` min (`50.10 ms` med / `20.0 FPS`) | `67.69 ms` min (`68.54 ms` med / `14.8 FPS`) | 基准（含上游 `mapped` 色带 Bug） | `1.00×` |
| **② 独立 CUDA 引擎 (`LmxxfNrRuntime.dll` V5/V6)** | `Clang O3 + PTX O4` | `43.10 ms` min (`43.26 ms` med / `23.2 FPS`) | `57.13 ms` min (`57.45 ms` med / `17.5 FPS`) | 独立引擎黄金哈希 `0 bit-diff` | `1.18×` |
| **③ 硬件指令 PTX 补丁 (`nvngx_dlssnr_sm86_fast.dll`)** | **15/15 满血 `O4`** | **`23.97 ms` min** (`24.32 ms` med / **`41.7 FPS`**) | **`29.97 ms` min** (`31.51 ms` med / **`33.3 FPS`**) | 与 `stock` `100.00%` 逐位一致（注：晚间修复上游 `mapped` 色带 Bug 后最终生产版 SHA256 为 `3f934a0a...`，见下方章节） | **`2.08× ～ 2.25×`** |

- **根因总结（为何原版 PTX 补丁 `fast` 比 RDNA4 移植的独立引擎快 `1.8×`）**：
  1. **GeForce 30 系硬件砍半限制**：在消费级 GA102/GA104 上，`mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16`（FP16 累加，原版 PTX 所用）为 Full Rate（512 FLOPs/clock/SM），而 `.f32.f16.f16.f32`（FP32 累加，RDNA4 移植版所用）被硬件限制为 Half Rate（256 FLOPs/clock/SM，吞吐量减半且累加器占 8 个寄存器 vs 2 个寄存器）；
  2. **原生线程座位**：原版 PTX 天然按 Ampere Warp32 `mma.sync` 座位排布（0 次跨线程 `shfl.sync`），而 RDNA4 移植版需在 RDNA4 Wave32 与 Ampere Warp32 座位之间执行洗牌。

### 4. 《鬼武者：剑之道》（Xbox 版）实机安装与验证
- 安装路径：`/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/`
- 安装文件：`dinput8.dll`（REFramework）、`dxgi.dll`（OptiScaler）、`OptiScaler.ini`、`nvngx.dll_dlssnr.dll`（转发桥）、`nvngx_dlssnr.dll`（初版 `f9465639...`，晚间修复天空色带后已更新为最终生产版 `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`）。
- 关键配置校准（`OptiScaler.ini` `[DlssNr]`）：
  - 必须保持 **`WhitePointSource=1`**（读取游戏原生曝光纹理，`paper white ≈ 512x`），因为 RE Engine 的线性 HDR 缓冲区数值在 `0 ~ 512` 之间；若设为 `WhitePointSource=0, WhitePointScale=1.0`，未归一化的高值会触发 `dlssnr.hlsl` 中 `ToOkLab` 的溢出偏绿（`the green tint`）并淹没细节分支；
  - 设置 **`Preset=2, Style=1`**（启用 31 层新模型的 Natural 神经重打光风格）。
- 实机性能表现（2560×1440 2K 显示分辨率）：
  - **2K 极高帧率档（Ultra Performance，内部渲染 `854×480`）**：DLSS 5 模型耗时 **`7.3 ~ 9.1 ms`**，整机实测 **`46 FPS`**；
  - **2K 帧率优先档（Performance，内部渲染 `1280×720`）**：DLSS 5 模型耗时 **`16.7 ~ 17.7 ms`**，整机实测 **`30 FPS`**。

### 5. 目录隔离与本地构建产物坐标（已完成）
- **仓库目录结构（已收拢完成）**：
  - `Development/ptx-patcher/`：主推路线（原版 `310.9.16.0` `nvngx_dlssnr.dll` 内置 PTX 的满血 `O4` 转换器及 `sky-audit/`、`release-rtx30/`、`magpie-native/`、`magpie-fix/` 子目录）；
  - `Development/hip-port/`：附加路线（`RDNA4 -> Ampere` 独立 HIP/CUDA 引擎移植方案）。
- **本地构建产物与底包坐标（位于 `/mnt/c/DLSS5-5090-dll/`）**：
  - 原版未改 DLL：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll`（SHA256 `2bc19bc0...`）
  - 满血 `O4` 最终生产版 DLL：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll`（SHA256 `3f934a0a...`）
  - 对照 `O1` 版 DLL：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_stock.dll`（SHA256 `fca63d10...`）
  - 独立 CUDA 引擎二进制：`/mnt/c/DLSS5-5090-dll/LmxxfNrRuntime.dll`、`/mnt/c/DLSS5-5090-dll/dlss5-amd.addon64`（及 `/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/` 下的 40 个 `sm_86` 模块）
  - 0.44 上游打包底包：`/mnt/c/DLSS5-5090-dll/amd的dlss5-0.44的打包/`
  - `v0.1.0` 正式发布包目录：`/mnt/c/DLSS5-5090-dll/发布打包/`（已上传至 `https://gofile.io/d/s9cpHYH9`）

## 2026-10-24 晚：天空红绿横带根因修复（safe mapped，15/15 O4）

- 反证更新：fast与stock逐位一致仅说明共享补丁一致，不能证明画面正确。关闭mapped消除天空横带；仅补回量化仍有104次红绿变号，不能将问题仅归为“少了量化”。
- Zero指出FB5 `cc_vit_attention_fp8` 的 `%r1352` 有真实向量load与越界fallback pack两种定义。旧`fp8_pack_sources`只统计特定pack/cvt形态，错误地将真实显存数据替换为fallback值。新增按指令解析的定义表与基本块边界检查，剔除多定义、跨块、受谓词控制及无法局部证明的替换；合法mapped保留，同时精确量化。
- 全量15个Fatbin全部O4；FB0/1/2/4超过旧槽位，通过新增`.dlssptx` PE节并重定位唯一宿主引用容纳，NGX实际加载及全部基准通过。
- 天空1280×720，preset2/style1：红绿色差变号0次，高频RMS=0.00010052723；同轮旧fast为106次、0.027630752。全部nonfinite=0。
- 5帧预热、20帧测量：safe GPU median 720p天空23.751ms、900p原bench场景33.034ms、1080p原bench场景43.418ms；同轮旧fast15.972/24.563/31.957ms。**正确性与全O4已恢复，旧速度尚未恢复。**
- 两通道各63,488个有限FP16编码GPU穷举零差异；6项mapped规则回归通过。源码构建入口已移除/tmp依赖并加入原DLL哈希门控。
- 新DLL SHA256 `7c8631871811c8bb3d98f87778917e9fc92f010d3db304f8f9bef0f822f16bf7`；旧版 `f94656391b63dc744c0275b8f2cc5c1254ac104d11dbc44222981fa31e64237d`。
- 细节、部署回执及恢复位置见 `sky-audit/安全mapped最终回执.md`。真实游戏画面观感仍需Zero进游戏验收；本轮未启动游戏。

## 2026-10-24 后续控制变量：仅拒绝多定义、不加量化，性能恢复并部署

- Zero要求把严格过滤和额外量化拆开。strict_nq与multidef_nq均15/15 O4原槽位装入，无需新增PE节；天空红绿变号均0次。
- strict_nq GPU median（720p天空/900p原bench/1080p原bench）17.886/31.756/37.113ms。
- multidef_nq对应15.829/24.474/32.036ms，高频色差RMS=.000102701，nonfinite=0；已恢复旧fast速度范围。
- 当前生产默认拒绝entry内pack目标、FP8中间值、FP16来源多定义的mapped，允许单定义跨块；通过检查后恢复原shfl/shfl/selp，不附加量化。保留严格过滤及量化诊断开关。生产PTX与通过实测的控制版FB0..6逐字节相同；8项回归通过。
- 已替换主fast与游戏DLL，SHA256 `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`。上一版量化safe已另存恢复，不覆盖更早备份。详见 `sky-audit/去量化控制变量回执.md`。

## 2026-10-24 RTX30 三包首次组装与《剑星》完整部署

- `C:\DLSS5-5090-dll\发布打包` 三个 `0.1.0` ZIP（基于上游 AMD `0.44` 底包）及逐包 `.sha256`、总 `SHA256SUMS.txt` 完成首次组装：初版包 A（Magpie）先按 CUDA 独立引擎（路线 A）打包验证，包 B（REFramework）与包 C（常规 OptiScaler）采用 15/15 `O4` PTX 路线（路线 B）。（注：随后在下方章节中，包 A Magpie 亦升级切换为原生 Feature 18 PTX 路线 B，故最终发布的三个包全员统一为路线 B）。
- 包 B/C 去除 AMD 独立引擎目录/runtime，保留完整辅助 DLL（26 KB `amd_fidelityfx_dx12.dll` loader + 28 MB `amd_fidelityfx_upscaler_dx12.dll` + XeSS/NvAPI 辅助库）；显式开启 FFX 输入、固定 DLSS 输出，Windows API smoke 实测 `FFX -> NGX -> NR` 的 `ready/composition` 和有限输出通过。
- 《剑星》常规包默认单遍 `TransferStrength=1.5 / ColourStrength=1.1`，另附 `1.0 / 1.0` 平衡配置（`OptiScaler-原始平衡.ini`）；保持游戏原生曝光（配对白点 `~1.0x`），不照搬《鬼武者》的 `520x`。
- 《剑星》目录（`/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64/`）同步 37 个文件，原始 6.6 MB `amd_fidelityfx_dx12.dll` 及 INI 备份至 `C:\DLSS5-5090-dll\backups\20261024-StellarBlade-full`，Zero 实玩验证通过。

## 2026-10-24 Magpie 路线 A 过渡排查与切换至原生 Feature 18 / PTX 路线 B

- **阶段 1（路线 A 过渡排查，`ptx-patcher/magpie-fix/`）**：
  - 排查初期 Magpie 选 `DLSS_SR` 报 `0xbad0000b` 原因为目录缺少 `nvngx_dlss.dll`；补入《剑星》自带 `nvngx_dlss.dll`（SHA256 `83de996b...`）并将预设改为 `FSR3 1x -> DLSS_SR`、修复 `dlss5-amd.addon64` 的 Present 等待与 FFX 双导出 Hook 后，《光环》720p→4K 跑通，但因路线 A 受限于 GeForce 30 系 FP32 累加 Tensor Core 砍半，单帧回调耗时中位数为 **`49.8 ms`（约 `20.08 FPS`）**。
- **阶段 2（发现并打通 Magpie 原生 `DLSSNR` Feature 18 / PTX 路线 B，`ptx-patcher/magpie-native/`）**：
  - 检查 `Magpie.exe`（定制 `0.6.6`）符号表发现其原生内置 `DLSSNR\DLSSNR_AI_Filter`（`DLSSNRFilter.cpp`），可直接加载 `nvngx_dlssnr.dll` 调用 Feature 18 并自带 caller IAT 绕过。
  - 原生 `DLSSNRFilter.cpp` 将 `DLSSNR.Hint.Render.Preset` 硬编码为 `0`（71 层老模型）；通过 [`ptx-patcher/magpie-native/patch_preset2.py`](ptx-patcher/magpie-native/patch_preset2.py) 对 `Magpie.exe`（原 SHA256 `ec0a90fc...`）施最小代码洞补丁，将 `Preset` 调用固定改为 **`2`（31 块 Small 模型）**，产出补丁版 `Magpie.exe`（SHA256 `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea`）。
  - 正式覆盖部署至 `C:\DLSS5-5090-dll\发布打包\Magpie-DLSS5-RTX30-0.1.0\`，移除旧 ReShade `dxgi.dll`、`dlss5-amd.addon64` 与 `DLSS5-AMD/` 外置权重，默认预设设为 **`DLSS5-RTX30-PTX`（`原生 DLSSNR [Preset 2, Style 1] -> DLSS_SR`）**。
- **阶段 3（《光环》720p→4K 实机分段计时与 60Hz 电视 VSync 台阶机制分析）**：
  - 23:06 Zero 实测《光环》720p 窗口 → 4K 电视全屏（连续 480 帧 `magpie.log` 硬件计时）：
    - `slotWait = 0.002 ms`、`inputPrepare = 0.003 ms`、`evaluateCPU = 0.478 ms`；
    - **`evaluateGPU`（DLSS 5 31 块模型纯 GPU 耗时）= `15.95 ms`**（相比路线 A 的 `49.8 ms` 提速 **3.1 倍**）；
    - **`publication fence`（含 `15.95 ms` DLSS 5 + `~5.25 ms` 后级 4K `DLSS_SR` 与同步的总 GPU 耗时）= `21.20 ms`**（纯 GPU 吞吐对应 `47.2 FPS`，无锁频动画窗口实测约 `36 FPS`）；
    - **60Hz 电视同步捕获台阶**：在 60Hz 电视（周期 `16.67 ms`）上，由于 Magpie 的 `WGC 捕获 -> CPU 等待 publication fence (21.20 ms) -> Present` 为同步串行循环，单帧 `21.20 ms` 跨过了第一个 `16.67 ms` VBlank，需等待 `11.6 ms` 到第 2 个 VBlank（`33.33 ms`）采样下一帧，故稳态帧间隔落在 **`32.81 ms`（`30.48 FPS`）**。若需在 60Hz 电视上跑满 60 FPS，可在配置末尾勾选 `XeSSFG 2x` 帧生成或将窗口调至 `960×540` 使总耗时压入 `16.67 ms` 内。

## 2026-10-24 PTX 主线目录收拢与 `v0.1.0` 正式发布定版

- **目录结构收拢**：`Development/` 顶层严格只保留 `DevHistory.md`、`WorkingPlan.md`、`ptx-patcher/`、`hip-port/`（及公众号说明 `doc/使用说明.md`）；`sky-audit`、`release-rtx30`、`magpie-native`、`magpie-fix` 全部收归 `Development/ptx-patcher/` 子目录。
- **三个 `v0.1.0` 正式发布包最终校验值（已上传至 `https://gofile.io/d/s9cpHYH9`）**：
  - `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`：`376,272,150 B`，SHA256 `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67`
  - `OptiScaler-DLSS5-RTX30-0.1.0.zip`：`319,200,566 B`，SHA256 `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac`
  - `Magpie-DLSS5-RTX30-0.1.0.zip`：`324,124,886 B`，SHA256 `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb`
- **文档体系**：根目录 `README.zh-CN.md`、`README.md`、`CHANGELOG.zh-CN.md`、`CHANGELOG.md` 与公众号文章 [`Development/doc/使用说明.md`](doc/使用说明.md) 全部对齐 `v0.1.0` PTX 主线并推送至 `origin/main`。

## 2026-10-25 hip-port Phase 1：packed FP16 MMA 首轮实现与实测（数值通过，性能未达预期）

### 改动与验证

- v0.1.0 `ptx-patcher` 与三个发布包保持归档，本轮没有替换共享 assets、游戏或 Magpie DLL。
- 独立引擎 `hip/sm86_compat.h` 的核心改为两条 `mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16`；Ampere 累加器使用 `sm86_u4`，布局 `{pack(ad0,ad1),pack(ad2,ad3),pack(ad4,ad5),pack(ad6,ad7)}`。A/B 准备和 E4M3 解包未改。
- `__sm86_c_to_ampere` 返回 `<4 x i32>`，`__sm86_d_to_rdna4` 接收 `<4 x i32>`。SSA pass 同步改写直接抵消、零初值、循环/diamond PHI、LCSSA 出口；修正整数返回 call 不得携带 `contract` 浮点标志的问题。`test_packed_acc_ir.py` 两项实际 LLVM verifier 回归通过。
- 全量 **40/40 模块、1898 个 kernel entry CUDA 加载验证通过**。40 个生产 PTX 合计 64,524 条 FP16 累加 MMA，旧 `.f32.f16.f16.f32` MMA 为 0。模块逐文件 SHA256 已保存。
- `wmma_validate_cuda --fp16-acc`：**63 组测试，failures=0、FP8/FP16 输入路径 bitdiff=0、half_diff=0**；包含 K16/K32、非零 C、32 个 K basis、整数及有界随机测试。非整数测试允许 FP16 累加误差；最大 CPU absolute error 0.0704956055。会溢出 FP16 的全值域 FP8 压力案例不在此模式内，原 F32 验证模式保留。

### 同机整网数值与耗时

- GPU：RTX 3080 Laptop，CUDA Driver 13040；同一 **140 W 上限**，默认 DVFS、未锁频。全轮 >=90% 利用率样本的功耗中位数 138.74 W、SM 时钟中位数 1695 MHz、显存 7001 MHz；原始遥测保留，不能把 1% 左右差异宣称为稳定加速。
- Small 31-block、Style 1；既有确定性 RGB 图案；关闭 Graph/adaptive reuse；初始化、输入上传和最终读回不计入 GPU event 时间。
- 最终 **50 帧预热、80 帧测量**；另采一帧核级 profile。1080p/900p 标签实际处理尺寸分别为 **1920×1152 / 1600×1024**，并额外对前 1080/900 行可见区域计算精度。基准 F32 输出 hash 与先前快照一致。

| 档位 | F32 GPU min / median ms | FP16 GPU min / median ms | median 比值 F32/FP16 | 可见区域 PSNR（peak=1） | maxabs | invalid |
|---|---:|---:|---:|---:|---:|---:|
| 900p | 45.725 / 46.190 | 45.046 / 45.444 | 1.016× | 46.6216 dB | 0.03801733 | 0 |
| 1080p | 60.548 / 63.342 | 60.024 / 63.264 | 1.001× | 46.1852 dB | 0.04758018 | 0 |

- 全 padded 区域 PSNR：900p 46.5913 dB、1080p 46.1542 dB；两档 `bit_diff_first_last=0`，确定性稳定。达到本次 >=45 dB 门槛，但不是 bitwise 等价，也不是游戏画面观感验收。
- 核级插桩累计：1080p **60.2061→60.9556 ms**（32 个活跃核），900p **45.2925→46.4978 ms**（34 个变体）。与未插桩整网时间分开看，不混算。

### 寄存器收益和回退

- 1080p 的 32 核：**21 核 Regs 降低、8 核升高、3 核不变**；OccW 上升 6 核、下降 3 核；LMem 为零的核从 32/32 回退为 **31/32**。
- C64/C128 主要 wave2：248→239、247→223/239，但大多仍 **OccW=8**，未跨过资源占用率门槛；C256 240→241，OccW 仍 8。
- `vit_stream_qkv_frag_bin_w5f8`：135→122 regs、OccW 10→15；`split_projection`：135→127、OccW 12→16；C512 attention projection：133→125、OccW 12→16。
- pool C64/C128/C256：121→200 regs、OccW **16→8**；pool C512：121→128 regs，新增 **104 B LMem**。这是真实回退，不能写成“全网寄存器减半/零溢出”。
- 本轮为了单独检验核心精度，C/D 边界仍使用旧 **8 次 scalar shuffle** 后打包/解包；K32 的 Hrtz 及 partition 的 FP32 求和保留原语义，通过 `_f32` 布局辅助函数维持。**尚未完成边界 4-shfl 与所有外围 K32/partition 的四寄存器化，Phase 1 性能目标未完成。** 新旧布局辅助路径之间的冗余转换、pool 的寄存器回退以及未提升的占用率是下一步要检查的具体对象；当前数据不足以将总耗时归因于某一个原因。

完整 **32/34 核 Regs、LMem、OccW 与耗时对照**、逐模块哈希、构建/验证/benchmark 日志、遥测和复测脚本见 [`hip-port/phase1/`](hip-port/phase1/README.md)，主表见 [`results.md`](hip-port/phase1/results.md)。候选 40 模块、F32 对照模块及 RGB 输出保存在该目录被忽略的 `artifacts/` 内；尚未部署为稳定运行时。结论：**核心类型改写和数值门槛通过，第一轮没有获得明确端到端性能提升，继续以此负结果定位外围转换与资源占用，而不是宣称满速翻倍。**

## 2026-10-25 hip-port Phase 2：静态权重预洗牌 + 精确 ones 特化 + packed 分段累加

### 完成的实现与小测试

- Host `packed_weights.h` 增加 `AmperePreshuffleTile256` / `AmperePreshuffleTile512W16`；在最终 FragmentPackedMatrix/W16、C32/MH residual diagonal、QKV Frag8 打包处执行纯字节置换。GPU 对应静态 weight reader 改为 `sm86_unpack_e4m3x8`，动态 Q/K/V 和 row-major fallback 保留原 prep；覆盖 C32/W2、C512、ViT expand/contract/project/QKV staging、decoder、downsample/pool 的主用 fragment 路径。
- 基础 GPU/CPU 测试：64 个 256B tile（含唯一字节位置标签）、64 个 lo/hi 内容不同的 W16 tile，与 GPU 原 prep/preshuffle **0 bit-diff**；128 组整数/正负随机/非负随机输入、非零 C、连续4次 ones 累加对原 FP16 MMA **0 bit-diff**；4096 个线程片段的 packed add 对 FP32 加后 half RNE 打包 **0 bit-diff**。范围见 `hip-port/phase2/check_primitives.py`，不声称未测的非有限值/溢出情况等价。
- ones 方案的重要校准：直接 `half(sum16+c)` 不等价于当前 FP16 MMA。实验保留 K8 边界的 `half(sum_hi + half(sum_lo + half(c)))` 后通过上述逐 bit 对照。`ones_a` 只需1次 XOR16；**通用 RDNA4 布局的 ones_b 要输出8个不同 A 行，精确版本需要16次 idx 广播**，不是1次 shuffle。先合成总和的9-shuffle版本产生随机输入差异，未采用。`wmma(zero,zero,pre)` 已移除。
- `sm86_add_u4_f16x2` 用4条 packed add；pool 的跨 K32 chunk、ViT contract/stream project 与 decoder W16 的跨 partition 累加保持 `sm86_u4`。partition 从 FP32 和改为逐步 half 和的误差由整网 PSNR 验收。
- 修复构建缓存不跟踪兼容头/pass 内容的问题，并在结构改写前先展开预处理分支。最终 **40/40 模块、1898 个 entry 编译和 CUDA 加载验证通过**；新 Linux CUDA benchmark runner 已重编，未部署 Windows frame.exe。Host 和模块通过 `AMPERE_WEIGHTS_V2` 配对，误将新 Host 默认预洗牌搭配旧模块会明确拒绝；关闭开关跑 Phase 1 模块的输出哈希完全复现。

### 同机 Small 31-block 整网实测

同轮重新测量 Phase 1；Style1，默认DVFS、同一约140W上限，50帧预热/80帧测量。高利用率遥测功耗中位数137.77W、SM1695MHz、显存7001MHz。处理尺寸900p=1600×1024、1080p=1920×1152；GPU event 和 CPU Wall 均不计初始化、打包和传输/最终读回。

| 档位 | Phase 1 GPU min / median ms | Phase 2 GPU min / median ms | median 速度比 | Phase 2 Wall median ms | 对 F32 可见区域 PSNR | maxabs | invalid |
|---|---:|---:|---:|---:|---:|---:|---:|
| 900p | 44.461 / 44.872 | 41.743 / 42.264 | 1.0617× | 42.360 | 46.6206 dB | 0.03485873 | 0 |
| 1080p | 59.245 / 59.806 | 53.921 / 54.476 | 1.0978× | 54.585 | 46.1009 dB | 0.04160273 | 0 |

- 两档首/末帧 bit_diff=0；输出 FNV1a64：900p `b9577aa87bf709d6`、1080p `a8365381a41f7f83`。完整 padded 区域 PSNR 为46.5919/46.0816 dB，均过45dB门槛。相对 Phase 1 的可见区域 PSNR另保存在结果 JSON 中；整网不宣称0 bit-diff。
- 额外插桩帧累计：900p **43.9020→41.6553 ms（34核）**；1080p **58.8165→53.6494 ms（32核）**。与未插桩整网时间分开报告。
- 1080p pool：C64/C128/C256 从 **200→111 regs，OccW8→16**；C512从128→111 regs，**104B LMem→0**。恢复 **32/32 零 LMem**，900p亦34/34零LMem。
- 代表性1080p核累计：C32 prefix **8.1244→7.3697 ms**，post **7.3226→6.6785 ms**；C256 bi_bo **3.2758→2.7525 ms**；ViT expand **3.1549→2.8549 ms**，compact contract **3.6557→3.3864 ms**。
- 真实回退仍保留：wave2 多核寄存器升到250、OccW仍8；compact contract **154→217 regs、OccW12→8**；C512 attention projection与split projection的OccW16→12。32核中14核寄存器下降、15核上升、3核持平，不能写成“全网占用率提升”。
- 静态 PTX 指令示例（不是动态计数/SASS利用率）：C128 pool shfl **136→40**、selp **813→381**、packed add **0→16**；C32 prefix shfl **385→337**、MMA **96→76**。QKV静态权重 staging 确已零-shuffle unpack，但精确 ones_b 广播抵消其总shfl计数收益。三项改动组合实测，不单独归因各项加速贡献。

完整 [实验说明与复测入口](hip-port/phase2/README.md)、[32/34核分解表](hip-port/phase2/results.md)、原始日志、逐模块SHA256、遥测均归档于 `hip-port/phase2/`；二进制与RGB输出在其忽略的 `artifacts/` 内。**v0.1.0 PTX发布包、共享assets、游戏/Magpie运行时未替换。** 本轮取得稳定可见的约6%/10%速度提升与零溢出恢复，仍远未达到原生PTX路线的延迟，后续应继续围绕寄存器与核间/边界布局收敛。
- 最终长负载段时钟复查：Phase1 1080p/900p=1695/1695MHz，Phase2=1695/1710MHz；900p有约0.9%的Boost差异，速度比按默认DVFS实测报告，不冒充锁频等频结果。40模块缓存复查通过，完整数据见Phase2归档。

## 2026-10-25 hip-port Phase 3：三项实现完成，两个性能预期未兑现

### 实现和控制设计

- 按Zero建议增加noinline `__sm86_unpack_fp8`；WMMA wrappers和QKV staging均使用该入口。prep/unpack纳入同基本块CSE、零折叠，后置O3前再alwaysinline。LLVM verifier回归和GPU置换/ones/packed add测试通过。
- compact contract/projection移除fast_numeric与1920×1152限制，使用TierGeometry/free_geometry；保留其他设备/功能/导出检查。900p C256 wave2也放开，新增`DLSS5_LAB_COMPACT_ALL`和`DLSS5_LAB_C256_900`控制开关。
- C32把Q移到消费qt循环，K/V共享数组3→2平面。Q从原residual half值重建并沿用原运算顺序，避免跨qt缓存Q。
- 最终 **40/40模块、1898 entry编译/CUDA加载通过**；重编新benchmark runner。额外保留原3平面Q的deferred控制核，控制目录与完整候选**仅差一个fast C32模块**。两档最终Q重排对照 **0 bit-diff**。
- 开发中的两次错误已修正并留日志：最初文本定位误中同名残差part循环，后Q变量改名使新投影绕过预洗牌读入规则；错误候选未被计入通过数据。

### 最终同轮数据（50预热/80测量，Small31-block、Style1）

| 档位 | Phase2 GPU min / median ms | 全Phase3 GPU min / median ms | 保留共享Q控制 GPU min / median ms | 全候选/共享Q对F32可见PSNR | maxabs | invalid |
|---|---:|---:|---:|---:|---:|---:|
| 900p（处理1600×1024） | 41.506 / 41.929 | 41.139 / 41.879 | **40.632 / 41.009** | 46.9753dB | 0.04004550 | 0 |
| 1080p（处理1920×1152） | 53.505 / 54.067 | 54.925 / 55.420 | **53.683 / 54.370** | 46.1009dB | 0.04160273 | 0 |

三组均首末帧逐位一致；两档完整Phase3与共享Q控制逐位一致。完整组合没有净提速，1080p回退；当前较合适子集是保留共享Q、启用900p新门控。仍为32/32零LMem（900p从34种活跃核变为32种）。完整候选输出hash：1080p `a8365381a41f7f83`、900p `b949727e624db210`。

### 三项假设分别校验

1. **延后解包修法没有降低关键Regs**：deferred-only+旧门控与Phase2整网0bit-diff，但wave2仍250regs、compact contract仍217regs。cubin ELF `.text`核机器码比较：contract、QKV、ViT expand与Phase2逐字节相同；wave2大小同、字节不同但Regs未降。捕获的persistent原始IR里noinline保留、pass后alwaysinline生效，unpack calls1154→1154，没有额外CSE删除。不能把“加了noinline”写成已解决根因或拿模块hash变化充当核优化证据。
2. **900p门控确有小收益，C256保留**：20预热/40测量的共享Q控制，compact-only median41.230ms，再启C256 median40.750ms。C256 split累计3.807232ms→fused3.346432ms，省0.460800ms，输出逐位一致。新900p compact W16/inter-byte生效，`vit_pack_input`8次→0次。compact全路径不与旧900p逐位一致：除权重无损重排外，还选择了Phase2的W16 half-partition求和与byte入口/出口组合；实际PSNR已单独通过。
3. **C32资源目标达到，性能目标未达到**：SMem10240→8192B；五个核OccW8/9→11。prefix/post/mapped regs169→146、160→152、146→152；finish/dcrop145regs；up225regs仍OccW8。新增residual读入、重新打包/预洗牌是实际成本；理论占用率上升没有转化为本轮延迟收益。8KB local-Q保留实验，不作为当前最快组合推广。

默认DVFS、约140W上限、未锁频、显存7001MHz。六个长负载段SM中位数：Phase2 1710/1740MHz，共享Q1710/1725MHz，local-Q1725/1710MHz（每组1080p/900p），完整遥测留档。不宣称严格等频因果结论。

详见 [`hip-port/phase3/README.md`](hip-port/phase3/README.md)、[32核分解表](hip-port/phase3/results.md)、三组原始日志、编译/机器码证据、SHA256及复测脚本。候选与对照均在忽略的artifacts目录；共享assets、游戏与v0.1.0发布包未覆盖。

## 2026-10-25 hip-port Phase 4：预初始化修复 + qt滚动 + C64/C128 W16

以Zero指定的 **Phase3共享Q+900p新门控** 为基线，C32源码恢复共享Q默认，未沿用8KB local-Q候选。

### 分步结果与保留项

1. **ViT预初始化修复保留**：contract/project的float total在进入partition循环前转换为packed_total；删除循环内`if(part==part0/p==0)`对旧f8 total的读取。contract **217→150regs**、project **210→155regs**，OccW均8→12、LMem=0；两档0bit-diff。900p核累计contract2.755584→2.178048ms，project1.087488→0.893952ms；1080p3.372032→3.309568ms、1.383424→1.362944ms。
2. **Stage3两处qt禁止展开保留**：代表C64/C128核机器码237568→173184B、C256267648→198272B；0bit-diff、实际LMem=0。峰值Regs仍250、OccW仍8，未达到168以内目标；该改动缩小代码，没有解决全部峰值活跃区间。
3. **显式kt滚动不保留**：单独试了QKV kt，再试Stage1/2/3/5等全部相关kt。9个实际活跃wave2核的SASS机器码与只滚动qt版本逐字节相同，无额外收益。后SSA代表核已有28/36个u4 PHI且f8 PHI=0，不把packed PHI计数误当总Regs下降。
4. **小通道W16/双qt复用保留**：`c64-wave2`与`c64-wave2-fast`均设`W2_FFN_W16_SMALL 3`、`W2_FFN_QT_SMALL_MASK 3`。Host实际选用新增C64/C128 `_w16` 导出，输出0bit-diff、32/32零LMem。1080p C128 bi_bo2.373632→2.059264ms、C64 bi_bo1.500160→1.348608ms；900p分别1.927168→1.583104ms、1.124352→1.011712ms。wave2仍250regs/OccW8，未宣称寄存器瓶颈已解决。

可选的“将running total直接作为partial MMA初值”经过GPU反例检查：partial先+2048再−2048，独立partial再加1得到1，seeded MMA得到0，256个输出均复现。它改变了FP16舍入边界，因此没有作为等价SSA消除纳入本轮0bit路线；基础置换/ones/packed add测试仍通过。

### 最终同轮成绩（50预热/80测量，Small31-block、Style1）

| 档位 | 共享Q基线 GPU min / median ms | Phase4 GPU min / median ms | median速度比 | Phase4 Wall median | 对F32可见PSNR | maxabs |
|---|---:|---:|---:|---:|---:|---:|
| 900p（处理1600×1024） | 40.364 / 40.793 | **38.763 / 39.442** | 1.0343× | 39.521ms | 46.9753dB | 0.04004550 |
| 1080p（处理1920×1152） | 53.460 / 54.126 | **52.252 / 52.845** | 1.0242× | 52.942ms | 46.1009dB | 0.04160273 |

两档对所选基线 **0bit-diff、首末帧bit_diff=0、invalid=0、32/32实际CUDA LMem=0**。输出FNV保持900p `b949727e624db210`、1080p `a8365381a41f7f83`。额外插桩帧核累计900p40.535040→38.511616ms、1080p53.289984→51.993632ms，与未插桩整网时间分开报告。

最终默认配置重编 **40/40模块、1918 entry CUDA加载通过**（比之前多20个小通道W16导出）。最终模块在`hip-port/phase4/artifacts/selected/modules/`，源码保留获益改动。Host实现未变，runner沿用已验证版本；复测脚本支持从源码重编。

默认DVFS、约140W上限，未锁频；基线1080p/900p长负载SM中位数1710/1740MHz，候选1695/1710MHz，显存7001MHz。具体频率/功耗已留档，速度比不冒充锁频测试。

完整[Phase4说明](hip-port/phase4/README.md)、[32核分解表](hip-port/phase4/results.md)、分步日志、有效编译参数、SSA/SASS证据、哈希与复测脚本均已归档。共享assets、游戏/Magpie和v0.1.0发布包未覆盖。**当前独立引擎最优测试基线升级为Phase4 selected；wave2 250regs仍是明确未解决项。**

## 2026-10-25 hip-port Phase 5：4-u32 Benes + 受约束的寄存器Q

### 先独立验证向量化

- 替换C/D映射为Zero提出的4-u32半精度Benes，保留scalar f32实现作测试参考。D→RDNA4每位置遍历65536种half位模式、256位置；C→Ampere测试16777216随机FP32位模式，均0bit-diff。`wmma_validate_cuda --fp16-acc` 63组零失败、FP8/FP16路径逐位一致。
- 两方向实际PTX helper selp48→17：16条交换＋1条生成prmt selector，另加4prmt；shfl仍8条，不误称4-shfl或净少32条总指令。
- 完整向量化40/40模块、1918 entry编译/加载通过。单独向量化已让prefix **169→168regs、OccW8→9**，无需为该断崖加launch bounds。

### 再验证零重算Q与资源约束

- Q仍在第一个qt循环按原顺序计算/归一化/量化/预洗牌，只将part0写入四对显式寄存器，K/V放两平面共享内存；第二循环选择寄存器，不重读residual或重建feature。
- 裸Q虽然0bit-diff、8KB、无spill，实际峰值却178～216regs、OccW8；逻辑缓存16个u32不等于整个kernel峰值只增加16。清零与不清零均测，未把裸版本作为获益改动。
- 单独prefix `(32,9)` 可压至168regs/OccW11，但其余缓存核仍占用过高；进一步对非up核统一约束，**五个C32核167～168regs、SMem8192B、OccW11、LMem0**。up保留原Q/10KB/234regs/OccW8，不强压。
- 补齐10KB共享Q＋同约束控制，避免把约束与缓存收益混为一谈。最终50/80 GPU median：仅向量化900p/1080p **37.011/49.793ms**；同约束共享Q **37.105/49.867ms**；受约束寄存器Q **36.671/49.346ms**。选择最后组合，但注明该额外收益小、未锁频，不宣称严格等频约1%因果提升。
- 默认仅在已测 `c32-wave1-fast` 启用 `SM86_C32_REGISTER_Q_MASK63`、`SM86_C32_MINBLOCKS9`；normal/rtz/fast-norm900仍共享Q。mask bit6单列Up并关闭。CUDA后置pass实现，原HIP源共享Q路径保留。

### 最终成绩（50预热/80测量，Small31-block、Style1）

| 档位 | Phase4基线 GPU min / median ms | Phase5组合 GPU min / median ms | median速度比 | 对F32可见PSNR | maxabs |
|---|---:|---:|---:|---:|---:|
| 900p（处理1600×1024） | 38.604 / 39.105 | **36.095 / 36.671** | 1.0664× | 46.9753dB | 0.04004550 |
| 1080p（处理1920×1152） | 51.792 / 52.571 | **48.893 / 49.346** | 1.0654× | 46.1009dB | 0.04160273 |

两档对基线0bit-diff、首末帧逐位一致、invalid0、32/32实际CUDA LMem0。1080p仅向量化的min为48.513ms，虽低于组合min48.893，但组合median/mean/p90更好；按median选型，不拼接不同方案min/median。

最终默认源码重编C32 fast的整个cubin与获胜长测模块逐字节相同（SHA256 `92bc4bfa05cd3bd7c15d965428cc0f695d73340f6d14424702adfc0e21cc884f`），最终40模块集所有哈希也与长测集合相同。`selected-bench.log` 明确引用register-q-capped同一次长测，不当独立重复结果。

同一约140W上限、默认DVFS未锁频，显存7001MHz。四组SM时钟中位数1080p/900p：基线1710/1725，向量化1680/1665，同约束共享Q1657.5/1680，Q组合1680/1695MHz。主要向量化收益明确，Q的额外小收益与Boost差异同量级，完整遥测留档。

当前最优独立引擎基线为 `hip-port/phase5/artifacts/selected/modules/`；源码已保留选定改动。详见[Phase5说明](hip-port/phase5/README.md)、[32核分解表](hip-port/phase5/results.md)、分步日志、GPU验证、哈希和复测脚本。外部共享assets、游戏/Magpie运行时、v0.1.0正式包未覆盖。

## 2026-10-25 hip-port Phase 6：IR对齐升级，900p进入20～30ms

### 实现与编译

- `build_sm86_modules.py` 新增 `upgrade_ir_alignments`，在SSA抵消结束和第二次O3结束、llc之前均调用。共享global至少align16且保留更强对齐；i32/float至少4，8B传输至少8，16B传输至少16。可配置模块cap8，最终没有采用fallback。
- LLVM verifier/对齐规则测试通过；完整 **40/40模块、1918 entry CUDA编译/加载通过**。默认16B两档无misaligned-address错误，与Phase5输出0bit-diff。

### 指令与资源数据

- C64/C128 bi_bo_w16热核：global load/store u8和shared load/store u8原288/16/168/160条全部降0，替换为native word v2/v4；PTX约14213→12870行，使用当前Phase5分母，不沿用更早未滚动qt时的21576行。C256主用W16核也清除四类u8。
- 原始16B全40模块静态LD global u8 **141625→9669**、LD shared u8 **86848→37640**。模块含未执行入口和真实byte/gather，不能把所有剩余u8当成本帧未修复的memcpy，也不能将静态数当动态事务数。
- ViT contract/project **148/150→106/101regs**、OccW12→16；split FFN164→106regs、OccW12→16；C512 QKV207→203regs。wave2仍242～250regs/OccW8，没有达到显著下降的前提，未再强压wave2 launch bounds。
- 原始16B使受约束prefix新增32B LMem。C32 cap8、放松约束、half自然2B控制均保持数值，但没有两档明确速度优势，未默认采用。
- 最后只关闭prefix寄存器Q：fast家族Q mask63→31，prefix改回共享Q，**152regs/10KB/OccW9，消除32B LMem**。其余四个非up核仍167～168regs/8KB/OccW11，up234regs/10KB/OccW8，恢复32/32零LMem。与原始16B相比额外0.093/0.019ms（1080p/900p），差异很小，默认选无spill方案，保留原始方案供比较。

### 最终推荐成绩（50预热/80测量，Small31-block、Style1）

| 档位 | Phase5基线 GPU min / median ms | Phase6默认 GPU min / median ms | median速度比 | 默认Wall median | 对F32可见PSNR | maxabs |
|---|---:|---:|---:|---:|---:|---:|
| 900p（处理1600×1024） | 36.016 / 36.671 | **27.315 / 27.685** | 1.3246× | 27.781ms | 46.9753dB | 0.04004550 |
| 1080p（处理1920×1152） | 49.145 / 49.394 | **36.538 / 36.891** | 1.3389× | 36.982ms | 46.1009dB | 0.04160273 |

两档对Phase5基线0bit-diff、首末帧逐位一致、invalid0、32/32实际CUDA LMem0。FNV仍900p `b949727e624db210`、1080p `a8365381a41f7f83`。插桩核累计900p36.103168→26.121184ms，1080p48.503808→34.360320ms。原始带32B local方案另为900p27.336/27.666ms、1080p36.292/36.798ms，不能把它的min拼到推荐median。

**900p达成20～30ms目标；1080p仍约37ms，未进入30ms。** C32六核占原始16B插桩累计900p49.2%、1080p50.8%，成为更明确的剩余瓶颈；不是单靠继续清模块中的未使用u8即可推导出新加速。

默认DVFS、约140W上限，未锁频，显存7001MHz。遥测覆盖基线与原始16B，SM中位数基线1080p/900p1665/1687.5MHz、16B均1620MHz；最后prefix共享Q长测未另采分段遥测，不宣称严格等频倍数。

最终默认源码重编C32 fast与推荐长测模块整个cubin相同，40模块集哈希相同；`selected-bench.log` 明确引用prefix-shared-q同次长测，不伪装独立重复。产物在 `hip-port/phase6/artifacts/selected/modules/`，默认源码已采用对齐升级和prefix共享Q回退。

详见[Phase6说明](hip-port/phase6/README.md)、[32核表](hip-port/phase6/results.md)、[40模块指令统计](hip-port/phase6/ptx-counts.md)、全部对照/IR诊断/哈希/复测脚本。外部共享assets、游戏/Magpie和v0.1.0正式包未覆盖。

## 2026-10-25：Phase 7 无分支FP8与常量裁剪；跨h2预解包无收益

保留compat头的无分支FP32→E4M3、8处3指令解包位处理、常量fmed3二指令裁剪。GPU原语4262720测试值（随机float位模式、全部half模式与量化边界邻近值）对旧实现0bit-diff。LUT0xEA输入排列错误由小测试抓获，修正后最终40/40模块、1918entry真实CUDA加载通过。独立FP8转换核0bra、常量裁剪核1max+1min。

50warmup/80iter，第一轮：900p同轮Phase6 min27.421/median27.908ms → **27.344/27.636ms**；1080p36.467/36.946 → **36.371/36.722ms**。核累计26.256384→25.724960ms、34.411520→33.817600ms。反向顺序复测1+2为900p27.113/27.564、1080p35.816/36.599；随后基线27.757/28.173、36.655/37.330。重复结果分列，不混拼最小值，默认DVFS不宣称严格等频速度比。

两档全部对本轮/归档Phase6输出0bit-diff、首末帧逐位一致、invalid0、32/32活跃核CUDA LMem0。PSNR900p46.9753、1080p46.1009dB不变。prefix静态PTX bra617→10、min/max528/530→288/290、MMA84不变；C64/C128 bi_bo_w16 bra540→19、min/max128/130→64/66、MMA100不变。静态PTX削减没有变成同量级帧耗时改善，不能等同动态SASS分支数。

资源有得有失：C512QKV203→151regs/OccW8→12，C32up234→210；wave2主核仍OccW8。splitFFN106→186regs/OccW16→8，ViTproject101→138/OccW16→12，ViTattention78→119，完整核表保留回退而不只报好处。

第3项仅C32 W16 expansion外提input[0/1]解包，数值0bit、LMem0、寄存器基本不变，但两档median27.788/36.904ms均慢于1+2，prefix/mapped/up各增640B机器码；因此不进入默认，保留独立实验。默认源码保留1+2，`phase7/artifacts/selected/modules/`40模块哈希等于step12；selected日志明确为第一轮step12别名，不算独立复测。

[Phase7说明](hip-port/phase7/README.md)、[32核表](hip-port/phase7/results.md)、[主用核PTX](hip-port/phase7/ptx-counts.md)、[40模块PTX](hip-port/phase7/ptx-module-counts.md)、原语验证/重复长测/遥测/哈希均已落盘。外部运行时、游戏/Magpie、共享assets及正式包未替换。

## 2026-10-25：Phase 8，2-shfl D→AB直通；bounds配合低寄存器FP8恢复零spill

加入 `sm86_d_bytes_to_ab`，GPU验证256/256个位置标签精确一致，4194304个随机half值经FP8打包后0bit-diff。独立bridge PTX确为2shfl+4selp+4prmt（另有lane地址计算ALU）。C32的expand/AV与wave2的expand/contract/result/AV通过CUDA源码后处理接入；Q/K归一化、位置偏置和残差通道寻址不改。SSA测试确认D→C映射成对删除，LLVM verifier通过。

原始完整40/40模块、1918entry编译加载通过。先测C32-only、C32+wave2，再加请求的bounds；全部两档0bit-diff。但mapped新增8B local，splitFFN在bounds下出现56/64B local，ViTproject16B local。不能只凭OccW提高认定修复。

最终两处局部处理：`vit-stream-fast`、`c512-m32-deep`恢复逐位等价的FP8 C++转换表达式，保留Phase7常量裁剪/LOP3和Phase8 bounds，splitFFN恢复**106regs/OccW16/LMem0**，ViTproject恢复**101regs/OccW16/LMem0**；C32fast Qmask31→29，仅mapped改共享Q，直通仍保留，mapped **146regs/10KB/OccW9/LMem0**。另外三个主用寄存器Q核仍8KB/OccW11。C32/wave2继续使用Phase7无分支FP8 asm。

最终默认源码重编3个修正模块，37个复用完整构建；以最终40模块目录重新跑独立50warmup/80iter。**900p min26.486 / median26.837ms，1080p min35.237 / median35.790ms**；最后配对Phase7基线26.979/27.382、35.741/36.354ms，median速度比1.0203×/1.0158×。候选核累计**25.025536 /33.181696ms**（独立单帧）；最终900p基线插桩有抖动，不能把其27.055104ms当稳定均值。所有控制原始日志保留。

两档对本轮Phase7与归档Phase6输出0bit-diff、首末帧逐位一致、invalid0、32/32活跃核CUDA LMem0；可见PSNR46.9753/46.1009dB、maxabs0.04004550/0.04160273不变。默认DVFS未锁频，最后基线/候选高利用率窗口SM中位1620/1605MHz，功耗约139W。

主用prefix静态shfl269→229，mapped240→200，C64/C128/C256 bi_bo_w16为324→204，MMA不变。只消除了目标布局往返，不能说整个核的所有shuffle少83%，也不能按静态PTX数量推算动态SASS收益。带mapped8B local的控制更快（26.658/35.362med），最终选择零spill，不能把它的min拼到默认median。

[Phase8说明](hip-port/phase8/README.md)、[32核分解与资源表](hip-port/phase8/results.md)、[PTX表](hip-port/phase8/ptx-counts.md)。默认产物 `hip-port/phase8/artifacts/selected/modules/`；源/模块哈希、原语、3个新布局/SSA测试及既有IR/对齐测试、遥测与复测脚本均保留，diff-check通过。外部运行时、共享assets、游戏/Magpie和正式包未覆盖。

## 2026-10-25：Phase 9，Graph真实重放、V直通、五个C32非Up全部8KB零LMem

Graph门控已解锁：Small、wave-owned、compact W16、final direct、900p选择路径的7处旧限制移除，PreflightPdl的Graph return保留。benchmark用DLSS5_BENCH_GRAPH控制，真实每档build1/replay130，Small/wave-owned/direct均1。改变整张输入后Graph与Raw逐位一致，恢复输入也一致；first/last0bit-diff。但多轮Graph未带来预估1.5～2.3ms收益，默认仍由opt.graph显式选择，没有强制开启。

V（part2）已纳入2-shfl直通：C32及wave2融合/非融合QKV路径转换，Q/K归一化保持。相对Phase8，主用prefix静态shfl229→209、mapped200→180、wave2主核204→184，MMA不变，V-only两档0bit-diff、零LMem。

第三拳关键是逐核编码选择：全模块低寄存器版令mapped零spill但prefix仍16B local；先消费qt3仍16B且更慢；全模块无分支版令prefix零spill但mapped8B。最终只让CW pack的 `!Up && cw_kind==1` 使用低寄存器FP8表达式，其余C32保持无分支；Qmask恢复63、minblocks9不变。**五个非Up C32全部8KB/OccW11/LMem0**，Up保持10KB/217regs/Occ8；整网32/32活跃核零LMem。mapped静态bra442恢复，prefix18，不隐瞒编码器局部回退。

最终默认源码C32重编后50warmup/80iter，同轮Phase8 GPU median900p26.641、1080p35.486ms；候选无Graph为**900p min26.265/median26.612ms，1080p min34.924/median35.318ms**，Wall median26.722/35.407ms，独立插桩核累计**24.837120/32.576256ms**。Graph候选GPU min/median26.254/26.614、35.058/35.420ms，Wall median26.727/35.555ms。**未进入24/32ms，没有正面反超原版PTX的实测结论。** GPU median减去另一个插桩帧的累计不能全部当作可消除launch气泡。

全部成功控制及最终两档对Phase8输出0bit-diff、invalid0、首末帧一致；F32 PSNR46.9753/46.1009dB、maxabs0.04004550/0.04160273不变。83次kernel调用已核实。默认DVFS未锁频，最后基线/候选/Graph窗口SM中位1620/1605/1590MHz，约139W；实际处理1600×1024/1920×1152。

完整V构建最初因过窄源码断言拦下三个非register-Q变体，修正后补编，**40/40模块、1918entry**加载验证通过；原失败日志保留。最终默认C32另编一次，其余39个复用完整V集，两档无Graph/Graph均验证。产物 `hip-port/phase9/artifacts/selected/modules/`，源/模块哈希、动态输入Graph检查、全部控制、10个相关测试和diff-check落盘。[说明](hip-port/phase9/README.md)、[32核表](hip-port/phase9/results.md)、[PTX表](hip-port/phase9/ptx-counts.md)。外部运行时、共享assets、游戏/Magpie和发布包未更新。

## 2026-10-25：Phase 10，9核maxnreg＋内部FP8饱和，median首次低于24/32ms

先仅对Phase9相同PTX加精确入口maxnreg白名单，3个模块O4重编、9个活跃核资源全部复现：C64四核/C128三核168regs/LMem0/Occ12，C512 QKV128/0/16，C32 Up168/0/9（10KB）。五个非Up继续8KB/Occ11/LMem0。caps单独50/80 median26.279/34.895ms（首轮基线26.242/34.964），资源提升没有直接变成同幅度帧提速。

第二锤CUDA后处理将FP8绝对值先用min.f32饱和到448，再做原RNE/subnormal，删除p_sat/p_nan与FP8前端冗余clamp，浮点残差夹断保留。注意当前cw_z保留-0，最终删clamp后返回x；原来x+0入口仍保留+0。4242851个有限值GPU原语（随机FP32、全部有限half、舍入边界/邻近ULP/正负零/极值）全部0bit-diff。NaN旧/新编码并不完全相同，单独诊断记录，不扩张有限域结论。

首个组合版median23.702/31.412ms但出现mapped8B、FFN56/64B、ViTproject16B local。随后只在三条低寄存器路径用受约束短分支隔离subnormal/normal计算，保持内部min与RNE，不恢复旧饱和谓词/外层clamp。三个模块另编后LMem全消失，splitFFN105regs/Occ16、project101/Occ16、mapped168/Occ11。

最终独立50warmup/80iter：**900p min23.461/median23.750ms，1080p min30.944/median31.631ms**；Wall median23.850/31.712ms，独立插桩核累计**21.753888/28.430336ms**。同轮Phase9 median26.361/35.028ms，时间减少9.90%/9.70%，速度比1.1099×/1.1074×。前一次修正组23.107/23.479与30.751/31.259单列，未混拼最小值。p90仍24.534/32.042，达标指median。

两档对Phase9逐位一致、invalid0、first/last0、32/32活跃核LMem0；F32 PSNR46.9753/46.1009dB和maxabs不变。Graph关闭、实际处理1600×1024/1920×1152，默认DVFS未锁频；没有同输入/同尺寸重跑原版DLL，不宣称正面对比超越它。最后基线/候选SM中位1612.5/1567.5MHz、约139W。

完整40/40模块、1918entry编译加载后，3个低寄存器模块局部修正重编，37个复用；默认PHASE10_CAPS/FP8均True，与构建脚本显式True配置一致，未声称第二次全部重编。最终集 `hip-port/phase10/artifacts/selected/modules/`，[说明](hip-port/phase10/README.md)、[32核表](hip-port/phase10/results.md)、[静态指令表](hip-port/phase10/ptx-counts.md)、原语/哈希/源快照/遥测/复测脚本均保留。外部共享assets、运行时、游戏/Magpie及正式包未替换。

## 2026-10-25：Phase 10 720p补测与三档PTX历史标尺

单位均为ms。CUDA均使用Phase10最终selected模块、0.5x Small31、Style1、Graph off、50 warmup/80 iter；720p本次补测，900p/1080p沿用上一轮最终独立复测，未混入其它控制轮次的min或核累计。PROFILE_TOTAL是单独插桩帧。PTX列为历史GPU median标尺，本轮未统一输入/处理尺寸重跑DLL，不计算严格同条件加速比。

| 档位（CUDA处理尺寸） | CUDA GPU min | CUDA GPU median | CUDA Wall median | CUDA PROFILE_TOTAL | invalid | PTX历史GPU median |
|---|---:|---:|---:|---:|---:|---:|
| 720p（1280×768） | 13.843 | **14.103** | 14.182 | 14.001120 | 0 | 15.83 |
| 900p（1600×1024） | 23.461 | **23.750** | 23.850 | 21.753888 | 0 | 24.47 |
| 1080p（1920×1152） | 30.944 | **31.631** | 31.712 | 28.430336 | 0 | 32.04 |

720p首次触发旧C256分散核的CUDA_ERROR_MISALIGNED_ADDRESS；逐核同步定位为mh_ffn_fused_c256_frag_project_g128_qkv_bytein_fb。仅扩展Host的1280×768门控以使用现有c256_wave2，selected的40个模块字节不变。采用Phase5无对齐升级模块、关闭新720 C256门控跑旧分散路径，完整输出与本次720p逐位一致（0 bit-diff）。新路径首末帧0bit-diff、invalid0、32/32活跃核LMem0。同步诊断仅由DLSS5_BENCH_SYNC_KERNELS显式启用，正式计时未启用。

复测脚本：`bash Development/hip-port/phase10/bench_720p.sh`；[三档记录](hip-port/phase10/three-tier-results.md)，原日志`hip-port/phase10/selected-720p-bench.log`、故障定位及Phase5参考日志均保留。900p/1080p门控不变。

## 2026-10-25：Phase 10 Windows Runtime部署《鬼武者：剑之道》

按Zero指示将C256整块融合放宽到所有TierGeometry/free_geometry，只有DLSS5_LAB_C256_SPLIT=1退回分散核。当前selected模块未改，Linux 3/5快验896×512与1280×768均invalid0、首末帧逐位一致、无对齐错误，median7.999/14.092ms（不是50/80正式性能表）。

build-runtime.sh交叉编译当前Host/packed_weights为LmxxfNrRuntime.dll（5,048,942B，SHA256 ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353）。补上RuntimeOptions对sm_86子目录的探测，flags loader允许CUDA架构/AMPERE/C256配置；否则架构目录仅sm_86时会错误关闭优化。

原OptiScaler.ini、nvngx.dll_dlssnr.dll、nvngx_dlssnr.dll已备份到C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0并核对哈希，两个旧NR DLL已从Content根移除。按指定0.44底包解出DLSS5-AMD、D3D12_Optiscaler、shaders，部署40个selected CUDA模块与AMPERE_WEIGHTS_V2到HIP/sm_86，删除gfx1200/gfx1201，更新SHA清单；93个Small权重和207个cso齐全。dxgi/dinput8不变。

INI切换lmxxf，Enabled/WhitePointSource/Preset/Style= true/1/2/1，DX12 upscaler=dlss。default-config选择0.5 Small、FAST_NUMERIC=1、AMPERE_WEIGHTS=1、CUDA_ARCH_NAME=sm_86、C256_SPLIT=0、Graph0。特别将NETWORK_FREE_RES=1：底包原0会把854×480升级到1344×768；Windows原生D3D12/CUDA探针重测确认实际854×480→896×512，modules_ok40/hip1，wave-owned/C512/ViT gates均开启，PrepareFrame与Cancel成功。尚未代替Zero启动游戏作画质验收。

[部署回执](hip-port/phase10/deploy-onimusha/README.md)及完整deployment.json、Windows探针/编译/两档快验日志已归档；备份目录含原文件SHA与新部署SHA。未改其它游戏与发布ZIP。

## 2026-10-25：鬼武者首次实机误跑PTX——AmdBridge厂商锁与_storage_残留双重排查

### 首次场景与结论修正

Zero第一次进入《鬼武者：剑之道》，2K高画质、超分“高性能”，实际为 **854×480 → 2560×1440**，反馈约31帧。该次实际运行的是此前的 **ptx-patcher v0.1.0**，不能记作hip-port Phase10独立CUDA引擎的游戏帧率，也不是4K输出测试。

上一轮部署已验证Runtime自身的Windows D3D12/CUDA API、模块和输入几何，但探针直接调用Runtime，绕过了OptiScaler宿主AmdBridge的入口。部署仅清理Content根目录，也遗漏了递归子目录里的NR副本。这两处属于上一轮验收覆盖不足，本次把“双位置宿主补丁＋整树递归残留＋真实游戏Backend/Enqueue证据”补进验收。

### 乌龙1：NrBackend=lmxxf仍被物理AMD厂商检查拦截

首次日志第515行由Zero提供：`DlssNr::AmdBridge::IsAmd AMD pre-SR physical adapter vendor: 10DE, AMD: false`。该次原始日志已被后续运行覆盖，本次没有把旧行号写成当前日志的独立复读证据；原始二进制反汇编和包内源码与这条诊断一致。

包内`AmdBridge.cpp`153～171行，`IsAmd`通过PhysicalAdapterScope绕过厂商伪装，按D3D12设备LUID取真实DXGI_ADAPTER_DESC1，再检查`desc.VendorId == 0x1002`。`Before`在选择lmxxf后仍调用此函数，`if(!amd) return false`发生在`new LmxxfBackend`之前，所以仅写INI `NrBackend=lmxxf`并不足以进入自编译Runtime。

按PE静态映像基址0x180000000反汇编（不是ASLR后的绝对运行地址）：

| 位置 | 文件偏移 | 原指令/字节 | 效果 |
|---|---|---|---|
| VA 0x18002c13f | 0x2b53f | `cmpl $0x1002,0x410(%rbp)` | 比较实际VendorId |
| VA 0x18002c149，RVA 0x2c149 | **0x2b549** | **`75 03`，jne** | NVIDIA跳过下面的置true |
| VA 0x18002c14b | 0x2b54b | `41 b4 01`，mov $1,%r12b | 设置入口允许标志 |

Zero已先备份原版dxgi.dll，再把Content/dxgi.dll及Content/_storage_/dxgi.dll的0x2b549处`75 03`改为 **`90 90`（nop;nop）**。本次逐字节核查：两份均26,213,888B，与原版相比**恰好只有0x2b549、0x2b54a两字节不同**。CMP及真实VendorId未改，后续日志“10DE, AMD:true”表示这一布尔入口已放行，不是RTX变成了AMD。

- 原始备份SHA256：`aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2`。
- 两份patched SHA256均为：`f3fe9bfbfd3b4add7460713521d4e16d6d95c6fa3bf90db27e7338b6d255f35d`。
- 原始备份：`C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0\dxgi.dll`；原始哈希也与0.44底包的dxgi.dll一致。
- 此文件偏移只对应上述精确原版哈希，核查脚本强制验证原版身份、原字节及完整两字节差异。

### 乌龙2：GDK镜像子目录把旧NGX路线重新带回来

AmdBridge返回false后，宿主回退NVIDIA NGX路径；`Util::FindFilePath`会递归找文件，不止Content根。Zero在XboxGames/GDK的`Content/_storage_/`镜像子目录发现仍有`nvngx.dll_dlssnr.dll`及`nvngx_dlssnr.dll`，报告其SHA与原PTX备份一致。原部署根目录虽已移除，这两个深层副本仍足以让旧路线加载。

备份的身份已在本次重新读取核对：

| PTX文件 | SHA256 |
|---|---|
| nvngx.dll_dlssnr.dll | `4f088f382171b3b3af4e2b34cb71b162788c947a55eeefc6e81e36206c59a0c9` |
| nvngx_dlssnr.dll | `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a` |

Zero已删除_storage_两副本；本次对Content整树复查，上述两个文件名的残留数均为0。被删文件的原字节现已无法重新读取，因此“删除前副本与备份同SHA”明确归于Zero提供的热修证据；“备份SHA”和“现已递归不存在”则是本次独立核查结果，没有混写。

### 其余AMD假设的快速审计

审计底包配套源码`AmdBridge.cpp`499行、`LmxxfBackend.cpp`716行及dlssnr目录相关VendorId/0x1002引用，并核对当前自编译Runtime/bridge源码：

1. AmdBridge这条主动调用路径中，唯一直接`VendorId==0x1002`检查位于IsAmd。其余门槛为文件存在、D3D12设备/队列、后端wired、输入子矩形原点、尺寸稳定/预热及资源状态，不是另一个AMD厂商锁。
2. `HasFiles`在lmxxf分支找LmxxfNrRuntime.dll；`LmxxfBackend::EnsureRuntime`显式LoadLibrary该DLL、GetApi、Create、PrepareSession，没有发现AMD VendorId判断。`RuntimeName`仍查AMD pass1的菜单元数据，`HipRuntimeLoad`仍含amdhip64加载路径，但它们属于原Daniel/AMD路线或名称显示，没有成为当前Lmxxf链路的附加准入锁。
3. 自编译Runtime经nvcuda.dll实现兼容API。桥接优先LUID匹配，名称回退已接受0x10DE/0x1002，架构白名单含sm_86。前次已修复sm_86模块目录枚举和配置加载，删除AMD目录后会选择HIP/sm_86。
4. `gfx1201_target`仍是ABI遗留字段名/值；已查宿主LmxxfBackend不使用它作厂商拒绝。SubmitPulse仍有AMD驱动指纹范围，它影响可选提交优化，NVIDIA退回普通提交；Small的pdl=1/0及swin_run=1/0不是再次拒绝整个CUDA网络。当前没有发现另一个阻断调用的AMD专属条件。

以上是针对本版本当前路径的快速静态审计加实际调用证据，不宣称全部可选功能、所有GPU/资源格式都已验收。

### 热修后的真实游戏调用证据（与首次场景分开）

本次读取的OptiScaler.log是 **15:17:21启动、15:19:58正常shutdown** 的后续运行，源日志SHA记录在hotfix-audit.json。该轮DLSSContext日志为 **1280×720 → 2560×1440**，不是最初854×480场景，不能混在同一FPS/分辨率结论里。

- 第512行及后续：physical adapter vendor **10DE, AMD:true**。
- 第513～526行：构造LmxxfBackend、assets/modules路径、Create成功并session ready。
- 第527行：PrepareFrame报告 **`modules_ok=40 hip=1`**，`wave_owned=1/1 c512_m32=1/1 vit_proj_n64=1/1 vit_stream=3/3 multi_pass=0.5`。
- 第529、531～534行：eval1～5，enqueueCalls0→4、betweenHits0→4、producerSubmitted/continuationSubmitted0→4，**lastEnqueueRc=0、submitFailures=0**。
- 15:19:58：LmxxfBackend正常shutdown。启动时单次“upscaler could not restore state this frame”之后已经进入正常Record/Enqueue，没有把这一条启动跳帧当作持续失败。

这证明后续实机确实走到了独立CUDA链路。日志没有给出新的、与首次同设置的FPS验收，因此本次不补造“修复后帧率”。`lmxxf diagnostic: mode=off`仅指诊断旁路关闭，不是神经网络关闭。`LMXXF_WEIGHTS_DIR unset`警告随后已有weights=1和PrepareFrame成功，也不是本轮权重加载失败。

根目录与_storage_的LmxxfNrRuntime.dll已分别核对，均为`ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353`。未修改Runtime或40个Phase10核。

### 清单与回滚记录

备份目录下`backup-manifest.json`新增原版dxgi条目、patched SHA/字节和两个部署位置；`phase10-deployment.json`及仓库deployment.json同步记录补丁、原版备份、_storage_清理、整树无残留与真实游戏证据。旧“dxgi未改”的字段已移除，dinput8仍保持原文件。

原版dxgi保留未改；回滚厂商补丁时应同时恢复两个位置，避免镜像副本继续加载另一版本。PTX三文件的原始备份仍完整。核查与记录脚本为`Development/hip-port/phase10/deploy-onimusha/audit_hotfix.py`，关键当前日志摘录为hotfix-live-evidence.txt；完整日志快照/反汇编/临时源码放在忽略的artifacts。本次没有修改其它游戏、发布ZIP，也没有将DLL或模型提交到Git。

## 2026-10-25：Phase 11，C32 FFN feature直接half2→FP8，小收益收敛

本轮以Phase10 selected为唯一基线，初始工作区干净，未找到适用AGENTS；没有动ptx-patcher、共享assets、Windows游戏/Magpie或v0.1.0 ZIP。Graph始终off，没有原样重试跨h2解包。冻结40模块SHA并在每个bench前验证。

先读C32源码、实际SSA/PTX和新发现的Triton cuobjdump/nvdisasm SASS。A尝试消除FFN已有half结果再走RTZ的往返，LLVM/原语有限域通过、prefix/post各少16条F2FP.RZ，但900p变慢，1080p反向32.024→32.032med无收益，放弃。原始负结果与首次汇总保留；初扫A1080日志误被反向复测覆盖，首扫JSON/MD仍在，之后脚本禁止覆盖旧运行名，此记录不作保留依据。

保留B仅限C32 fast的FFN feature Site2：原residual RTZ和存储保持，将RTZ half8直接成对量化为E4M3，省half扩FP32再通用量化。clamp448、half2加2.0生成相同2^-9子正规网格，normal3bit RNE及指数差用每16位槽+0xc0/取低8位；最坏低槽0xff7e不会跨槽进位，符号/负零保持。16252928有限half字节穷举逐位一致；模拟真实RTZ生产者后，全部half输入位模式也0bit。其它float激活、累加与布局不改。

默认源码全量重编并实际CUDA加载 **40/40模块、1918entry**；39模块机器码与Phase10逐字节相同，最终C32与候选57个代码节相同。prefix/post SASS静态槽分别12227→12117、10356→10252，HADD2.F32各少32条；mapped反增7372→7532且F2FP.RZ16→24，未据静态多少推算速度。finish Regs168→162但Occ仍11。

最终第一对50warmup/80iter（Small31/Style1/默认DVFS约140W、Graph0）：

| 档位（处理尺寸） | Phase10 GPU min /median ms | Phase11 GPU min /median ms | Phase11 Wall med ms | Phase11核累计ms |
|---|---:|---:|---:|---:|
| 720p（1280×768） | 13.949 /14.369 | 13.894 /14.406 | 14.490 | 13.586432 |
| 900p（1600×1024） | 23.110 /24.077 | 23.205 /24.019 | 24.126 | 22.693888 |
| 1080p（1920×1152） | 31.099 /32.161 | 31.549 /31.928 | 32.041 | 28.465152 |

反向确认Phase11 median14.580/24.170/32.011，配对Phase10为14.737/24.471/32.257；1080p两对分别快0.233/0.246ms（约0.72%/0.76%），900p微小正向，720p首对慢0.037、反向快0.157，不宣称稳定720收益。独立插桩帧有波动（720确认核累计15.984640高于median14.580），不将PROFILE_TOTAL与median差额当launch气泡，不拼不同轮次min/median，不作锁频因果结论。

最终及反向三档均相对Phase10 **0bit-diff、invalid0、首末帧一致、32/32活跃核LMem0**。900/1080可见F32 PSNR46.975322/46.100947dB不变，720比特相同保证任何共同固定参考下PSNR不降。尝试的旧Phase1 F32模块/当前Host/720组合未验收（观测11.6075dB/maxabs1），未当作可信绝对金标准；原诊断保留，本轮不修复旁支。

候选/对照均在phase11忽略artifacts，遥测和每次运行完整40模块哈希/时窗/参数保留。已删除约979MB冗余模块/临时IR/派生反汇编，逐字节验证后硬链接去重约551MB重复输出；最终40模块、改变的候选C32、原始日志和质量证据保留。最终默认 `hip-port/phase11/artifacts/selected/modules/`；[说明](hip-port/phase11/README.md)、[三档与核级表](hip-port/phase11/results.md)、[质量门](hip-port/phase11/quality.json)，复测 `bash Development/hip-port/phase11/run_benchmark.sh`。

建议Phase12先审计已有FP16的AV/V生产者量化，先证明舍入/NaN和布局，再逐站小步控制；不要将float激活或Q/K归约直接降精度。另补匹配当前Host/Small图的720p F32参考。只提交本轮，不push。

## Phase12：C32 AV half2→FP8；逐站验证与720 F32参考审计（2026-10-25，闇）

唯一基线Phase11 selected（起点1da7855，工作树干净）。分别实验C32 AV、C32 V、wave2 AV、wave2 V；默认只保留C32 AV。没有改float激活多项式、Q/K行归一化、RTZ residual，不重试Graph/跨h2；未动冻结PTX、共享assets、Windows部署或发布包，不push。

- 四站分别覆盖65536种half模式×256位置、256单点布局及实际MMA累加次数（4/2/4/4、8、16），包含NaN/Inf/±0，GPU字节比较均0；不沿用Site2有限域结论。C32用half2乘1保持-0并规范化NaN，wave2用half2加0复现原零语义；裸halfpack的NaN规范化差异已显式处理。完整验证D→RDNA4→pack→preshuffle与D→halfpack→2shfl的ABI。
- C32 AV独立反向/确认med33.884vs34.013、32.179vs32.664；C32 V补充只快0.038ms，wave2 AV近零/首轮负、wave2 V方向不稳定，后三站不入默认。保留全部负结果。
- 最终默认从源码全量重编40/40并独立CUDA加载1918entry，39模块SHA未变，唯一C32机器码与单站候选精确一致。16项Python/LLVM回归通过；完整SHA与复测入口见Phase12。

Small31 Style1、Graph off、默认DVFS约140W，每行独立50warmup/80iter，单位ms；不跨轮拼min，不把插桩累计与GPU median之差全当launch气泡：

| 档位 | 顺序 | Phase11 median | Phase12 min / median | Wall median | 独立核累计 |
|---|---|---:|---:|---:|---:|
| 720p 1280×768 | 正向 | 14.555 | 13.884 / 14.588 | 14.730 | 13.984768 |
| 720p 1280×768 | 反向 | 14.876 | 14.233 / 14.884 | 14.973 | 14.102528 |
| 900p 1600×1024 | 正向 | 24.159 | 23.244 / 24.236 | 24.339 | 22.022144 |
| 900p 1600×1024 | 反向 | 24.644 | 23.465 / 24.569 | 24.691 | 23.024640 |
| 1080p 1920×1152 | 正向 | 32.639 | 31.327 / 32.637 | 32.754 | 28.468224 |
| 1080p 1920×1152 | 反向 | 33.217 | 31.583 / 32.849 | 32.998 | 30.803968 |

1080正向0.002ms几乎持平，反向正向0.368ms；额外ABBA确认31.966→31.921、33.221→32.887ms，与此前独立站点配对同方向，但不宣称固定收益比例。720无收益结论，900方向相反、不宣称稳定收益。全部min/median/Wall、核累计、时钟/温度/功耗原始遥测按轮保留；首轮探索前四项未采到遥测，明确缺失，不补造。prefix/post静态SASS槽12117→12035/10252→10169，不能等同速度。

两轮三档0bit-diff、invalid0、首末帧一致、32/32活跃核LMem0；7201280×768仍走C256wave2、无对齐错误。可信900/1080 F32可见PSNR46.975322410562406/46.100947087035124dB与基线完全相同。

720 F32旁支：先用冻结Phase1 Host+F32模块重现900/1080gold0bit，再用当前Host+同F32模块、旧权重/compact/C256门控配对，两档再次0bit。但同链720仍产生与Phase11坏参考同SHA的输出，可见PSNR11.607545dB/maxabs1（坏参考诊断，不是精度成绩）。**可信720绝对F32参考仍未建立**；具体阻断为720几何/模块路径尚未逐层校准，精确根因不捏造。下阶段优先逐层定位首次偏离，再建当前图F32链，不让其阻断已通过严格0bit的主线。

[Phase12说明](hip-port/phase12/README.md)、[两轮完整成绩](hip-port/phase12/final-results.md)、[32核表与全部控制](hip-port/phase12/results.md)、[质量门](hip-port/phase12/quality.json)。默认产物hip-port/phase12/artifacts/selected/modules；复测bash Development/hip-port/phase12/run_benchmark.sh。已清理本轮重复大文件，最终40模块/哈希/原始日志保留，临时产物被Git忽略。Phase13性能侧先取prefix/post动态依赖证据，不继续无依据推广half站点。

### Phase13 阶段一：720p首个异常核已定位（2026-10-25，闇）

以Phase12 selected/41220e0为唯一基线，初始工作树干净。Stage只读tap不装observer、不改raw/inter-byte门控；三档两链trace输出均与各自原样0bit。C256 split/fused F32 720输出0bit相同，排除此门控。

首次异常放大在block31的vit_attention_fused_256_bytein_bout（n240）：head RMS约1.67正常，block31后约22；**Phase12和旧F32都受影响**，不是仅参考链错误。抓相同实际QKV，用CPU独立矩阵算法核验：F32 legacy256 AV对CPU RMSE33.331681/maxabs446.75，诊断改走400后245760个AV字节100%一致；Phase12相应RMSE33.287352→0.027869。均匀QK0/V1探针n16/240/256都通过，不能草率归因n%64尾块；具体索引/布局指令尚未证明。

只在诊断Host改400后，两条720链可见差异43.577948dB/maxabs0.0509355；这是修正图诊断，不是默认720绝对PSNR。同链900/1080既有F32gold再次0bit。当前默认仍按Phase12严格0bit保持，不混入会改变输出的正确性修复；720绝对参考继续未验收。约1.24GB层dump统计/哈希后清理，小样本与复测脚本保留。详见[参考链定位](hip-port/phase13/reference-audit.md)。Phase14优先以独立正确性阶段修256路径，再另立720新输出基线；无部署、不push。

### Phase13 阶段二收官：动态C32审计，默认保持Phase12（2026-10-25，闇）

软件clock64/warp边界采样先取得真实阶段证据；50次预热附近抓prefix540/post547个CTA，插桩仍168regs/8KB/LMem0、输出0bit。每qt FFN expand→float激活→contract中位10432/11122周期，AV仅1304/1322。含插桩扰动/并发等待，不当硬件stall计数、纯MMA延迟或帧耗时。真实SSA保持4个u4 PHI、无f8 PHI，C/D调用数不变；SASS生产消费寄存器上下文完整保留，不凭静态条数判断速度。

只试FFN即时contract：每个hp激活产生后更新两个独立ci，保持各链h2/hp累加序。4096warp×32lane、全部half模式原始u32差异0，结构2项及既有Python/LLVM16项通过。分别控制prefix/post，50/80：prefix正31.306→31.512、反候选32.017vs基线31.946，两对更慢；post正31.306→31.645、反31.816vs31.871，方向不稳。**两项均不保留，不组合、不追噪声重试。** 未重试Graph、跨h2、Phase12已拒V/AV站点。

最终默认从源码全量重编40/40，实际CUDA加载1918entry；**40个SHA全部与Phase12 selected相同**。三档两轮数据如下（Small31 Style1、Graph off、默认DVFS140W上限、50warmup/80iter；相同二进制轮间差异不宣称Phase13提速）：

| 档位/轮次 | GPU min / median | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|
| 720p正向 | 13.975 / 14.123 | 14.198 | 13.440000 |
| 720p反向 | 14.230 / 14.377 | 14.472 | 13.700096 |
| 900p正向 | 23.205 / 23.646 | 23.763 | 21.706752 |
| 900p反向 | 23.397 / 23.932 | 24.067 | 21.781504 |
| 1080p正向 | 31.264 / 31.835 | 31.934 | 28.743680 |
| 1080p反向 | 31.537 / 32.057 | 32.188 | 29.387775 |

两轮三档相对Phase12输出0bit、invalid0、首末帧一致、32/32 LOCAL0；7201280×768/C256wave2门控保留，无misaligned address。900/1080 F32可见PSNR46.975322410562406/46.100947087035124dB不变。每行min/median/Wall/独立PROFILE_TOTAL成组，实际遥测、温度/DVFS波动逐轮保留，不拼轮次、不把差额全算launch气泡。

720结论见阶段一独立提交6b61bd9：已确定Phase12和旧F32共同的256 attention问题，默认绝对PSNR仍不报；400修正图只作隔离诊断，没有混入严格0bit默认。Phase14建议优先允许新输出基线的独立正确性修复，单点QKV确定256的转置/分母/PV问题，再立720F32金标准；不要原样重试本轮无收益调度变体。

[Phase13报告](hip-port/phase13/README.md)、[两轮完整成绩/遥测](hip-port/phase13/final-results.md)、[32核表及负结果](hip-port/phase13/results.md)、[参考链定位](hip-port/phase13/reference-audit.md)。复测bash Development/hip-port/phase13/run_benchmark.sh（新名字）；完整模块哈希/实际加载记录/质量门保留。仅清理本轮重复模块、临时LLVM/预处理产物，证据及最终40模块在忽略artifacts，未改部署/ZIP/共享资产，不push。

### Phase14 阶段一：256 attention两处ABI错配修复与新720金标准（2026-10-25，闇）

以Phase12 selected为性能/旧输出基线，起点41042b6，工作树干净。定位到build_sm86_modules.py通用预洗牌插入也命中legacy attention，但两处Q/xb的A侧消费者仍走generic MMA，发生二次洗牌；400的B侧匹配已正确。新phase14_transform严格限定legacy函数，只改两处消费者为preshuffled_a，不改LDS/分母/精度/尾块。16token坐标256组已独立复现坏Q(score)与坏P(PV)，LDS转置、行和、PV原索引均正确；不能归因n%64。

172项两种累加/全部16种<=256合法token数/32head/非均匀/末token/subnormal/±0/有限边界/适用浮点NaNInf入口测试：修复256对规范原始布局参考及400均0字节差异。真实首块245760 AV字节F32对CPU0bit；八块CPU精确除法仅1字节边界差已定位rcp.approx：1.0625→1.062500119，从FP8 0x38到0x39。CPU仅匹配独立RCP原语后1966080 AV字节全部相同；无保留NaN字节。保留字节7f/ff的现有packed decoder有限域捷径未扩称IEEE NaN支持。

先重建未修复F32 control（目标SHA与归档精确相同），control与修复F32均复现900/1080 gold0bit，再生成新720 F32累加gold，SHA149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5。256/400正确整网0bit；新720对该独立gold PSNR43.57794791233917dB、maxabs0.05093550682067871、invalid0；相对Phase12旧720改变2947224个f32元素，为授权正确性变化。900/1080仍对Phase12 0bit、PSNR不变。非复用旧400诊断数字。

默认模块已全量重编/实际加载40/40、1918entry，7个含legacy导出的模块变化；三档selected快验相对修复原型0bit、首末帧同、32/32 LOCAL0。阶段一已清理不变F32模块副本，仅保留证据/新gold/变化模块；接下来用正式50/80配对比较正确256与400，再选默认并完成最终两轮。详见[正确性证据](hip-port/phase14/correctness.md)。不改共享assets/部署/发布，不push。

### Phase14 阶段二：采用等价400默认、原生Host最终验收（2026-10-25，闇）

正确性修复先独立提交830185d。正确256/400两组ABBA有近乎持平轮次，全部保留；后续双向配对与实际attention核累计支持400微小正向，因此选400为<=256token运行时默认。两处Host选桶（byte stream/普通）同时更新，无1280特判；correct256仅保留benchmark显式开关，运行时默认不读该开关。默认模块仍是阶段一完整重编的40模块，7变33不变、实际1918entry加载；最终正式Host重新编译并不强制选桶。

最终720correct256对照median14.182/14.424，default400为14.147/14.381，只快0.035/0.043ms，不夸大收益。先前近乎零/负向与ABBA完整保留；8次attention插桩核累计约0.301～0.317→0.260～0.270ms，不当作整帧收益或寄存器推算速度。Graph off、Small31/Style1、默认DVFS140W上限、50warmup/80iter，逐轮遥测齐全：

| 档位/轮次 | GPU min / median | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|
| 720p正向 | 14.076 / 14.147 | 14.245 | 13.498368 |
| 720p反向 | 14.204 / 14.381 | 14.468 | 13.714240 |
| 900p正向 | 23.375 / 23.722 | 23.882 | 22.387712 |
| 900p反向 | 23.586 / 23.885 | 23.996 | 21.772288 |
| 1080p正向 | 31.347 / 31.826 | 31.926 | 28.646400 |
| 1080p反向 | 31.250 / 32.111 | 32.206 | 28.637216 |

900p Phase12对照median23.640/23.998，1080p31.681/32.100；本轮900方向不同、1080慢0.145/0.011ms，如实保留，不宣称提速或锁频因果。PROFILE_TOTAL是独立插桩帧，不将与median之差全部当launch气泡。

两轮三档invalid0、首末帧0bit、32/32 LOCAL0；720相对新正确基线0bit，对旧Phase12改变2947224个f32元素；900/1080仍对Phase12 0bit、F32 PSNR46.975322410562406/46.100947087035124dB不变。新720可信F32 PSNR43.57794791233917dB/maxabs0.05093550682067871，最终原生Host无强制选桶重新生成三档F32 gold均0bit。另整网512×512/896×512/1024×768（64/128/192token）correct256/4000bit、invalid0、首末帧同、32 LOCAL0，无对齐错误；不是只验证720。

[Phase14报告](hip-port/phase14/README.md)、[最终两轮与遥测](hip-port/phase14/final-results.md)、[全部控制/32核表](hip-port/phase14/results.md)、[根因/CPU/舍入证明](hip-port/phase14/correctness.md)。新gold SHA149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5，八块CPU仅匹配独立rcp.approx原语后1966080 AV字节全同；不再使用旧错误720比较。18项Python/LLVM回归、172原语项、256坐标证明与40/1918加载全部通过。复测python3 Development/hip-port/phase14/run_benchmark.py（自动新名字）；保留原语/新gold/模块SHA/CPU小样本，清理仅本轮大副本与LLVM，未碰共享assets/游戏/Magpie/发布ZIP，不push。

Phase15先把新720gold固化回归，再补真实帧/动态输入/Style1 HDR和free-geometry覆盖；性能只在正确新基线上继续C32动态证据，不重试即时contract/跨h2/Graph。bridge或游戏部署另阶段验证，本轮没有部署。

### Phase15 阶段一：输入审计，暂停新C32性能实验（2026-10-25，闇）

以Phase14 selected/新720 F32 gold为唯一基线，起点9c27a1c，工作树干净。找到一张有GameDVR/sRGB元数据并目视核实的《明末》1920×1080武器菜单截图（SHA a055f4e3e43ee2094ca76433b8c57587e35eb5a73a6013622f540a5d52d1d29a），只有单张SDR菜单，非真实线性HDR/非动态场景序列。旧D:\DLSSNR-Lab\hip-backend\live-menu-before.f16在本机缺失；当前Temp input.f16全零，Magpie smoke input为人工渐变，均不能冒充实拍。完整搜索范围/原始来源SHA/统计见[Phase15输入审计](hip-port/phase15/input-audit.md)。

按本轮用户“真实输入不足则暂停性能侧”要求，暂停新的C32性能实验；继续长期回归与动态/geometry/HDR模拟配对验证。由SDR线性化×512的配对将明确标为衍生/合成，不称真实HDR捕获或实机画质验收。43.577948dB低于旧45dB门槛，不改写门槛。无游戏/共享assets/发布包写入，无push/部署，不要求Zero重进游戏。

### Phase15 阶段二：长期回归闭环，画质限制与性能暂停（2026-10-26，闇）

以Phase14 selected/新720 gold为唯一基线，没有生产源码或算法变更。建立并实际完整重放run_all入口：40/40源码重编、1918entry真实CUDA加载，40个SHA全部与Phase14相同；256坐标、172项16..256合法token/实际执行QKV、CPU匹配rcp.approx后1966080 AV字节0bit，18项既有Python/LLVM通过。旧QKV来自合成benchmark实际执行，不冒充游戏帧。

真实来源仅一张已目视核实GameDVR《明末》SDR武器菜单，原始SHA a055f4e3e43ee2094ca76433b8c57587e35eb5a73a6013622f540a5d52d1d29a；没有真实场景线性HDR/多帧游戏序列。保留源副本/元数据/SHA。以该SDR及明确标记的全幅动态衍生图、既有codec half-bit RGB规则与smoke渐变构成56输入配置、7几何：512²、854×480→896×512、1024×768、640²、1152×640、1280×768可见720、1024²。1/512手动白点模拟HDR原始范围0..512，21配对编码/三模式输出0bit；这是CPU fixture预处理+独立CUDA网络回归，不是D3D12/HDR实机验收。

复用同一CUDA输入/输出地址，每帧整幅上传，输出NaN哨兵防漏写；每几何A/B等8配置两遍再恢复A，改变像素约99.998%。两轮各375帧调用加27资源重放（共750+54），全部repeat/first-last0bit、invalid0；56项correct256/4000bit，Native32种活跃核LOCAL0，无对齐错误；两轮输入/输出SHA全相同并冻结为pinned-image-outputs.json。

精度均为可见编码工作RGB，固定peak1，不用逐图最大值，也不将其当原始线性HDR peak512。真实SDR菜单1280×720对F32为60.247254dB/maxabs0.043955266，但它是单张UI输入且只是相对F32精度，不能概括全部画质。新增未达旧门槛压力项：1024² codec-ramp white1/512同一编码图为43.436806dB/maxabs0.054382861，256/400及两轮均一致；具体层级来源未归因，保留证据。43.577948与43.436806都没有达到45dB，全局45门槛明确False。

规范三档：720对Phase14新正确输出0bit，可信F32 PSNR43.57794791233917/maxabs0.05093550682067871；900/1080对Phase12及Phase14均0bit，F32 PSNR46.975322410562406/46.100947087035124不降，maxabs0.04004549980163574/0.0416027307510376。三档invalid0、first-last0bit、Native32 LOCAL0，金标准SHA及参考链不变。

按用户真实输入不足则暂停性能侧的条件，并保留新增质量门槛缺口，本轮无新C32性能实验或性能计时，不用正确性快验时长充50/80成绩。保留Phase14实现，既无新性能保留项也无性能负收益判断；下一步先恢复既有HDR/多帧档案、逐层定位43.436806压力项，不强行开Phase16、不要求Zero重进游戏。无共享assets/游戏/Magpie/发布包写入，无push/部署。

[Phase15报告/一键入口](hip-port/phase15/README.md)、[56项逐输入精度](hip-port/phase15/image-results.md)、[质量门](hip-port/phase15/validation.json)、[真实性缺口](hip-port/phase15/input-audit.md)。所有原始来源SHA、参考模块与Native模块SHA、全幅动态日志、原语/CPU证据保留；只清理本轮重复大二进制与可再生编码输入，旧档案只读。

### Phase15B：1024² codec-ramp 与 720p 质量差异根因闭环（2026-10-26，闇）

- 针对 `1024² codec-ramp` (`43.44 dB`) 与 `720p` (`43.58 dB`) 略低于早期经验值 `45 dB` 的问题，完成全网逐阶段特征 NRMSE 追踪、F32 post 独立反事实重放、首个 ViT expand 65,536 个预激活值 CPU K8-FP16-RNE 逐位核验、8,126,464 个 ViT attention AV 字节 CPU 逐位核验及输出头逐位复算（详见 [`hip-port/phase15/DIAGNOSTIC15B.md`](hip-port/phase15/DIAGNOSTIC15B.md)）。
- **核心结论**：**确认不存在算子索引、布局或预洗牌 Bug**。`43.44 ~ 43.58 dB` 纯粹源于 `.f16.f16.f16.f16` 硬件指令每 K8 步的 FP16 RNE 舍入与 FP8 量化边界在 31 层深网上的正常累积传播（且原版 NVIDIA PTX 本身即为 FP16 累加，真实《明末》截图在全部 7 种几何下 PSNR 高达 `57.0 ~ 60.9 dB`）。同时修正了旧诊断 tap 在 `PrepareForExternalInput()` 前提前触发截获全零预热帧的时序问题。
- **主脑裁决（2026-10-26，朱雀）**：Phase 15 质量审计正式结案，**`Phase 14 selected` 确立为 100% 正确的黄金数值与性能基线**，解除“45 dB 暂停令”，全面重启 `hip-port` 性能优化主线（Phase 16+）。


## 2026-10-26：Phase16，ViT四核16B尾写全覆盖（闇）

按815d096新裁决，以Phase14 selected三档输出作严格0bit基线，恢复性能线。三个CUDA模块开启EXPAND/QKV/CONTRACT/PROJECT TAIL_VEC；expand沿用1KB转置，contract复用4096B occ_pad，project新增1KB，QKV复用dead raw norm tile。实际compactw_w16入口PTX单字节global写32/32/32/16→0/0/0/0，v4.u32与SASS STG.128均为2/2/2/1；Regs分别80→85、106→102、101→103、119不变，OccW16/16/16/15不变。未做可选FP8 LDS子实验。

仅3模块重编、37按SHA复用，40/40实际CUDA加载1918entry；最终源码重编SHA与实测集合全部相同。三档各两组ABBA、50warmup/80iter，共24次正式运行均相对Phase14完整输出0bit、invalid0、first-last0、32/32 LMem0。18项既有Python/LLVM及1项尾部还原顺序回归通过。首版contract被旧Phase2 pass把packed_total还原放到标量fallback，快验拦截，修复后再进入正式计时；失败日志保留。

GPU median按A1/B1/B2/A2，单位ms：首组720为14.102/14.087/14.083/14.146，900为23.628/24.193/23.712/24.309，1080为32.091/31.915/32.402/32.326；确认组720为14.173/14.444/14.432/14.899，900为25.241/24.444/24.437/24.518，1080为32.538/32.606/32.463/32.592。两次median均值比较小幅正向，但默认DVFS/基线抖动与收益同量级，不宣称稳定百分比；第二组900不拿0.439ms作因果收益。四核独立插桩数据与整帧min/median/Wall/PROFILE_TOTAL逐轮完整保留，不能按静态写指令削减推算加速。

按任务要求保留四处默认开启，数值/资源/向量化目标达成，整帧收益很小。详见[Phase16报告](hip-port/phase16/README.md)、[两组ABBA与四核](hip-port/phase16/summary.md)、[32核完整表](hip-port/phase16/results.md)、[验收](hip-port/phase16/validation.json)。最终40模块在phase16/artifacts/tail/modules；临时LLVM/失败输出已清理，正确输出按SHA去重，保留日志/遥测/SHA/生成源。未改共享assets、游戏/Magpie、PTX或发布ZIP，不push；本阶段独立commit，下一阶段Phase17未启动。


## 2026-10-26：路线 B ptx-patcher V2 偶奇K16零洗牌（闇）

以c77a689派单执行。fast_render_fp8_mma_run默认同lane偶/奇字节解包，mapped用5410/7632 PRMT，保留multidef_nq、不加量化；旧拆解仅--mma-layout legacy诊断。GPU每奇偶位置65536字节对（64516有限对）0bit，65536组mapped half位标签0bit，768个A/B槽独立坐标证明、64组实际MMA对CPU整数矩阵积8192输出全同；8项mapped及1项代码生成回归通过。精确实数内积相同不保证FP16旧累加顺序逐位相同，实际PSNR单独保留。

新DLL `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v2.dll` 为266414592B、15/15 O4、全部原槽位、无新增节；SHA737af93c2843fe18462c39da36a0a482e4d410493bed0e178fecabf526880f74。原DLL/旧fast哈希确认未改。

bench_sky同轮50warmup/80iter、每档正old/new/V7再反V7/new/old：720天空旧median15.877/15.956，新10.187/10.249，V7 6.417/6.477ms；900旧24.514/24.527，新15.266/15.280，V7 9.328/9.319；1080旧31.959/32.005，新20.359/20.333，V7 12.311/12.305。新对旧约1.56～1.61×，V7仍快约1.58～1.66×；默认DVFS无锁频，不作等频因果。完整min/median/Wall和遥测逐轮归档；三DLL正反输出各自全幅0bit、18次全finite。天空变号均0，新HF RMS0.000101989（旧0.000103482，V7 0.000093139）。新旧PSNR62.544361/61.663517/58.495481dB；新对V7为47.913975/39.253644/38.541064dB。相互PSNR不是原生新卡绝对画质gold。

FB00～06全导出静态SHFL总计26300/16627/14195/12371/6563/4963/834→1274/706/706/706/610/258/257；只消除MMA搬运新增SHFL，原归约保留。max STACK分别264/80/8/232/1152/608/456→240/120/0/200/1032/480/168B；仍有spill，且部分变体回退，不能宣称全DLL零STACK。例FB00 upsample200→48B但outview152→200B；FB05 projection264→0B。

V7二进制分析：22Fatbin，新15～21为75/86/120网络，原00～06保留sm120；Small资源113893343→226693087B、HT147695410→291526450B。Small四个纯矩阵共2097152值，原FP8解码与V7 FP16位值多重集合全同但顺序不同，证实离线FP16预展开/重排；混合scale/metadata没有简单翻倍。FB18-sm86另有1040条IMMA.16832.S8.S8，位于五个C256非_fp8变体；未用运行时核追踪证明本次Small实际执行，不能把剩余1.6×全归INT8，也没有单因素消融分配预解码收益。

[完整回执](ptx-patcher/v2/README.md)、[实测/PSNR](ptx-patcher/v2/bench-results.md)、[资源/栈表](ptx-patcher/v2/sass-summary.md)。临时PTX/cubin/SASS、全部本轮RGB和discord_v7旧RGB记录SHA后清理；保留新DLL、源码/原始日志/遥测/资源表/哈希/IMMA摘录。未改发布ZIP、游戏/Magpie，不push，阶段独立commit。V7权重ABI与进一步优化尚未移植。


## 2026-10-26：路线 B V2.1，放宽maxnreg控制胜出（闇）

以066aed5/V2为唯一基线，只改已有PTX maxnreg数字；8个编译控制规范化文本/SHA与V2完全一致，不改FP8图、权重、K分组或Host。先测C256128→168/255及各FB255，再比较fb45/hot255/all255。1080扫描C256单点20.315/20.386ms对穿插V2约20.14～20.38无可靠净收益；仅FB04为17.665、仅FB05为15.361，hot255组合12.761ms。

最终推荐FB00/03/04/05/06→255，FB01/02保留。三档同轮正/反50warmup/80iter：V2 median720为10.227/10.209→V2.1 **6.662/6.668ms**；900为15.221/15.302→**9.697/9.761**；1080为20.378/20.418→**12.784/12.776**。同方向速度比约1.53/1.57/1.60×；完整min/median/Wall及默认DVFS遥测逐轮保留，不冒充锁频。全部13扫描+24正式对比共37次输出相对同档V2全幅0bit、invalid0，天空变号0/HF RMS0.000101989不变。

hot255略优fb45且额外清FB00/03/06 spill，保留；不把约0～0.1ms小差异作固定独立贡献。all255额外改FB01/02反而慢（900p 9.897/9.910、1080p 13.074/13.054），未选。全导出静态max STACK：FB00 240→0、FB03 200→0、FB04 1032→80、FB05 480→8、FB06 168→0 B；对应LDL/STL为709/702→0/0、629/706→0/0、2169/2201→40/78、1027/1017→7/5、117/110→0/0。推荐仍有FB01原120B以及FB04/05少量栈，不能宣称全网零STACK；全导出计数不冒充动态实际访问。

新推荐`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v21.dll`，266414592B，**15/15 O4、全部原槽位，无扩节**，SHA **c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed**。最终原源全量15重编/实际CUDA加载，SHA与获胜控制相同；V2原SHA保留。专用复测构建`python3 Development/ptx-patcher/v21/build_recommended.py`；通用构建器新增--maxnreg FB:LIMIT，无参数仍为V2。

[回执](ptx-patcher/v21/README.md)、[正式两轮](ptx-patcher/v21/final-results.md)、[全控制](ptx-patcher/v21/results.md)、[资源/溢出](ptx-patcher/v21/resources.md)、[验收](ptx-patcher/v21/validation.json)。8项mapped、1项MMA生成、1项cap回归通过。候选DLL/RGB/临时PTX/cubin记录SHA后清理，保留推荐DLL、日志/遥测/资源/清单；不改发布ZIP或游戏/Magpie，不push，立即独立commit。本轮未改FP16图/离线权重/IMMA，不将这些机制混入收益。


## 2026-10-26：v0.2.0正式三包与本机PTX V2.1部署（闇）

按9980783计划完成1～4步。主fast.dll已更新为V2.1（SHA c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed），v21/v2副本保留。鬼武者根及_storage_恢复原dxgi aa3761f2…、原PTX INI（nvidia/WhitePointSource1/Preset2/Style1），补齐配套库并移除活动HIP运行时/资产/add-on/shader至备份；两处转发桥与NR哈希已核。剑星NR更新，默认TransferStrength/ColourStrength=1.0/1.0，增强风格INI=1.5/1.1；Magpie目录升级0.2.0并保留Preset2补丁/config。旧现场在C:\DLSS5-5090-dll\backups\20261026-v020，剑星恢复清单及Live SHA同步，旧日志已归档。

三个ZIP位于C:\DLSS5-5090-dll\发布打包；CRC、逐文件SHA、核心DLL、原宿主和INI默认/增强配置全部核验。旧0.1.0 ZIP与SHA归档archive/v0.1.0；总SHA256SUMS仅列新三包：
- `OptiScaler-REFramework-DLSS5-RTX30-0.2.0.zip`，375533391B，SHA256 `531179b60d55e7147262e488afa760f8fc6422b353882ee5b223c47db3022d94`。
- `OptiScaler-DLSS5-RTX30-0.2.0.zip`，318461731B，SHA256 `ce7c18e05e286f17b93ee841d2ea9ae829f62cb0a5b3018b93500d3eb902509f`。
- `Magpie-DLSS5-RTX30-0.2.0.zip`，323386599B，SHA256 `e88a6c86ee6803de64cf6cabb1d3d2af3ef37565c91822a77a5dd8a6ef347739`。

Windows：三包Feature18 create/evaluate成功、全部finite；两个OptiScaler完整FFX→NGX→NR smoke成功，composition detail1/colour1。Windows Get-FileHash匹配全部最终部署NR；驱动NGX核心数字签名Valid，修补NR为预期NotSigned。随后 Zero 进游戏完成实机验收：《鬼武者：剑之道》2K 性能档从 `v0.1.0` 的 `30 FPS` 跃升至 **`43 FPS`**，《剑星》2K 性能档达**接近 `60 FPS`**；`v0.2.0` 三个正式包已上传至 Gofile 镜像：`https://gofile.io/d/OOeOcxn6`。

公开文档同步0.2.0与模型median6.66/9.70/12.78ms、偶奇K16和选择性maxnreg255。对0.1.0历史比值约2.38～2.53×；O1历史37.13/49.89/67.69分别对应5.58/5.14/5.30×，如实修正900p分母，不统称5.3～5.6。STACK大减但保留FB04/05残留说明。

[正式回执](ptx-patcher/release-rtx30/v020/README.md)、[部署/验证](ptx-patcher/release-rtx30/v020/validation.json)、[包SHA](ptx-patcher/release-rtx30/v020/packages.json)。临时stage/RGB清理，保留旧包和现场备份，完成后独立commit，无Co-Authored-By，不push。


## 2026-10-27：hip-port Phase17，C32权重尾部追加FP16，采用新默认（闇）

以Phase16 selected/585fda1为唯一性能基线。保留原权重/偏置/尺度所有偏移，FFN在41088、attention在32912字节追加Ampere布局精确FP16；覆盖expand/contract/diag/QKV/OutProj。CUDA仅c32-wave1-fast使用消费点ld.global.nc.v4.u32，地址描述符不跨循环预存sm86_u4。V3标记与v3_独立导出名交叉核验，新旧ABI拒绝混用；PHASE17_C32_HALF=True成为默认，V3限定fast_numeric/W16=1/非temporal，其它模式保留V2模块路径。

原语32768解码位置覆盖全部字节模式，两侧静态MMA/非零C/4步65536输出元素0bit；6个完整C32单核用真实Small权重+相同合成整幅输入，各64CTA全部输出字节0diff。4项ABI/模式错配全部拒绝（含旧Phase16 Host）。三档快验与正式ABBA均对Phase16/14全幅0bit、invalid0、首末帧0bit、32/32 LMem0；非Up保持8KB/OccW11，Up10KB/OccW9。18项Python/LLVM回归通过。仅1个C32模块改变，39模块SHA保留；最终重编C32/Host与实测SHA一致，实际加载40/1918entry。

50warmup/80iter、Small31/Style1、Graph off、默认DVFS，A1/B1/B2/A2 median(ms)：720为14.067/13.785/13.812/14.066，900为23.581/23.203/23.215/23.657，1080为31.608/31.094/31.131/31.828。两次median均值A→B为14.0665→13.7985、23.6190→23.2090、31.7180→31.1125，速度比1.0194/1.0177/1.0195×；三档两次候选均快，采用V3。完整min/median/Wall、六核4次插桩、独立PROFILE_TOTAL与遥测逐轮保留，不拼轮次、不作锁频等频或气泡归因。

实际12个C32缓冲443928→609888B（+165960），纯FP8矩阵82944B，新增FP16矩阵165888B，另72B对齐；不能把旧0.39MiB预算当纯矩阵数据。本机L2查询4194304B但ncu不可用，未采L1/L2命中率/DRAM计数，不宣称100%常驻。六核SASS HMUL2和PRMT均下降，仅作静态指令证据。初始memcpy读只做3/5快验，不充正式长测；单核fixture最初按half为raw输出多分配一倍，哨兵检查后按源码FP8输出修正，无生产数值修复。

[Phase17回执](hip-port/phase17/README.md)、[ABBA与六核](hip-port/phase17/summary.md)、[全核资源/结果](hip-port/phase17/results.md)、[验收](hip-port/phase17/validation.json)。默认产物hip-port/phase17/artifacts/selected/modules（candidate的无重复别名），保留40模块/PTX/生成源与SHA，清理重复RGB/单核权重/中间产物。读取核对外部v0.2.0生产DLL与3ZIP哈希全部未变，不部署、不push，阶段独立commit。


## 2026-10-27：hip-port Phase18，纯half生产者逐站验证＋C256控制（闇）

以Phase17 selected为唯一基线。七候选contract/result/Wave2V/AV/ByteOut/C32Prefix/C32V分别65536种half×256位置、256单点布局穷举，含±0/NaNInf和实际MMA步数，全部0字节差。Wave2 AddZero=true，C32 false；Q/K归一化、float激活、RTZ/MMA顺序不动。ByteOut需D→RDNA4 half位重排，且必须在像素裁剪前全warp完成。首版放在裁剪内致预热挂起约200秒，只终止该进程；修正后再进入正式计时并加防回归，原失败无性能成绩。

七站各三档50/80 ABBA共84次，均Phase17全幅0bit/invalid0/首末0/32LOCAL0；峰值REG/OccW没有逐站下降，不把省转换说成占用率提升。只保留方向稳定的ByteOut（720/900/1080均值差-0.0655/-0.0385/-0.0585ms）与C32V（-0.0630/-0.0325/-0.1100），其它站点混合/近零，不推广。完整7站4次数据与负结果保留。

C256128cap两目标核各8B STACK；全量打包+128仍8B；fuse/pair+128各48B，违反门槛不计时。168cap可零spill、REG168，但256线程块仍OccW8，1080对pack2均值差+0.029ms，无可靠净收益，不采用。另7个资源通过控制1080做28次50/80 ABBA，fuse7对pack2-0.218ms最稳定；pair、全量、cap组合未优先。采用QKV mask7（保留原C64/128位1/2，加C256 bit4），不加pair8，不强压cap。

最终默认仅C32V＋Wave2ByteOut＋QKVmask7；C256仍226regs/48KB/OccW8，**占用率未突破**。相对Phase17最终三档ABBA A1/B1/B2/A2 median(ms)：720为13.817/13.648/13.661/13.852，900为23.212/22.971/23.217/23.366，1080为31.091/30.916/31.037/31.294。两次median均值A→B为13.8345→13.6545、23.2890→23.0940、31.1925→30.9765，速度比1.0132/1.0084/1.0070×；六次配对都更快，采用小幅正收益默认。保留每次min/median/Wall/独立PROFILE_TOTAL、15个C32/Wave2核和原始遥测，不拼轮次/不作等频或气泡归因。

169次成功快验/正式运行全部对Phase17全幅0bit、invalid0、首末0、32/32 LMem0；1次首版ByteOut未完成并排除。最终重建两个变化模块与实测SHA相同，38模块保留Phase17；实际加载40模块1918entry。20项Python/LLVM回归通过。默认产物phase18/artifacts/selected/modules，V3权重ABI和Phase17 Host不变。临时重复模块/输出清理，源/日志/资源/哈希保留。

[Phase18回执](hip-port/phase18/README.md)、[逐站ABBA](hip-port/phase18/site-summary.md)、[C256控制](hip-port/phase18/screen-summary.md)、[最终三档与15核](hip-port/phase18/final-summary.md)、[验收](hip-port/phase18/validation.json)。外部v0.2.0主DLL与三ZIP保护性SHA核验未变，无共享assets/游戏/Magpie/发布包写入，不push，阶段独立commit。下一阶段不在本轮启动。


## 2026-10-27：hip-port Phase19收官，C64/C128 W16 FFN预解码（闇）

严格仅mask1=C64与mask3=C64+C128两候选，Phase18 selected为基线；未做CW_FAST_NUM|4非0bit诊断。复用Phase17解码器和尾部追加，覆盖W16 FFN expand/contract/mix，旧偏移不变；Up/Frag8及attention/diag保留原路径。每MMA消费点NC16B读取，C256原路径不动。W19标记1/3与w19m1_/w19m3_命名空间配对，错标记及旧Host拒绝。

两个候选各三档50/80 ABBA，共24正式+6快验均Phase18全幅0bit、invalid0、首末0、32/32 LMem0，活跃C64/C128≤168regs/OccW≥12。mask1均值A→B为13.6125→13.6095、22.9440→22.9090、30.9365→30.7665ms，但部分方向相反且1080 A2漂移，不单独宣称稳定收益。mask3 A1/B1/B2/A2：720为13.939/13.861/13.916/13.937，900为23.341/23.256/23.229/23.289，1080为31.208/31.069/31.116/31.214；六配对均快，均值13.9380→13.8885、23.3150→23.2425、31.2110→31.0925，约0.3～0.4%速度比，采用mask3默认。原始min/median/Wall/独立profile及遥测保留，默认DVFS不作等频/缓存常驻声明。

实际4个W16缓冲总1476096→2213376B（+737280）；不把全部7核预算当覆盖范围。CPU旧前缀/新增half值偏移测试通过，解码器GPU证明沿用Phase17。最终仅Wave2 fast模块改变，39个保持Phase18；实际加载40/1918，默认源码重编与实测SHA相同，20项既有回归通过。新Host与W19模块必须配套。

[收官回执](hip-port/phase19/README.md)、[两候选ABBA](hip-port/phase19/summary.md)、[验收](hip-port/phase19/validation.json)。默认PHASE19_WAVE_HALF=3；最终产物phase19/artifacts/selected/modules。清理临时重复产物，保留日志/遥测/SHA；外部v0.2.0 DLL/三ZIP保护性哈希未变，不部署、不push，立即独立commit。


## 2026-10-27：hip-port Phase20，单候选half2激活探索，不入默认（闇）

基线Phase19 selected，只有C32+Wave2一个联合候选，无组合扫描。Ampere累加器half位直接做clamp/abs/两次fma.rn.f16x2/mul，再half_pack+D→AB，避开激活处f32展开/标量编码；C32保-0、Wave2消-0，其它残差/归一化不变。GPU65536种half编码中63488有限，各182个有限输入（0.2867%）改变FP8输出，最大幅值编码差1ULP/数值差32；非有限变化0，按当前量化器语义记录。

50/80三档ABBA A1/B1/B2/A2 median：720为13.490/13.400/13.423/13.573，900为22.762/22.552/22.615/22.871，1080为30.576/30.326/30.366/30.780。两个median均值13.5315→13.4115、22.8165→22.5835、30.6780→30.3460，速度比1.0089/1.0103/1.0109×。15次快验/正式运行invalid0/首末0/32LOCAL0，候选重复SHA一致；默认DVFS，分组min/median/Wall/独立profile与15核数据保留，不拼轮次。

候选vsP19可见RGB peak1 PSNR43.582691/46.926900/46.763612dB，maxabs0.050379157/0.036648065/0.040914565；vsF32gold为43.206459/46.671080/46.312321（P19为43.577948/46.975322/46.100947），maxabs0.052299023/0.051891208/0.047206312。三档vsP19均未到50dB，720/900gold分数下降约0.37/0.30dB，不由极少原语边界差宣称图像几乎无损。

裁决：仅约1%提速且质量条件未通过，PHASE20_HALF_ACT=False，保留Phase19严格默认；候选只作诊断并明确有损标记。没有把非0bit混入默认，没有再调参/扫描。[回执](hip-port/phase20/README.md)、[误差与核表](hip-port/phase20/results.md)、[验收](hip-port/phase20/validation.json)。20项既有回归通过，临时重复产物清理、证据保留。外部v0.2.0 DLL/三ZIP保护性哈希未变，不部署、不push，阶段独立commit。


## 2026-10-27：PTX V2.2，SWAR双通道量化＋原生异步绑定，严格0bit（闇）

Zero裁决hip-port收官，主推路线B。以V2.1 hot255为唯一基线，两个单因素与组合，共12次1/1初验＋72次50warmup/80iter正反ABBA/BAAB，无组合扫描。8,944处half2→E4M3x2由29行（8 b32＋2 pred）改20行（5 b32/0 pred），clamp448、双通道舍入偏置、half2比较mask＋lop3选择；GPU33,554,432组配对覆盖全部65,536half位型/63,488有限值、256种对侧位型与位置互换，所测有限和非有限组合均0差异。

FB04/05/06共316处bulk（104/208/4）改用cp.async.mbarrier.arrive.shared::cta.b64，移除对应当场commit/wait。原barrier以ntid.x*ntid.y初始化，每线程arrive1，故绑定必须带默认增量使异步arrival自配平，不能直接.noinc。保留init/arrive/test_wait与控制流。CFG含回边，copy到下一arrive最短路径指令范围3～273/4～841/4～86；不把原316copy错误当成316个线性arrive（实际46/58/4）。4组FB04原有非bulk等待不动。语义来源与审计见回执。

正式组合配对V2.1→V2.2 GPU median均值：720p(sky)6.7390→6.2485、900p(scene)9.7835→9.1223、1080p(scene)12.7797→11.8595ms，耗时下降7.28%/6.76%/7.20%，两方向均赢。异步单因素720p慢0.48%，900/1080快0.63%/1.14%；SWAR单因素三档均赢，耗时降7.14%/5.79%/6.04%。默认DVFS，保留每进程min/median/wall及部分轮次遥测，均值不冒充合并样本median。

84次运行全部相对同配置V2.1严格0bit/maxabs0/PSNR∞/nonfinite0，天空0变号、HF RMS约0.000101989相同。初版脚本把1/1和50/80基线末帧比较而检出61.786dB时间帧差，已拆gold并重新完整运行，失败控制证据保留。静态O4反例：组合FB01 STACK120→168B、LDL+STL315→462；FB02 0→8B、0→2；FB04 80B/118不变；FB05 8→16B、12→18。其余FB00/03/06～14 STACK0；绝不宣称零spill，最终按净帧耗时推荐组合。

推荐DLL `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v22.dll`，266,414,592B，15/15 O4原槽位，未扩节。SHA256 `2705462fc74ca20208ebb83c08cd0e75613ddc220a7834b1e80f4c9aeb0eb90f`，独立推荐入口全15重编相同SHA、CUDA加载通过，既有10项回归通过。兼容CLI默认保留V2.1，新增因子要求显式输出路径。[回执](ptx-patcher/v22/README.md)、[配对表](ptx-patcher/v22/results.md)、[验收](ptx-patcher/v22/validation.json)。清理重复DLL/RGB/PTX/cubin，保留推荐DLL及证据；主fast/V2.1/三正式v0.2.0ZIP保护性SHA未变。不部署、不push，立即独立commit，无Co-Authored-By。

- **2026-10-27 09:49 本机游戏与 Magpie 同步更新为 `V2.2`（待 Zero 回家实机试玩）**：
  已将 `nvngx_dlssnr_sm86_v22.dll`（SHA256 `2705462fc74ca20208ebb83c08cd0e75613ddc220a7834b1e80f4c9aeb0eb90f`）同步覆盖安装至以下 5 个位置并完成 SHA256 校验：
  1. `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_fast.dll`
  2. `/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/nvngx_dlssnr.dll`
  3. `/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/_storage_/nvngx_dlssnr.dll`
  4. `/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64/nvngx_dlssnr.dll`
  5. `/mnt/c/DLSS5-5090-dll/发布打包/Magpie-DLSS5-RTX30-0.2.0/nvngx_dlssnr.dll`

---

## 2026-10-27 19:12 时间节点快照：RTX 3080 Laptop 物理算力上限（Roofline）标尺与 `PTX V2.3` 主动剖析目标

### 1. 硬件双管道算力账本与三档理论物理极限（Roofline）
详见 `/home/lmxxf/work/ai-theorys-study/wechat/short/20261027/如何测算3080laptop的dlss5算力上限.md`：
- **硬件参数（GA104，`48` SMs）**：1080p/900p 满载 `131~139.7 W` 下稳态频率 **`1605 MHz`**（全卡每毫秒 `7,704 万` SM 周期），720p 下 **`1695 MHz`**（每毫秒 `8,136 万` SM 周期）。
  - **一号管道（FP16 Tensor Core，`.f16.f16.f16.f16`）**：每 SM 每周期 `512 FMA = 1,024 FLOPs`（`1605 MHz` 下 **`78.89 TFLOPS`**，`1695 MHz` 下 **`83.31 TFLOPS`**），每条 `HMMA.16816.F16`（`4,096 FLOPs`）耗时 **`4` 个 SM 周期**。
  - **二号管道（INT32 位运算 / FP16x2 向量 / LSU 辅助管道）**：每 SM 每周期 `64` 个 INT32 操作（`2.0` 条 Warp 整数指令/周期/SM），负责软件 FP8 解包/打包、激活函数与访存，平均每周期每 SM 消化约 **`2.0` 条非 `HMMA` 辅助指令**。
- **三档工作量、理论 Roofline 下限（按 70% 双管道重叠率 `max(T_tc, T_alu) + 0.3 * min(T_tc, T_alu)`）与 `V2.2` 实测差距**：

| 分辨率档位 | 实测频率 | 动态 `HMMA` 总数 | 动态非 `HMMA` 辅助指令 | ① 纯矩阵乘下限 `T_tc` | ② 辅助指令下限 `T_alu` | **③ 理论合成极限 (Roofline)** | **④ `V2.2` 实测耗时** | **达成率 / 剩余损耗空间** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **720p (`1280×720`)** | `1695 MHz` | `4,897 万` (`200.6 GF`) | `4.581 亿` | `2.41 ms` | `2.82 ms` | **`3.54 ms`** | **`6.25 ms`** | **56.6%**（差 **`2.71 ms`**） |
| **900p (`1600×900`)** | `1605 MHz` | `7,751 万` (`317.5 GF`) | `7.254 亿` | `4.02 ms` | `4.71 ms` | **`5.92 ms`** | **`9.12 ms`** | **64.9%**（差 **`3.20 ms`**） |
| **1080p (`1920×1080`)** | `1605 MHz` | `1.093 亿` (`447.6 GF`) | `10.211 亿` | `5.67 ms` | `6.63 ms` | **`8.33 ms`** | **`11.86 ms`** | **70.2%**（差 **`3.53 ms`**） |

### 2. 当前正在执行的任务（`PTX V2.3` 主动剖析与优化，已派单给闇 `wE:p1`）
- **核心问题**：为什么 720p 的 Roofline 达成率（`56.6%`，差 `2.71 ms`）明显低于 1080p（`70.2%`，差 `3.53 ms`）？这 `2.7 ~ 3.5 ms` 的未解释损耗具体花在哪些 Kernel 和哪些指令停顿（Stall）上？
- **执行抓手**：
  1. 在 `bench_sky.exe` 中拦截 `nvcuda.dll` 的 Kernel 发射接口（`cuLaunchKernel` / `cuLaunchKernelEx` / `cuGraphLaunch`），采集 `V2.2` 在 720p 与 1080p 下一帧实际发射的全部 Kernel 名称、Grid/Block 尺寸、调用次数与逐核硬件时间戳耗时排行榜（落盘于 `Development/ptx-patcher/v23/`）；
  2. 重点排查：① 实际执行的核是否走了带跨块原子自旋同步的 `*_tilesync_fp8` / `*_wait_fp8`（`fence.acq_rel.gpu;` + `nanosleep` 自旋等待开销）；② `FB07~FB14` 辅助核及与分辨率弱相关的固定开销；③ `even_odd_decode_lines`（每操作数 10 条指令）与 `multidef_nq` 保守回退的进一步瘦身空间；
  3. 对定位到的真实瓶颈实施 `V2.3` 优化并做三档正反 ABBA 实测验证。


## 2026-10-27：PTX V2.3，真实NVAPI逐核账本、弱缩放定位与PRMT8推荐（闇）

以19:12已部署的V2.2为唯一基线。公开nvcuda Module/Launch/Graph/GetProcAddress拦截没有发射记录，NVAPI QueryInterface证实NGX D3D12走CreateCuModule/CreateCuFunction/LaunchCuKernelChain。独立runner按原调用插D3D12硬件timestamp，50warmup/20iter与trace-only对照；稳态每帧82次、40个核名，每链1核，未拆链。83的初计包含一次初始化空链探测。720/1080真实Grid/Block、逐核/FB ledger、原始CSV归档[v23](ptx-patcher/v23/README.md)。两种捕获末帧0bit，插桩会扰动调度，不冒充硬件stall计数器。

逐FB累加mean（720/1080ms）：00 1.86593/4.26317、01 0.53842/1.17612、02 0.46807/0.98586、03 0.50033/1.11677、04 0.63416/0.92662、05 1.99562/3.13231、06 0.03354/0.04413、13 0.05663/0.12662、14 0.03436/0.08909；07～12未发射。核合计mean6.12705/11.86068，核间间隙median0.0215/0.0241ms。按1080/2.25参照，720非线性额外0.856ms，其中04～06贡献约0.840ms；这是缩放账本，不是可回收预算。ViT主体96→160CTA、attention64→96，720小Grid利用率受限。C32首层168×96→240×144，边界扩张/取整，非可见像素窗口数；真实活跃prefix/post HMMA528/580而非统一512。Roofline静态辅助比与70%重叠仍待动态验证，不能把2.7～3.5ms估算差直接当作确定stall或“浪费”。未改外仓文章。

两项同步控制均独立于解包：绕过匹配的ready轮询并去GPU fence，使720PSNR仅15.0～16.4dB、1080仅23.2～24.4dB，不合格，不拿错误输出速度算收益；仅去nanosleep保留全部轮询/fence，50/20 ABBA末帧0bit，720 6.1515→6.1520、1080 11.6585→11.6695ms，无净收益。两者均不进默认，原同步语义保留。真实活跃核mapped静态操作数使用39312次中13600已转发、25552其他编码源、仅160次直接pack_multidef回退（C32两个wait核各64、ViT attention32），不是已证明安全的160处机会，不放宽规则。

PRMT符号复制0xa280/0xb391、mask0x017f017f再shl7/HMUL2，把偶奇解包10→8条。GPU33,554,432组，两parity完整字节对＋256干扰字节、含非有限，逐位0差异；MMA/K次序、图、权重、mapped不变。SASS prefix5456→5352、post5511→5407、ViT expand3289→3225、contract4194→4074，HMMA数不变。静态全导出STACK FB01 168→192B、FB04 80→96B、FB02 8→0B，FB05仍16B，实际C64四活跃核spill增长，C512活跃QKV仍80B；如实保留，不宣称零spill。

三档50/80正反ABBA原轮24次，1080一方向有12.144ms慢样本，因此加完整正反8次确认，全部保留未删样本。原轮配对6.24950→6.12575、9.12125→8.92525、11.87775→11.80750ms；1080确认11.73375→11.55650ms，两方向均赢。原轮＋确认1080为11.80575→11.68200ms。最终三档耗时降1.98%/2.15%/1.05%，6快验＋32正式末帧全0bit/maxabs0/PSNR∞/invalid0。晚段遥测仅覆盖后段控制与确认，不冒充全程锁频实验。[配对表](ptx-patcher/v23/results.md)、[账本](ptx-patcher/v23/kernel-ledger.md)、[验收](ptx-patcher/v23/validation.json)。

推荐独立DLL `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v23.dll`，266414592B、15/15 O4原槽位；SHA256 `b9c463beec6aba945beb2ce31aa96edd52fbae2933cb72cdb6f394b52bda9ca6`。全15重编SHA相同，10项既有回归通过；入口v23/build_recommended.py显式选prmt8，兼容构建默认保留。临时DLL/RGB/PTX/cubin清理，保留推荐DLL及文本证据；已部署V2.2主fast、V2.2副本及三个正式ZIP保护性SHA未变。本轮不部署、不push，立即独立commit，无Co-Authored-By。


## 2026-10-27：PTX V2.4四靶子验证，仅C入推荐（闇）

唯一基线V2.3 b9c463be，用户在启动前已修改WorkingPlan为20:15任务单；原文保留并追加结果。A实现全4,744处UP helper7→5条prmt9180解包，16,777,216组GPU穷举u16＋高位干扰、含非有限0bit。B偏置603f合并当前helper20→19条；bias/quad各33,554,432组全half两位置与干扰对照0bit。7,540个泛型mov拼接匹配不是7,540个合格quad，同基本块、单一定义与无其他消费者审计只融合1,688对（FB01 456、FB02/03各616），两源读取保持原位置，不跨分支或作用域。

C预计算first/last_use，紧邻MMA按需解包，死亡pair归池；额外处理源或mapped别名在首次使用前被MMA覆写，提前保存，保持upfront读取run入口值语义。声明峰值FB00～06分别64→40、80→56、80→56、96→56、160→112、128→80、144→20。两个128warp/64-MMA GPU长run（普通及mapped累加器别名风险）0bit。物理spill反例保留：全导出FB01 STACK192→224B、LDL+STL477→507，FB04 96→88B、125→127，FB05仍16B；虚拟声明缩短不等于物理零spill。

A、bias、bias+quad、C、ABC五因素，每因素三档正反ABBA/BAAB 50/80，共120次；12个单FB cap控制在ABC上各1080正反50/80，共96次；ABC对C条件增量三档正反另24次；加18次初验，258次末帧全部严格0bit/maxabs0/PSNR∞/nonfinite0。另16次50/20 NVAPI硬件时间戳诊断逐FB账本全部末帧0bit，保留测量帧CSV及原始全CSV SHA；不用插桩表代替未插桩净帧比较。10项既有回归通过。

正式C对V2.3 median均值720 6.24900→6.20100、900 9.12850→9.09175、1080 12.20700→12.02650ms，降0.768%/0.403%/1.479%，各档两方向均赢。1080 GPU min均值11.72350→11.72300ms基本不变，属于小幅median收益；默认DVFS，不与历史6.13/8.93/11.68跨轮硬比。A单因素0.069%/-0.221%/2.283%，bias -0.080%/-0.337%/0.627%，bias+quad 0.024%/1.020%/0.093%，均非全档稳定。bias虽省PTX，40活跃核静态SASS总数仍183792；A为181914、B为182567、C为183651、ABC180635。ABC对V2.3虽三档两方向均赢，直接ABC对C时900/1080增量方向变号，所以最终只选C，不把其收益归给A/B。

D修正占用率前提：C64活跃Shared4096B，CUDA occupancy API预测168cap最多12warps/SM，192/224/255为8，非免费扩容、也非动态occupancy计数。255清零活跃C64 spill却整帧慢0.759%；FB04 cap168活跃最大STACK640B、整帧慢6.723%，FB05 cap168虽提升部分理论驻留却STACK最高176B、慢4.219%。FB02 cap255仅0.087%微差且min变慢，其他有方向变号者也不默认保留，沿用原hot255。逐FB诊断FB01 cap255约1.316ms对ABC约1.221，FB04 cap168约1.880对ABC约0.922，FB05 cap168约3.575对ABC约3.207；非ABBA、插桩影响调度，仅作定位佐证。

推荐 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v24.dll`，266414592B，15/15 O4原槽位，SHA256 `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`；mask8，保留SWAR/PRMT8/multidef_nq与原caps。全15重建SHA/PTX均同实测候选。A/B保留可选开关，兼容构建默认不变。[回执](ptx-patcher/v24/README.md)、[因素与cap表](ptx-patcher/v24/results.md)、[逐FB表](ptx-patcher/v24/profile-results.md)、[验收](ptx-patcher/v24/validation.json)。清理临时大DLL/PTX/cubin/RGB与profile runner，保留推荐DLL和文本证据；主fast/V2.3副本仍b9c463be…，三正式ZIP保护性SHA未变。不部署、不push，阶段独立commit，无Co-Authored-By。


## 2026-10-27：PTX V2.5 Hybrid负结果，实测循环/MMA账本补齐（闇）

唯一基线V2.4 1687087e。奇半边and/shr/lop3 0xea/mul、偶半边PRMT保持，共8条、无新增解包临时变量，保留C池/SWAR/mapped/原caps。33,554,432组两parity完整字节对及干扰位GPU对照含非有限全0bit。15/15原槽位O4、266414592B，候选SHA2cd74bfc5aec61bbef4bc153237e5d26048af3471b5d7e6dfcbf6b82c9c0bfd7，仅为失败实验身份。

全网三档50/80正反ABBA/BAAB：V2.4→Hybrid 6.17950→6.20500、8.93025→9.04750、11.72275→11.96775ms，增0.413%/1.313%/2.090%，各档两方向均慢。另做FB00-only：720 6.16425→6.15150ms，1080 11.70750→11.70525ms、正反变号且min变慢，无稳定收益。6快验＋24全网＋16单FB共46次末帧全0bit/maxabs0/PSNR∞/nonfinite0。按任务单条件不升级推荐，不生成正式v25.dll，继续V2.4。

静态40活跃核PRMT25483→19774、IMAD.SHL12169→6456、LOP3 32370→38081、SHF.R6355→12067，总183651→183800；pre_block PRMT732→629、post828→716。非mapped模板减半不等于核总PRMT减半。FB01 STACK224→200B但LDL+STL507→529，不能由静态PRMT下降推断完美均衡。PRMT2cycles、INT0.5cycles仍是成本假设，本轮未测独占吞吐或硬件stall。NVIDIA管道资料也区分IMAD和普通ALU；不按错误单速管道叙事包装负结果。

新增独立诊断DLL/runner，为FB00/04/05追加UAV指针参数，原布局不动，NVAPI专用runner扩展参数、每帧零填/屏障/readback，收敛MMA run由lane0累加：FP8 K32按2条HMMA.16816等价操作、原生F16 K16按1条；另计循环入口、MMA-decoder PTX PRMT/INT/HMUL2及mapped/unmapped事件。三档1/1诊断末帧与原V2.4严格0bit，82次Grid/Block与捕获帧50一致；参数捕获三对50/1参考也0bit。诊断耗时不用于性能。该工具测的是执行的MMA语义等价次数/循环/PTX事件，不冒充原二进制硬件issued计数。

实测ViT expand16圈、contract15＋1尾、QKV15＋1、projection7＋1；attention按tokens288/448/640为5/7/10圈。FB04两个ffwd为7/8圈，多种projection/final_head8，qkv及proj_pool7圈＋循环外计算。720 FB04/05 HMMA等价次数4,694,016/20,185,088；900为7,155,712/27,000,832；1080为9,699,328/35,389,440。循环展开辅助SASS模型对应33,309,600/162,130,944、50,889,440/216,246,272、69,783,168/286,136,320；其HMMA逐核对计数全匹配，但辅助模型未测谓词/分歧、helper、同步重试，不是精确issued数，也不是任意重试上界。仅供循环修正后的可审计预算，频率1695/1605MHz为模型输入。

FB00 HMMA等价次数三档25,696,224/40,691,424/54,871,200；1080 decoder事件unmapped12,892,128、mapped30,109,220，后者占大头，只减非mapped一半PRMT使decoder PTX PRMT事件仅减约14.99%。这些PTX事件可被编译器折叠，不直接套SASS吞吐。静态Grid×Block账本和所谓2.104ms不能单独认证PRMT关键路径。

[回执](ptx-patcher/v25/README.md)、[配对表](ptx-patcher/v25/results.md)、[运行时计数及模型](ptx-patcher/v25/dynamic-ledger.md)、[验收](ptx-patcher/v25/validation.json)。10项既有回归通过。保留V2.4推荐，失败/诊断产物只留源码、日志、参数、计数和SHA；大DLL/PTX/cubin/RGB/runner清理，主fast/V2.4与三ZIP收尾哈希未变。原用户任务单保留并追加实测。阶段独立commit，无Co-Authored-By，不部署、不push。


## 2026-10-28：PTX V2.6 Low/High K16＋mapped零拷贝，三档净提速约2%（闇）

唯一基线V2.4 1687087e。线程内K32的first取byte0/1、second取byte2/3，encoded用9180/b3a2双PRMT8；mapped直接填原native half2 low/high，未改SWAR/独立UP/mapped资格/图/权重/原hot255。数学K映射为2*j-(j&1)+2*phase，A/B共用同一置换且两相覆盖0..31；并非全局连续低/高16，也未证明原厂SM120内部累加顺序更接近。FP16结合次序变化，明确非0bit升级。

零拷贝按半条MMA跟踪读写：首次d0/d1写坏源早于最后mapped读取时，才在首次写坏前mov备份；包含同一原K32内第一K16覆写第二K16要读high的风险，C累加器仍读当前值而非输入快照。非mapped保留首次使用/覆写前解码及死亡寄存器池。768槽位坐标证明、33,554,432组位型解码重排对照0bit；六源全部64种mapped掩码×16组整数矩阵，GPU两版与CPU矩阵积＋0.5全精确。5类128warp长run/别名用例与独立入口快照LowHigh参考全0bit，全mapped无覆写时0临时寄存器/0PRMT。随机FP8、混合FP16/FP8、全mapped FP16各256组，对float64积累后舍入float32参考的RMSE比值1.001/1.024/0.998，同量级但不宣称逐点误差均不增。

三档未插桩bench_sky 50/80正反ABBA/BAAB，V2.4→V2.6 median均值6.09950→5.98000、8.92475→8.72200、11.73225→11.46250ms，耗时降1.959%/2.272%/2.299%，各档两个方向皆赢；GPU min均值6.02800→5.91325、8.71250→8.52300、11.49050→11.22550。默认DVFS，同轮比较，不用旧冷/热轮次估算成绩。V1备份经SHA3f934a0a核验，各档正反另作输出参考，不将其非配对时长当提速基准。

正式三档相对V2.4 PSNR61.819121/61.767286/58.421047dB，maxabs0.0048828125/0.005615234375/0.009765625；相对V1为62.124349/61.854969/60.884550dB，maxabs0.00439453125/0.006103515625/0.00732421875。peak1、bench最终RGB域，是移植实现间距离，非原生sm120/整网FP32绝对质量gold。9快验＋24配对计时＋6V1参考共39次末帧全部finite，同版本同配置重复0bit，跨版非0bit；天空变号0，V2.6正式HF RMS0.000102746766。没有外推所有实机动态场景。

全导出生成路径mapped PRMT减少21712条，真实模型备份mov0；对应旧V2.5 FB00/1080的60,218,440次mapped PTX事件在代码生成层消失，不当成同量硬件issued削减。40个唯一活跃核静态PRMT25483→19864、总SASS183651→178170、HMMA13188不变。FB00临时pool声明峰值40→24，其他FB最大值仍56/56/56/112/80/20，由encoded输入控制；不是全kernel临时为零。活跃C32 prefix REG234→196，inpview234→200，ds231→199，outview236→197，up229→212；post没有相同下降。全导出FB01最大STACK224→104B、LDL+STL507→381；活跃outview224→96、ds/inpview80→64，但up88→96回退。FB04/05仍88/16B，FB05LDL+STL18→16。资源复核后保留原cap，不宣称零spill或全局最优。

推荐 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v26.dll`，266414592B、15/15 O4原槽位、无扩节；SHA256 `04b01f0c963061e24d1fd34f5097043d4eeddb001c846d9002e4e2bdc73ad788`。全15重编与实测候选SHA及PTX一致，10项既有回归通过。显式lowhigh布局/lowhigh8解码/mask8/SWAR/nonquantized mapped成对门控，兼容旧版默认保留。[回执](ptx-patcher/v26/README.md)、[正式表](ptx-patcher/v26/results.md)、[验收](ptx-patcher/v26/validation.json)。清理重复大产物，保留推荐DLL与文本证据；主fast/V2.4/V1备份/正式ZIP哈希未变。不部署、不push，阶段独立commit，无Co-Authored-By。
