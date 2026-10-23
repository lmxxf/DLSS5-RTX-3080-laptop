# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植开发历史与实测回执 (`DevHistory.md`)

**硬件环境**：NVIDIA GeForce RTX 3080 Laptop GPU（GA104，`sm_86`，48 SMs，16,383.5 MiB GDDR6，101,376 B Shared Memory/SM，Boost `P0: 1725 MHz SM / 7001 MHz Mem / 132.1 W`，CUDA Driver `13040`）  
**基线来源**：`DLSS5-AMD 0.44`（含 71-block `1x Original` 模型与 31-block `0.5x Small` 模型）

---

## 2026-10-24：全栈移植、V5 预洗牌 + 32/32 零 `LMem` 栈溢出优化与 Linux/Windows 全档位验收

### 1. 仓库初始化与外部资产解耦
- 将 639 个模型权重与资产文件（根目录 71-block `1x Original` 权重 + `small/` 31-block `0.5x Small` 93 个权重文件）从 `OptiScaler-REFramework-DLSS5-AMD-0.44.zip` 提取至 `/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/`，与 Git 源码仓分离，保持 Git 仓库轻量纯净。
- 配置 `.gitignore` 忽略二进制权重（`*.f16`, `*.f32`, `*.bin`）、编译产物（`*.hsaco`, `*.cubin`, `*.ptx`, `*.dll`, `*.addon64`, `*.exe`）及第三方头文件缓存（`third_party/`）。

### 2. RDNA4 Wave32 -> Ampere `sm_86` 设备端兼容层 (`hip/sm86_compat.h`) 与 V5 SSA 编译器优化管线 (`hip/build_sm86_modules.py`)
- **构建管线**：
  - `clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -Xclang -fnative-half-type -Xclang -fallow-half-arguments-and-returns -nocudainc -nocudalib -std=c++20 -O3 -S -emit-llvm` -> `opt-14 -instnamer -loop-simplify -lcssa` -> `cancel_wmma_shuffles_ir` (SSA Pass) -> `opt-14 -O3 -disable-loop-unrolling` -> `llc-14 -march=nvptx64 -mcpu=sm_86 --fp-contract=fast -O3` -> `hip/ptx2cubin`（生成 `sm_86` ELF `.cubin` 并原位保存为 `.hsaco`），全量 **40/40 模块、1,970 个 Kernel 入口**实机校验通过。
- **V5 六大核心指令与编译器优化**：
  1. **无分支单基本块 `sm86_f32_to_e4m3_byte` 与无分支向量化 `prmt.b32` + `mul.rn.f16x2 (0x5c005c00)` E4M3x8 -> FP16x8 解包 (`sm86_unpack_e4m3x8`)**：将 FP32->E4M3 量化全部收拢为单基本块 `selp` 无分支实现，并利用 IEEE FP16 次正规数乘以 $2^8$ (`0x5c00`) 在硬件内一步完成 E4M3 正规数与次正规数的精确转换，8 个 E4M3 字节仅需 4 条 `prmt.b32` + 4 条 `mul.rn.f16x2`。
  2. **Shuffle-Before-Unpack `__sm86_prep_fp8` 与 8-shfl XOR-Benes C/D 网络 (`__sm86_c_to_ampere` / `__sm86_d_to_rdna4`)**：先对两个 32 位 E4M3 打包字执行 4 条 `shfl.sync`（将 `selp` 从 16 条降至 6 条），再经奇偶 lane 选择器 `0x3424 / 0x1404` 一步 `prmt.b32` 展开为 4 个 `f16x2`。
  3. **8 字节预洗牌 `sm86_preshuffle_fp8` + 零洗牌 `sm86_wmma_fp8_preshuffled_ab`**：在 `wave_owned_c32.inc` 与 `wave_owned_mh.inc` 中，将 `Q`、`K`、`V` 与 `prob` 在写入 Shared Memory / 寄存器前预洗牌为 8 字节 Ampere 布局 (`i2`)，使 `Q*K` 与 `P*V` WMMA 循环内部**完全省去跨线程洗牌 (`0 shfl.sync`)**，且跨循环常驻仅占 2 个寄存器 (`i2`) 而非 4 个寄存器 (`u4`)。
  4. **`vit_stream_qkv_frag_bin_w5f8` 共享内存预解包/预洗牌 (`sm86_wmma_fp8_prepped_b`)**：在 `vit_stream.inc` 中由 4 个搬运 Warp (`t < 128`) 在写入 16 KB `lds` 时直接完成 `__sm86_prep_fp8`，使全部 5 个计算 Warp 在内层 K 循环中直接从 `lds` 加载 `sm86_u4` 送入 `mma.sync`（`vit_stream_qkv` 耗时从 `5.37 ms` 降至 **`3.95 ms`**）。
  5. **LLVM IR SSA 跨 K 循环 C/D 互逆洗牌代数抵消 (`cancel_wmma_shuffles_ir`) + 单基本块操作数/解包 CSE (`cse_and_hoist_prep_calls`)**：
     - 在 LCSSA 形式下自动消除 K 累加循环（含普通循环、完全展开循环、Diamond-PHI `if(live)` 循环以及 K32 `acc = H(acc + sum)` / 4-partition 分段归并循环）内部的 `@__sm86_d_to_rdna4` 与 `@__sm86_c_to_ampere` 互逆调用对，使累加器在整个 K 循环期间保持 Ampere `m16n8k16` 原生寄存器布局。
     - 对同一基本块内共享的 `@__sm86_prep_fp8`、`@__sm86_prep_f16` 与 `@sm86_unpack_e4m3x8` 自动执行 SSA 去重。
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
| **`0.5x Small 900p`** (`flags_900_05x.flags`) | 31 | `1600×1024` | **`46.948 ms`** | **`47.821 ms`** | **21.3 FPS** | `0` | `0` (`maxabs=0`) | `1.161911` / `1.149981` |
| **`0.5x Small 1080p`** (`same.flags`) | 31 | `1920×1152` | **`62.993 ms`** | **`64.230 ms`** | **15.9 FPS** | `0` | `0` (`maxabs=0`) | `1.161226` / `1.149793` |
| **`1x Original 1080p`** (`flags_1080_1x.flags`) | 71 | `1920×1152` | **`114.362 ms`** | **`115.254 ms`** | **8.7 FPS** | `0` | `0` (`maxabs=0`) | `1.168327` / `1.156113` |

- 含 D3D12 Encode、D3D12 Direct Input、CUDA Shared Resource/Fence Handoff、31/71-Block Neural Network、D3D12 Neural Texture、D3D12 Decode 与 Readback 完整链路，D3D12 编解码与跨 API 同步总开销仅 **`~1.5 ms/frame`**。

#### 4.3 `0.5x Small 1080p` (`1920×1152`) 完整 32 核属性与耗时普查表（32/32 核 `LMem = 0 B`，Total = `63.386 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
c32_wave1_prefix_b8d_w16                             1     8.253    8253.4  34560    32  207      0  10240     9
c32_wave1_post_b8_w16                                1     7.376    7375.9  34945    32  201      0  10240     9
vit_stream_qkv_frag_bin_w5f8                         8     4.255     531.9    768   160  135      0  16384    15
vit_stream_contract_frag_bstream_bout_compactw_w16   8     3.748     468.5    640    32  162      0   4096    12
c256_wave2_bi_bo_w16                                 3     3.797    1265.7    135   256  240      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.241     405.1   2560    32  119      0      0    16
c128_wave2_bi_bo                                     2     2.899    1449.5    540   128  249      0  24576     8
c64_wave2_bi                                         1     2.232    2232.3   2220    64  249      0  12288     8
c64_wave2_up_lb_sh                                   1     2.175    2175.0   2196    64  249      0  12288     8
vit_attention_fused_640_bytein_bout                  8     2.165     270.7   1280    32  112      0      0    16
c64_wave2_bi_ho                                      1     1.992    1991.7   2257    64  248      0  12288     8
c32_wave1_up_b8_w16                                  1     2.038    2037.8   8712    32  240      0  10240     8
c128_wave2_up_lb_sh                                  1     1.668    1668.1    558   128  249      0  24576     8
c32_wave1_finish_dcrop_b8d_w16                       1     1.975    1975.3   8833    32  169      0  10240     9
c64_wave2_bi_bo                                      1     1.862    1861.6   2160    64  249      0  12288     8
c32_wave1_mapped_b8_w16                              1     1.851    1851.1   8640    32  193      0  10240     9
c32_wave1_finish_b8_w16                              1     1.790    1790.0   8760    32  169      0  10240     9
c256_wave2_bi_w16                                    1     1.617    1616.9    160   256  240      0  49152     8
c128_wave2_bi_ho                                     1     1.553    1553.4    589   128  248      0  24576     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.528     191.0    640    32  218      0      0     9
c512_qkv_attention_compact_w16                       4     1.157     289.3    640    64  229      0   6144     8
split_ffn_one_w2f8_w16_bin                           4     0.912     228.1    544    64  149      0      0    12
mh_attention_project_frag_c512_w16_u4_bout           3     0.433     144.4   1080    32  133      0      0    15
split_projection_frag_w16_bskip                      4     0.411     102.9   1080    32  135      0   1024    15
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.383     191.3   1280    32   71      0   2176    16
mh_attention_project_frag_c512_w16_u4                1     0.147     147.5   1080    32  133      0      0    15
mh_pool_project_c32_b8_out8                          1     0.138     138.2  34560    32   44      0      0    16
mh_pool_project_group_c64_hin_out8_f8w16             1     0.118     117.8   2160    64  121      0   1152    16
mh_pool_project_group_c256_out8_f8w16                1     0.084      84.0    135   256  121      0   4224    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.086      86.0    540   128  121      0   2176    16
mh_pool_project_group_c512_out8_f8w16                1     0.079      78.8     40   512  121      0   8320    16
vit_gather_b8                                        2     0.027      13.3    640   256   16      0      0   128
```

#### 4.4 `1x Original 1080p` (`1920×1152`) 完整 35 核属性与耗时普查表（Total = `113.296 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
sp_run256_w16                                        2    16.453    8226.3    893   256  255    568  49152     8
c128_wave2_bi_bo                                    10    14.688    1468.8    540   128  249      0  24576     8
c64_wave2_bi_bo                                      5     8.924    1784.8   2160    64  249      0  12288     8
c32_wave1_prefix_b8d_w16                             1     8.499    8499.2  34560    32  207      0  10240     9
c32_wave1_post_b8_w16                                1     7.486    7486.5  34945    32  201      0  10240     9
c32_wave1_chain_w16                                  4     7.129    1782.3   8833    32  168      0  10240     9
c512_qkv_attention_compact_w16                      16     4.596     287.2    640    64  229      0   6144     8
vit_stream_contract_frag_bstream_bout_compactw_w16   8     3.989     498.7    640    32  162      0   4096    12
vit_stream_qkv_frag_bin_w5f8                         8     3.971     496.4    768   160  135      0  16384    15
split_ffn_one_w2f8_w16_bin                          16     3.618     226.2    544    64  149      0      0    12
c256_wave2_bi_bo_w16                                 3     3.587    1195.6    135   256  240      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.187     398.4   2560    32  119      0      0    16
mh_attention_project_frag_c512_w16_u4_bout          15     2.160     144.0   1080    32  133      0      0    15
vit_attention_fused_640_bytein_bout                  8     2.114     264.3   1280    32  112      0      0    16
c64_wave2_bi                                         1     2.017    2017.1   2220    64  249      0  12288     8
c32_wave1_finish_dcrop_b8d_w16                       1     2.008    2008.1   8760    32  169      0  10240     9
c64_wave2_up_lb_sh                                   1     2.006    2006.0   2160    64  249      0  12288     8
c32_wave1_up_b8_w16                                  1     2.005    2004.9   8640    32  240      0  10240     8
c64_wave2_bi_ho                                      1     1.947    1946.6   2220    64  248      0  12288     8
c32_wave1_mapped_b8_w16                              1     1.913    1912.8   8640    32  193      0  10240     9
c128_wave2_bi_ho                                     1     1.880    1880.1    589   128  248      0  24576     8
c32_wave1_finish_b8_w16                              1     1.791    1791.0   8760    32  169      0  10240     9
split_projection_frag_w16_bskip                     16     1.605     100.3   1080    32  135      0   1024    15
c256_wave2_bi_w16                                    1     1.583    1583.1    150   256  240      0  49152     8
c128_wave2_up_lb_sh                                  1     1.542    1542.1    558   128  249      0  24576     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.490     186.2    640    32  218      0      0     9
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.372     185.9   1280    32   71      0   2176    16
mh_pool_project_c32_b8_out8                          1     0.152     151.6  34560    32   44      0      0    16
mh_attention_project_frag_c512_w16_u4                1     0.147     147.5   1080    32  133      0      0    15
mh_pool_project_group_c64_hin_out8_f8w16             1     0.119     118.8   2160    64  121      0   1152    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.098      98.3    540   128  121      0   2176    16
mh_pool_project_group_c256_out8_f8w16                1     0.089      89.1    135   256  121      0   4224    16
mh_pool_project_group_c512_out8_f8w16                1     0.079      78.8     40   512  121      0   8320    16
vit_gather_b8                                        2     0.026      12.8    640   256   16      0      0   128
sp_recover256_w16                                    2     0.016       8.2      1   256  255    728  49152     8
sp_init                                              2     0.010       5.1     11   256   10      0      0   128
```
