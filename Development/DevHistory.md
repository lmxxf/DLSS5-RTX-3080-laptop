# DLSS 5 -> NVIDIA RTX 3080 Laptop (`sm_86` Ampere) 移植开发历史与实测回执 (`DevHistory.md`)

**硬件环境**：NVIDIA GeForce RTX 3080 Laptop GPU（GA104，`sm_86`，48 SMs，16,383.5 MiB GDDR6，101,376 B Shared Memory/SM，Boost `P0: 1725 MHz SM / 7001 MHz Mem / 132.1 W`，CUDA Driver `13040`）  
**基线来源**：`DLSS5-AMD 0.44`（含 71-block `1x Original` 模型与 31-block `0.5x Small` 模型）

---

## 2026-10-24：全栈移植、V3+ SSA 代数洗牌消除 + 零 `LMem` 栈溢出优化与全档位基准验收

### 1. 仓库初始化与外部资产解耦
- 将 639 个模型权重与资产文件（根目录 71-block `1x Original` 权重 + `small/` 31-block `0.5x Small` 93 个权重文件）从 `OptiScaler-REFramework-DLSS5-AMD-0.44.zip` 提取至 `/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/`，与 Git 源码仓分离，保持 Git 仓库轻量纯净。
- 配置 `.gitignore` 忽略二进制权重（`*.f16`, `*.f32`, `*.bin`）、编译产物（`*.hsaco`, `*.cubin`, `*.ptx`, `*.dll`, `*.addon64`, `*.exe`）及第三方头文件缓存（`third_party/`）。

### 2. RDNA4 Wave32 -> Ampere `sm_86` 设备端兼容层 (`hip/sm86_compat.h`) 与 V3+ SSA 编译器优化管线 (`hip/build_sm86_modules.py`)
- **构建管线**：
  - `clang++ -x cuda --cuda-device-only --cuda-gpu-arch=sm_86 -Xclang -fnative-half-type -Xclang -fallow-half-arguments-and-returns -nocudainc -nocudalib -std=c++20 -O3 -S -emit-llvm` -> `opt-14 -instnamer -loop-simplify -lcssa` -> `cancel_wmma_shuffles_ir` (SSA Pass) -> `opt-14 -O3 -disable-loop-unrolling` -> `llc-14 -march=nvptx64 -mcpu=sm_86 -O3` -> `hip/ptx2cubin`（生成 `sm_86` ELF `.cubin` 并原位保存为 `.hsaco`），全量 **40/40 模块、1,970 个 Kernel 入口**实机校验通过。
- **V3+ 四大核心指令与编译器优化**：
  1. **无分支向量化 `prmt.b32` + `mul.rn.f16x2 (0x5c005c00)` E4M3x8 -> FP16x8 解包 (`sm86_unpack_e4m3x8`)**：利用 IEEE FP16 次正规数乘以 $2^8$ (`0x5c00`) 在硬件内一步完成 E4M3 正规数与次正规数的精确转换，8 个 E4M3 字节仅需 4 条 `prmt.b32` + 4 条 `mul.rn.f16x2`，零分支。
  2. **4-shfl XOR-Benes A/B 网络 (`sm86_frag_benes4`) 与 8-shfl XOR-Benes C/D 网络 (`__sm86_c_to_ampere` / `__sm86_d_to_rdna4`)**：将 A/B 片段洗牌从 12 条 `shfl.sync` 降至 **4 条 `shfl.sync`**，将 C/D 累加器洗牌从 20 条 `shfl.sync` 降至 **8 条 `shfl.sync`**。
  3. **LLVM IR SSA 跨 K 循环 C/D 互逆洗牌代数抵消 (`cancel_wmma_shuffles_ir`) + 操作数 CSE/LICM (`cse_and_hoist_prep_calls`)**：
     - 在 LCSSA 形式下自动消除 K 累加循环（含普通循环、完全展开循环、Diamond-PHI `if(live)` 循环以及 K32 `acc = H(acc + sum)` / 4-partition 分段归并循环）内部的 `@__sm86_d_to_rdna4` 与 `@__sm86_c_to_ampere` 互逆调用对，使累加器在整个 K 循环期间保持 Ampere `m16n8k16` 原生寄存器布局，仅在循环退出时转换一次。
     - 对同一 A/B 片段在多次 WMMA 调用间的 `@__sm86_prep_fp8` / `@__sm86_prep_f16` 执行跨基本块 CSE 与循环不变量外提（LICM）。
  4. **NVPTX Local Memory (`__local_depot`) 零溢出优化**：
     - 在 `wave_owned_c32.inc` 中将跨 `qt` 循环存活的 QKV 片段移入 Shared Memory (`cw_qkv_smem`)；
     - 在 `wave_owned_mh.inc` 中将 Q 存入闲置的 `plane1[64*C]`、K 存入 `plane_k[64*C]`（总静态 Shared Memory $\le 48\text{ KB}$），并将 `W2_FFN_QT_BATCH` 调整为 `2`；
     - 在 `vit_stream.inc` 中将 `vit_stream_qkv_frag_bin_w5f8` 的 `acc[2]` 标量化为 `acc0, acc1` 并展开归并尾循环；
     - 在 `build_sm86_modules.py` 中自动为 `<=16` 步内层寄存器切片循环注入 `_Pragma("unroll")`，使 LLVM SROA 将 `f8`/`h8`/`i2` 局部数组 100% 提升至 SSA 寄存器，**32 个活跃内核中 29 个实现 `LMem = 0 B`**！

### 3. 宿主运行时与 D3D12-CUDA 桥接层 (`Development/HIP/hip_api.h`, `hip_d3d12_bridge.h`, `hip_reference_network.h`)
- Windows 下加载 `nvcuda.dll`，Linux/WSL 下加载 `libcuda.so.1`，自动管理 `cuDevicePrimaryCtxRetain` 与 `thread_local` 上下文绑定。
- 完整实现 `cuDeviceGetLuid` D3D12 适配器 LUID 匹配、`cuImportExternalMemory`、`cuExternalMemoryGetMappedBuffer`、`cuImportExternalSemaphore`、`cuWaitExternalSemaphoresAsync`、`cuSignalExternalSemaphoresAsync`。
- 交叉编译产出 Windows `LmxxfNrRuntime.dll`（4.9 MiB）、`dlss5-amd.addon64`（5.1 MiB）与 `frame.exe`（2.3 MiB）。

---

### 4. RTX 3080 Laptop GPU 全档位实测结果 (`Development/HIP/benchmark_cuda_nn.cpp`)

#### 4.1 四个阶段端到端耗时演进对照表（GPU Median `ms/frame`，Warmup 5 帧，测量 20 帧）

| 模型与分辨率档位 | 块数 | Baseline (Initial Port) | Phase 1 (`c32` 0-LMem) | Phase 2 (`w2` + Inner Unroll) | **Phase 3 (V3+ SSA + 0-LMem)** | **总提速比 (vs. Baseline)** |
|:---|---:|---:|---:|---:|---:|---:|
| **`0.5x Small 900p`** (`1600×1024`) | 31 | `208.749 ms` | `144.220 ms` | `144.220 ms` | **`55.108 ms`** (min `54.818 ms`, **18.1 FPS**) | **`3.79×` (`-73.6%`)** |
| **`0.5x Small 1080p`** (`1920×1152`) | 31 | `278.075 ms` | `187.861 ms` | `169.508 ms` | **`74.089 ms`** (min `73.443 ms`, **13.5 FPS**) | **`3.75×` (`-73.4%`)** |
| **`1x Original 900p`** (`1600×960`) | 71 | `362.415 ms` | `254.476 ms` | `254.476 ms` | **`92.755 ms`** (min `91.679 ms`, **10.8 FPS**) | **`3.91×` (`-74.4%`)** |
| **`1x Original 1080p`** (`1920×1152`) | 71 | `493.640 ms` | `354.928 ms` | `314.841 ms` | **`131.765 ms`** (min `131.066 ms`, **7.6 FPS**) | **`3.75×` (`-73.3%`)** |

- 全部 4 组测试 `invalid (NaN/Inf) = 0`，首尾帧 `bit_diff = 0`，`SP_STATS fallback = 0, errors = 0`。

#### 4.2 `0.5x Small 1080p` (`1920×1152`) 完整 32 核属性与耗时普查表（Total = `74.516 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
c32_wave1_prefix_b8d_w16                             1    11.307   11306.9  34560    32  162      0  10240     9
c32_wave1_post_b8_w16                                1    10.433   10432.5  34945    32  167      0  10240     9
vit_stream_qkv_frag_bin_w5f8                         8     5.157     644.6    768   160  128      0  16384    15
vit_stream_contract_frag_bstream_bout_compactw_w16   8     3.775     471.9    640    32  157      0   4096    13
c256_wave2_bi_bo_w16                                 3     3.696    1232.1    135   256  241      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.156     394.4   2560    32  117      0      0    16
c128_wave2_bi_bo                                     2     2.921    1460.7    540   128  248      0  24576     8
c64_wave2_bi                                         1     2.815    2815.0   2220    64  247     64  12288     8
c32_wave1_up_b8_w16                                  1     2.799    2798.6   8712    32  202      0  10240     9
c32_wave1_finish_dcrop_b8d_w16                       1     2.710    2709.5   8833    32  146      0  10240     9
c32_wave1_mapped_b8_w16                              1     2.553    2552.8   8640    32  159      0  10240     9
c32_wave1_finish_b8_w16                              1     2.512    2511.9   8760    32  151      0  10240     9
c512_qkv_attention_compact_w16                       4     2.330     582.4    640    64  255    232   6144     8
c64_wave2_bi_bo                                      1     2.298    2297.9   2160    64  248      0  12288     8
vit_attention_fused_640_bytein_bout                  8     2.277     284.6   1280    32  159      0      0    12
c64_wave2_up_lb_sh                                   1     2.268    2268.2   2196    64  255      0  12288     8
c64_wave2_bi_ho                                      1     2.056    2056.2   2257    64  248      0  12288     8
c256_wave2_bi_w16                                    1     1.729    1728.5    160   256  247     64  49152     8
c128_wave2_up_lb_sh                                  1     1.704    1703.7    558   128  255      0  24576     8
c128_wave2_bi_ho                                     1     1.579    1579.0    589   128  248      0  24576     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.530     191.3    640    32  217      0      0     9
split_ffn_one_w2f8_w16_bin                           4     1.013     253.4    544    64  248      0      0     8
mh_attention_project_frag_c512_w16_u4_bout           3     0.452     150.8   1080    32  127      0      0    16
split_projection_frag_w16_bskip                      4     0.392      98.0   1080    32  137      0   1024    14
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.372     185.9   1280    32   67      0   2176    16
mh_pool_project_c32_b8_out8                          1     0.148     148.2  34560    32   40      0      0    16
mh_attention_project_frag_c512_w16_u4                1     0.144     144.4   1080    32  127      0      0    16
mh_pool_project_group_c64_hin_out8_f8w16             1     0.123     122.9   2160    64  118      0   1152    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.088      88.1    540   128  118      0   2176    16
mh_pool_project_group_c256_out8_f8w16                1     0.079      78.8    135   256  118      0   4224    16
mh_pool_project_group_c512_out8_f8w16                1     0.076      75.8     40   512  118      0   8320    16
vit_gather_b8                                        2     0.025      12.3    640   256   16      0      0   128
```

#### 4.3 `1x Original 1080p` (`1920×1152`) 完整 35 核属性与耗时普查表（Total = `131.590 ms`）

```
Kernel Name                                      Calls Total(ms)   Avg(us)   Grid Block Regs   LMem   SMem  OccW
sp_run256_w16                                        2    16.316    8158.1    893   256  255    568  49152     8
c128_wave2_bi_bo                                    10    14.720    1472.0    540   128  248      0  24576     8
c32_wave1_prefix_b8d_w16                             1    11.235   11235.3  34560    32  162      0  10240     9
c32_wave1_post_b8_w16                                1    10.340   10340.4  34945    32  167      0  10240     9
c32_wave1_chain_w16                                  4     9.993    2498.3   8833    32  144      0  10240     9
c64_wave2_bi_bo                                      5     9.638    1927.5   2160    64  248      0  12288     8
c512_qkv_attention_compact_w16                      16     7.903     493.9    640    64  255    232   6144     8
vit_stream_qkv_frag_bin_w5f8                         8     5.374     671.7    768   160  128      0  16384    15
split_ffn_one_w2f8_w16_bin                          16     4.058     253.6    544    64  248      0      0     8
vit_stream_contract_frag_bstream_bout_compactw_w16   8     3.775     471.9    640    32  157      0   4096    13
c256_wave2_bi_bo_w16                                 3     3.754    1251.3    135   256  241      0  49152     8
vit_expand_blocked_fp8_frag_bytein_w16               8     3.129     391.2   2560    32  117      0      0    16
c64_wave2_bi                                         1     2.781    2781.2   2220    64  247     64  12288     8
c32_wave1_up_b8_w16                                  1     2.764    2763.8   8640    32  202      0  10240     9
c32_wave1_finish_dcrop_b8d_w16                       1     2.731    2730.9   8760    32  146      0  10240     9
c32_wave1_mapped_b8_w16                              1     2.582    2582.4   8640    32  159      0  10240     9
c32_wave1_finish_b8_w16                              1     2.522    2522.1   8760    32  151      0  10240     9
c64_wave2_up_lb_sh                                   1     2.260    2260.0   2160    64  255      0  12288     8
mh_attention_project_frag_c512_w16_u4_bout          15     2.204     147.0   1080    32  127      0      0    16
vit_attention_fused_640_bytein_bout                  8     2.201     275.2   1280    32  159      0      0    12
c64_wave2_bi_ho                                      1     2.088    2087.9   2220    64  248      0  12288     8
c256_wave2_bi_w16                                    1     1.748    1747.8    150   256  247     64  49152     8
c128_wave2_up_lb_sh                                  1     1.708    1707.8    558   128  255      0  24576     8
split_projection_frag_w16_bskip                     16     1.607     100.4   1080    32  137      0   1024    14
c128_wave2_bi_ho                                     1     1.576    1575.9    589   128  248      0  24576     8
vit_stream_project_n64_bb_bout_compactw_w16          8     1.494     186.7    640    32  217      0      0     9
decoder_project2x_h16w_byteout_w_bin_f8w16           2     0.371     185.3   1280    32   67      0   2176    16
mh_attention_project_frag_c512_w16_u4                1     0.151     151.4   1080    32  127      0      0    16
mh_pool_project_c32_b8_out8                          1     0.148     148.5  34560    32   40      0      0    16
mh_pool_project_group_c64_hin_out8_f8w16             1     0.125     124.7   2160    64  118      0   1152    16
mh_pool_project_group_c128_hin_out8_f8w16            1     0.088      88.1    540   128  118      0   2176    16
mh_pool_project_group_c512_out8_f8w16                1     0.078      77.8     40   512  118      0   8320    16
mh_pool_project_group_c256_out8_f8w16                1     0.078      77.8    135   256  118      0   4224    16
vit_gather_b8                                        2     0.025      12.3    640   256   16      0      0   128
sp_recover256_w16                                    2     0.016       8.2      1   256  255    728  49152     8
sp_init                                              2     0.009       4.5     11   256   10      0      0   128
```
