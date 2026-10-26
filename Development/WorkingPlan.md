# DLSS 5 (`310.9.16.0` 31-Block Small) — RTX 30 系 (`sm_86`) 独立引擎 (`hip-port`) 深度优化工作计划

> **⚠️ 工程与 Git 提交铁律（必读）**：
> 1. **阶段即提交**：每完成一个功能修改或一个优化阶段（Phase）并通过实测验证、更新 `DevHistory.md` 与本文件后，**必须立即执行一次 `git commit`（严禁添加 `Co-Authored-By` 尾巴）**，绝不允许跨多个阶段不提交。
> 2. **保持仓库轻量纯净**：提交前必须确保 `.gitignore` 生效且清理掉实验目录下的临时大二进制产物（如重复的 `artifacts/` 模块副本、`*.rgb32`、`*.ll`、临时 dump 等），只保留最终选定模块与 Markdown/JSON 实验证据。

---

## 1. 战略定位与当前双路线最新战况（截至 Phase 15B）

1. **路线 B（`Development/ptx-patcher/`，`v0.1.0` 已发布稳定标尺）**：
   - 直接改写原版 `310.9.16.0` `nvngx_dlssnr.dll` 内置的 15 个 Fatbin PTX（两条 IEEE 754 `f16x2` 硬件算术恒等式 + 多定义 `mapped` 过滤），实现 **15/15 满血 `O4` 原槽位装入 + 0 天空色带**。
   - RTX 3080 Laptop (`sm_86`, 132~140W) 耗时：720p **`15.83 ms`**、900p **`24.47 ms`**、1080p **`32.04 ms`**。

2. **路线 A（`Development/hip-port/`，独立 CUDA 引擎，当前主攻战场）**：
   - 经过 Phase 1 ~ Phase 14 的连续攻坚（`.f16.f16.f16.f16` 满速 Tensor Core、CPU 静态权重 Ampere 预洗牌、IR 16B 对齐升级、4-u32 C/D Benes、2-shfl D→AB/V 直通、9 核 `maxnreg` 上限、单次 FP8 内部 448 饱和、C32 FFN/AV `half2->FP8` 直包、修复 `<=256 token` legacy ViT attention 二次洗牌 Bug 并切换 `400` 桶），**`Phase 14 selected` 在三档分辨率上已全面超越原版 PTX 标尺**：
     - **720p（`1280×768`）**：GPU median **`14.15 ms`**（min `14.08 ms`，核累计 `13.50 ms`）
     - **900p（`1600×1024`）**：GPU median **`23.72 ms`**（min `23.38 ms`，核累计 `21.77 ms`）
     - **1080p（`1920×1152`）**：GPU median **`31.83 ms`**（min `31.25 ms`，核累计 `28.65 ms`）
     - 全网 **32/32 个活跃核 `LMem = 0 B`**，首末帧 `0 bit-diff`，`invalid = 0`。

3. **Phase 15 / 15B 质量审计正式结案（解除性能暂停令）**：
   - Phase 15B（`155af20`）已通过全网逐阶段特征追踪与 CPU 逐位核验（65,536 个 ViT expand 预激活值、8,126,464 个 ViT attention AV 字节、输出头逐位复算）证明：**代码中不存在算子索引或布局 Bug**。合成图案在 720p (`43.58 dB`) 和 `1024² codec-ramp` (`43.44 dB`) 相对 FP32 累加参考的差异，完全是 `.f16.f16.f16.f16` 每 K8 步 FP16 RNE 舍入在 31 层网络上的正常物理精度边界（真实《明末》截图在 7 种几何下 PSNR 高达 `57.0 ~ 60.9 dB`，且原版 NVIDIA PTX 同样是 FP16 累加）。
   - **裁决**：自即日起，**以 `Phase 14 selected` 的三档输出哈希（720p/900p/1080p）作为新的严格 `0 bit-diff` 黄金基准**，不再拿早期的经验值 `45 dB` 阻塞性能优化主线。

---

## 2. `Phase 14 selected` 1080p (`1920×1152`) 耗时账本与五大剩余金矿

当前 1080p 独立插桩核累计 **`28.646 ms`**（端到端 GPU median **`31.826 ms`**），按板块拆解如下：

| 板块 | 核心与 1080p 耗时 (`ms`) | 合计耗时 | 占比 | 当前资源状态与暴露的物理瓶颈 |
| :--- | :--- | :---: | :---: | :--- |
| **1. 外围 `C32` 六核** | `post_b8` (`4.65`)、`prefix_b8d` (`4.54`)、`up_b8` (`1.21`)、`finish_dcrop` (`1.09`)、`mapped_b8` (`1.07`)、`finish_b8` (`1.06`) | **`13.612 ms`** | **47.5%** | 5 个非 Up 核为 `162~168 regs / 8 KB / OccW 11`，`up` 为 `168 regs / 10 KB / OccW 9`。**核心浪费**：① 每个 CTA 在 4 个 `qt` 循环内动态执行 80~104 次 `__sm86_unpack_fp8` 解包同一份仅 `36 KB` 的只读权重（全网每帧约 **2 亿条 warp 解包指令**）；② Site 0 (`Prefix` `pre`)、Site 3 (`V` `part==2`)、Site 6 (`mapped/up` 输出) 仍在走 `f16 -> f32 -> 标量 FP8` 绕路；③ FFN 激活占 40% 周期，仍在跑 FP32 标量多项式。 |
| **2. 中层 `Wave2` 九核** | `c64_wave2` ×4 (`3.36`)、`c128_wave2` ×3 (`2.40`)、`c256_wave2` ×2 (`2.44`) | **`8.192 ms`** | **28.6%** | ① **`c256_wave2` 被 `phase10_transform.py` 漏加寄存器上限**，仍卡在 **`226 regs / 48 KB / OccW 8`**（每 SM 仅 1 个 CTA），而 48 KB Shared Memory 本可容纳 2 个 CTA（`OccW = 16`）或 12 warps；② Stage 1 (`contract`)、Stage 2 (`result`)、Stage 3 (`V`)、Stage 4 (`av`)、Stage 5 (`ByteOut`) 产出的 `sm86_u4` 仍在先 `sm86_unpack_acc` 转 8 个 `float` 再调 8 次标量 `sm86_f32_to_e4m3_byte`；③ `plane_k[64*C]` 占了 1/3 Shared Memory，限制了 `C64/C256` 占用率。 |
| **3. 谷底 `ViT` 与 `C512`** | `vit_stream_qkv` (`1.39`)、`vit_stream_contract` (`1.21`)、`vit_attention_640` (`1.18`)、`vit_expand_w16` (`1.13`)、`c512_qkv_attn` (`0.45`)、`vit_stream_project` (`0.35`)、`split_ffn` (`0.31`)、`split_proj` (`0.17`) | **`6.191 ms`** | **21.6%** | **重大漏网之鱼**：`vit_expand_blocked_body_w16` (`1.13 ms`)、`vit_stream_contract` (`1.21 ms`)、`vit_stream_project` (`0.35 ms`) 和 `vit_stream_qkv` (`1.39 ms`) 的 Epilogue 全部在执行 **每个线程 16~32 条跨大步长（stride 1024B/4096B）的单字节 `st.global.u8` 散写**！源码中明明已有 `VIT_EXPAND_TAIL_VEC` 和 `VIT_QKV_TAIL_VEC`（利用 1 KB Shared Memory 片上转置后执行 16B `b128` 向量化合并写），却在 `build-modules.ps1` 中未开启或未覆盖到 `w5f8 / contract / project`！ |
| **4. 其余辅助核** | `mh_attention_project` (`0.18`)、`mh_pool_project` ×5 (`0.31`)、`decoder_project2x` (`0.13`)、`vit_gather` (`0.02`) | **`0.651 ms`** | **2.3%** | 已高度精简（`33~120 regs`，`OccW = 16~48`）。 |

---

## 3. 下一阶段深度优化路线图（Phase 16 ~ Phase 19，按确定性收益排序）

### Phase 16：ViT 四大核心 Epilogue 16B 向量化合并写（`TAIL_VEC` 全覆盖）+ `vit_stream_qkv` 访存瘦身（严格 `0 bit-diff`）
- **物理机制与源码证据**：
  1. 在 [`hip/deep_fast.hip`](hip/deep_fast.hip) 第 711~718 行中，`vit_expand_blocked_body_w16`（1080p 耗时 `1.132 ms`，`2,560` 个 block）默认走 `#else` 分支：每个 lane 发出 32 条跨 4096 字节步长的单字节 `st.global.u8` 散写，导致 L1/L2 写事务严重分裂。而第 711 行的 `#if VIT_EXPAND_TAIL_VEC` 利用 `1024 B` Shared Memory `t8[1024]` 将 `16×64` 字节在片上排成连续行，每个 lane 仅发出 **2 条 16 字节对齐的 `st.global.v4.u32` (`b128`) 合并写**，且 `vit_expand` 当前 `Shared = 0 B, Regs = 80, OccW = 16`，加 `1024 B` Shared 后 `OccW` 保持 `16` 不变！
  2. 同理，在 [`hip/deep_fast.hip`](hip/deep_fast.hip) 第 794 行的 `vit_contract_blocked_body`（`vit_stream_contract_frag_bstream_bout`，耗时 `1.207 ms`，已自带 4096 B `occ_pad` Shared Memory）和 [`hip/vit_stream.inc`](hip/vit_stream.inc) 第 66 行的 `vit_stream_project_tiles`（`vit_stream_project_n64_bb_bout`，耗时 `0.352 ms`）中，Epilogue 同样是每个 lane 发出 32 条跨 1024 字节步长的 `st.global.u8` 散写！直接复用/引入 `1024 B` Shared Memory `t8[1024]` 做与 `VIT_EXPAND_TAIL_VEC` 完全同构的 `16×64` 片上转置 + 2 条 `b128` 向量化合并写出。
  3. 在 [`hip/vit_stream.inc`](hip/vit_stream.inc) 第 212 行的 `vit_stream_qkv_frag_bin_w5f8`（耗时 `1.389 ms`）中，Epilogue 同样是 16 条跨 1024 字节步长的 `st.global.u8` 散写，而第 153 行现成写好了 `VIT_QKV_TAIL_VEC`（复用已死掉的 `raw` Shared Memory tile 做 `16×32` 转置 + 单条 `b128` 16B 合并写），只需把 `VIT_QKV_TAIL_VEC` 逻辑同步应用到 `vit_stream_qkv_frag_bin_w5f8` 的第 249~260 行！
  4. 额外检查 `vit_stream_qkv_frag_bin_w5f8` 的 LDS 权重搬运：目前 `F8_STASH` 把 8B FP8 权重解包成 16B `sm86_u4` 写入 LDS（`sts.128` + 计算 warp `lds.128`），可对比测试“直接将 8B 预洗牌 `i2` 存入 LDS（`sts.64` + `lds.64`，LDS 带宽减半），计算 warp 读出后寄存器内 `__sm86_unpack_fp8`”是否进一步降低 `vit_stream_qkv` 延迟。
- **验收标准**：
  - 720p / 900p / 1080p 三档相对 `Phase 14 selected` 输出 **严格 `0 bit-diff`**，`32/32` 活跃核 `LMem = 0 B`；
  - 检查四个 ViT 核的静态 PTX `st.global.u8` 归零（转为 `st.global.v4.u32`），并在同轮 50/80 下测量四个 ViT 核的插桩耗时与整帧 median 收益。

### Phase 17：C32 静态权重离线预解码为 FP16（消灭每帧 2 亿条动态 `__sm86_unpack_fp8` 指令，严格 `0 bit-diff`）
- **物理机制**：
  - 六个 C32 核占全网 47.5% 时间（`13.61 ms`），在 1080p 下共启动 `104,450` 个单 Warp CTA。每个 CTA 在 4 个 `qt` 循环中对只读权重调用 80~104 次 `__sm86_unpack_fp8`（每次 4 条 `prmt` + 12 条位运算 + 4 条 `mul.rn.f16x2` = 20 条指令），全网每帧重复执行约 **2 亿条 warp 解包指令**。
  - 而 6 个 C32 核的矩阵权重总计仅约 **0.39 MiB（FP8）**，离线精确解包为 FP16 后仅约 **0.78 MiB**（单个核仅 `~72 KB`），100% 常驻 RTX 3080 Laptop 的 **4 MB L2 Cache**。
- **实施方案**：
  1. 在 Host 权重打包层（`packed_weights.h`）为 C32 的 `W16` 矩阵权重（FFN expand/contract、Chain diag、QKV、Attention Out）生成离线解包好的 Ampere `sm86_u4` (`FP16x2`) 权重块（配对 `AMPERE_WEIGHTS_V3` 标记）；
  2. 在 `wave_owned_c32.inc` / 构建转换中，C32 权重读取直接通过 `ld.global.nc.v4.u32`（`__ldg` / 只读缓存路径）加载 `sm86_u4` 送入 `sm86_mma_prepared_core`，彻底省去运行期 `__sm86_unpack_fp8` 的 20 条指令/MMA；
  3. 严格控制寄存器生命周期（确保 `sm86_u4` 权重在紧邻 MMA 前加载、用完即死，不跨 `hp/ci` 囤积导致 spill）。
- **验收标准**：
  - 三档相对 `Phase 14 selected` 输出 **严格 `0 bit-diff`**，`32/32` 活跃核 `LMem = 0 B`，同轮 ABBA 50/80 验证 C32 六核与端到端耗时下降。

### Phase 18：`c256_wave2` 占用率破局（`226 regs / OccW 8` -> `OccW 12~16`）与 Wave2/C32 全站 `half2 -> FP8` 直通打包
- **物理机制**：
  1. **修复 `c256_wave2` 漏加 Cap 与寄存器峰值**：`phase10_transform.py` 中 `c64_wave2` 和 `c128_wave2` 均已压至 `168 regs / OccW 12`，唯独漏掉了 `c256_wave2_bi_bo_w16` 与 `c256_wave2_bi_w16`（1080p 合计 `2.44 ms`，仍卡在 `226 regs / OccW 8`）。此外检查 `c256_wave2` 是否可通过开启 `W2_QKV_FUSE` (bit3 `W2QkvPair=8`) 或将 `plane_k` 优化为按需计算/复用，使每个 SM 驻留从 8 warps 提升至 12~16 warps。
  2. **Wave2 与 C32 剩余纯累加器站点的 `sm86_pack_ad_producer` 直通（严格 `0 bit-diff`）**：
     - 目前 Wave2 的 Stage 1 (`contract`)、Stage 2 (`result`)、Stage 3 (`V` = `q[2][ci]`)、Stage 4 (`av`)、Stage 5 (`ByteOut`) 以及 C32 的 Site 0 (`Prefix` `pre`)、Site 3 (`V` `part==2`)，其源数据本身就是 `.f16.f16.f16.f16` MMA 产出的 `sm86_u4`（精确 half 值），在 `FAST_NUM=3` 下却先调 `sm86_unpack_acc` 转成 8 个 `float`，再调 8 次标量 `sm86_f32_to_e4m3_byte`。
     - 将这些站点统一替换为已通过 65,536×256 穷举验证的 `sm86_pack_ad_producer<true/false>`（`f16x2 -> E4M3` 硬件向量化打包），既砍掉大量 `cvt.f32.f16` 与标量打包指令，又显著降低 Wave2 的寄存器压力（直接助力 `c256_wave2` 压低寄存器！）。

### Phase 19（可选探索）：C32 / Wave2 FFN 激活函数 `f16x2` 向量化（`CW_FAST_NUM&4`）与《鬼武者》/《剑星》实机 Runtime 同步更新
- **物理机制**：
  1. Phase 13 动态采样证实 C32 的 `FFN expand -> 激活 -> contract` 占每个 `qt` 周期的 40%。`wave_owned_c32.inc` 第 356 行已有现成的 `#if CW_FAST_NUM&4`（用 `min.f16x2 / max.f16x2 / fma.rn.f16x2 / mul.rn.f16x2` 替代 8 路 FP32 标量多项式），配合 `sm86_pack_half_h8_e4m3` 可直接从 `sm86_u4` 算完激活并一步打包成 E4M3，全程不进 FP32 寄存器。单独实测其对三档速度与 PSNR 的影响（若 PSNR 几乎无损且提速显著则纳入 `FAST_NUMERIC` 选项）。
  2. 将通过全部验证的最新 `hip-port` 内核与 `LmxxfNrRuntime.dll`（含 Phase 14 修复的 `<=256 token` ViT attention 正确性补丁与 Phase 16~18 性能成果）重新交叉编译并同步部署至《鬼武者：剑之道》实机目录。

---

## 4. 历史阶段实测归档（Phase 1 ~ Phase 15B 速查）

- **Phase 1（2026-10-25）**：实现两条 `.f16.f16.f16.f16` MMA + `sm86_u4` 累加器及 SSA 抵消，900p `45.44 ms` / 1080p `63.26 ms`。
- **Phase 2（2026-10-25）**：CPU 静态权重 Ampere 预洗牌 + `ones` 专用求和 + packed 分段累加，恢复 32/32 零 `LMem`，900p `42.26 ms` / 1080p `54.48 ms`。
- **Phase 3 ~ 4（2026-10-25）**：启用 900p compact/C256 门控 + ViT `packed_total` 循环前初始化 + Stage 3 `qt` 滚动 + C64/C128 W16，900p `39.44 ms` / 1080p `52.85 ms`。
- **Phase 5（2026-10-25）**：4-u32 C/D Benes 向量化洗牌 + 受约束寄存器 Q（5 个非 Up C32 核 8KB / OccW 11），900p `36.67 ms` / 1080p `49.35 ms`。
- **Phase 6（2026-10-25）**：LLVM IR 16B 对齐升级（清除热核 scalar `u8` 读写，转为 native `v2/v4`），900p **`27.69 ms`** / 1080p **`36.89 ms`**（提速 `1.33×`）。
- **Phase 7 ~ 9（2026-10-25）**：无分支 FP8 转换与常量裁剪 + 2-shfl D→AB 直通 + V 直通 + 5 个非 Up C32 核全部 8KB/OccW 11/零 LMem + CUDA Graph 实测验证，900p `26.61 ms` / 1080p `35.32 ms`。
- **Phase 10（2026-10-25）**：9 核 `.maxnreg` 上限 + FP8 内部单次 448 饱和，三档首次全面反超原版 PTX：720p **`14.10 ms`**、900p **`23.75 ms`**、1080p **`31.63 ms`**；完成《鬼武者》实机部署并排除 `AmdBridge::IsAmd` 厂商锁与 `_storage_` 残留。
- **Phase 11 ~ 12（2026-10-25）**：C32 FFN feature (Site 2) 与 AV (Site 5) 直接 `half2 -> E4M3` 打包，65,536×256 全位模式 0 bit-diff。
- **Phase 13 ~ 14（2026-10-25）**：定位并修复 `vit_attention_fused_256` 中通用预洗牌对 legacy attention 造成二次洗牌的 Bug，建立正确的 720p F32 Gold，默认切换 `<=256 token` 至等价且更快的 `400` 桶（**`Phase 14 selected`**：720p **`14.15 ms`** / 900p **`23.72 ms`** / 1080p **`31.83 ms`**）。
- **Phase 15 ~ 15B（2026-10-26）**：建立 56 配置 × 7 几何动态回归套件（[`hip-port/phase15/README.md`](hip-port/phase15/README.md)），并通过逐层 NRMSE 与 CPU K8-FP16-RNE 逐位核验（[`hip-port/phase15/DIAGNOSTIC15B.md`](hip-port/phase15/DIAGNOSTIC15B.md)）证实 `43.44 ~ 43.58 dB` 为 FP16 累加的正常物理精度边界，正式结案并进入 Phase 16。


## 2026-10-26：Phase16，ViT四核16B尾写全覆盖（闇）

按815d096新裁决，以Phase14 selected三档输出作严格0bit基线，恢复性能线。三个CUDA模块开启EXPAND/QKV/CONTRACT/PROJECT TAIL_VEC；expand沿用1KB转置，contract复用4096B occ_pad，project新增1KB，QKV复用dead raw norm tile。实际compactw_w16入口PTX单字节global写32/32/32/16→0/0/0/0，v4.u32与SASS STG.128均为2/2/2/1；Regs分别80→85、106→102、101→103、119不变，OccW16/16/16/15不变。未做可选FP8 LDS子实验。

仅3模块重编、37按SHA复用，40/40实际CUDA加载1918entry；最终源码重编SHA与实测集合全部相同。三档各两组ABBA、50warmup/80iter，共24次正式运行均相对Phase14完整输出0bit、invalid0、first-last0、32/32 LMem0。18项既有Python/LLVM及1项尾部还原顺序回归通过。首版contract被旧Phase2 pass把packed_total还原放到标量fallback，快验拦截，修复后再进入正式计时；失败日志保留。

GPU median按A1/B1/B2/A2，单位ms：首组720为14.102/14.087/14.083/14.146，900为23.628/24.193/23.712/24.309，1080为32.091/31.915/32.402/32.326；确认组720为14.173/14.444/14.432/14.899，900为25.241/24.444/24.437/24.518，1080为32.538/32.606/32.463/32.592。两次median均值比较小幅正向，但默认DVFS/基线抖动与收益同量级，不宣称稳定百分比；第二组900不拿0.439ms作因果收益。四核独立插桩数据与整帧min/median/Wall/PROFILE_TOTAL逐轮完整保留，不能按静态写指令削减推算加速。

按任务要求保留四处默认开启，数值/资源/向量化目标达成，整帧收益很小。详见[Phase16报告](hip-port/phase16/README.md)、[两组ABBA与四核](hip-port/phase16/summary.md)、[32核完整表](hip-port/phase16/results.md)、[验收](hip-port/phase16/validation.json)。最终40模块在phase16/artifacts/tail/modules；临时LLVM/失败输出已清理，正确输出按SHA去重，保留日志/遥测/SHA/生成源。未改共享assets、游戏/Magpie、PTX或发布ZIP，不push；本阶段独立commit，下一阶段Phase17未启动。
