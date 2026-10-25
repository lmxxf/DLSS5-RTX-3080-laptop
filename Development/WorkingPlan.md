# DLSS 5 (`310.9.16.0` 31-Block Small) — RTX 30 系 (`sm_86`) 独立引擎 (`hip-port`) 深度优化工作计划

> **⚠️ 工程与 Git 提交铁律（必读）**：
> 1. **阶段即提交**：每完成一个功能修改或一个优化阶段（Phase）并通过实测验证、更新 `DevHistory.md` 后，**必须立即执行一次 `git commit`（严禁添加 `Co-Authored-By` 尾巴）**，绝不允许跨多个阶段不提交。
> 2. **保持仓库轻量纯净**：提交前必须确保 `.gitignore` 生效且清理掉实验目录下的临时大二进制产物（如 `artifacts/`、`*.rgb32`、`*.hsaco`、`*.cubin`、`*.ptx`、`benchmark_cuda_nn` 可执行文件等），只提交源码、构建脚本与 Markdown/JSON 实验报告。

## 1. 战略定位与双路线基线

- **当前已发布基线（`v0.1.0` 主推路线，`Development/ptx-patcher/`）**：
  - 直接改写原版 `310.9.16.0` `nvngx_dlssnr.dll` 内置的 15 个 Fatbin PTX（两条 IEEE 754 `f16x2` 硬件算术恒等式 + 花括号向量加载多定义 `mapped` 过滤），实现 **15/15 满血 `O4` 原槽位装入 + 0 天空色带**。
  - RTX 3080 Laptop (`sm_86`, 132W) 实测耗时（`Preset 2` 31 块新模型）：
    - `1280×720` (720p)：**`15.83 ms`**
    - `1600×900` (900p)：**`24.47 ms`**
    - `1920×1080` (1080p)：**`32.04 ms`**
  - 结论：`ptx-patcher` 在原版 DLL 骨架下已达物理天花板，作为 `v0.1.0` 稳定基线与性能标尺。

- **下一阶段主攻方向（独立 CUDA 引擎路线，`Development/hip-port/`）**：
  - 当前 `hip-port`（V5/V6，32/32 活跃核 `LMem = 0 B` + 激活预洗牌）在同机同模型下的耗时为：
    - `1280×720` (720p)：**`~31.0 ms`**
    - `1600×900` (900p)：**`43.10 ms`**
    - `1920×1080` (1080p)：**`57.13 ms`**（32 核累计 `61.28 ms`）
  - **为什么重写独立引擎非常有价值**：
    `ptx-patcher` 受限于闭源宿主 DLL，无法修改 190 次 Kernel Launch 结构、无法改变核间显存张量布局、也无法跨核融合。而 `hip-port` 拥有 100% 源码控制权——只要我们先在算子底层解开 GeForce 30 系的硬件限速与跨架构洗牌包袱，就能在此基础上进一步做跨核融合、静态权重重排与 CUDA Graph 固化。

---

## 2. `hip-port` 当前耗时账本与瓶颈剖析（`0.5x Small` 31 块模型，1080p 累计 `61.28 ms`）

根据 `DevHistory.md` 4.3 节的 32 核普查表，耗时高度集中在以下三大板块（占全网 **92.3%**）：

| 板块 | 包含核函数（31 块 `0.5x Small`） | 1080p 累计耗时 | 占比 | 核心物理瓶颈 |
| :--- | :--- | :---: | :---: | :--- |
| **A. 外围 `C32` 站** | `c32_wave1_prefix` (`8.37 ms`)、`c32_wave1_post` (`7.41 ms`)、`up` (`2.04 ms`)、`finish_dcrop` (`1.98 ms`)、`mapped` (`1.88 ms`)、`finish` (`1.80 ms`) | **`23.49 ms`** | **38.3%** | ① 使用半速 `.f32.f16.f16.f32` 指令；② 权重每次进 WMMA 仍在运行期执行 `__sm86_prep_fp8`（4 条 `shfl.sync`）；③ 每块仅 1 Warp (`Block=32`)，寄存器 `168~234` 限制 `OccW = 8~9` |
| **B. 中层 `C64~C256` 站** | `c256_wave2` ×2 (`4.83 ms`)、`c128_wave2` ×3 (`5.70 ms`)、`c64_wave2` ×4 (`7.64 ms`) | **`18.17 ms`** | **29.6%** | ① 半速 FP32 累加；② FP32 累加器 (`f8`) 占双倍寄存器，导致全系 `Regs = 240~248`、`OccW = 8`；③ 权重运行期 `shfl.sync` 及 Stage 间 C/D 布局洗牌 |
| **C. 谷底 `ViT C1024` 与 `C512` 站** | `vit_stream_qkv` (`4.24 ms`)、`vit_stream_contract` (`3.93 ms`)、`vit_expand` (`3.19 ms`)、`vit_attention` (`2.07 ms`)、`vit_stream_project` (`1.50 ms`)、`c512_qkv_attn` (`1.13 ms`)、`split_ffn` (`0.90 ms`) | **`16.96 ms`** | **27.7%** | 纯 Tensor Core 矩阵乘密集型（K=512/1024/4096），直接受制于 GeForce 30 系 `.f32` 累加吞吐量砍半（256 vs 512 FLOPs/clk/SM） |
| **D. 其余辅助核** | `mh_attention_project`、`split_projection`、`decoder_project2x`、`mh_pool_project`、`vit_gather` | **`2.66 ms`** | **4.4%** | 占比小，受访存与启动开销影响 |

---

## 3. 分阶段优化路线图（小步快跑、每步实测耗时与 PSNR）

### Phase 1：解锁 GeForce 30 系满速 Tensor Core —— `.f16.f16.f16.f16` 半精度累加与 4-shfl 累加器洗牌
- **物理机制**：
  - 在 GA102/GA104（RTX 3080/3090）消费级核心上，`mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32` 被硬件限制为 **Half Rate（256 FLOPs/clock/SM）**，而 **`mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16` 为 Full Rate（512 FLOPs/clock/SM，吞吐量翻倍）**；
  - 原版 `nvngx_dlssnr.dll` 的 PTX 本身采用的就是 FP16 累加（`.f16.e4m3.e4m3.f16`），因此切换为 `.f16.f16.f16.f16` 完全符合原版模型的数值设计；
  - 同时，16×16 累加片段从 8 个 32 位寄存器（`sm86_f8`）缩减为 **4 个 32 位寄存器（`sm86_u4`，即 4 个 `f16x2`）**，跨 K 循环的寄存器压力减半，且 C/D 布局转换只需搬运 4 个 `u32`（`shfl.sync` 次数从 8 条直接减半为 **4 条**）。
- **实施方案**：
  1. 在 `hip/sm86_compat.h` 与 `hip/build_sm86_modules.py` 中引入满速 `.f16.f16.f16.f16` 核心路径：
     - 将 K 循环内部的累加器保持为 Ampere 原生布局的 `sm86_u4`（4 个 `f16x2`）或通过升级版 SSA Pass (`cancel_wmma_shuffles_ir`) 自动把连续 WMMA 累加降级为 `f16x2` 累加；
     - 对于单次或循环边界的 C/D 转换，利用 `cvt.rn.f16x2.f32` / `cvt.f32.f16` 与 4-shfl Benes 网络（因为每两个相邻元素打包在一个 `u32` 中，仅需 4 条 `shfl.sync` 即可完成 RDNA4↔Ampere 转换！）。
  2. 验证判据：
     - 跑 `wmma_validate_cuda` 与 31 块 `0.5x Small` 端到端测试（`900p` 与 `1080p`），确保 `invalid (NaN/Inf) = 0`，输出画面与 `f32` 基准的 PSNR $\ge 45\text{ dB}$（或与原版 PTX 高度一致）；
     - 对比 32 核寄存器占用（预期 `c64/c128/c256_wave2` 寄存器显著下降、`OccW` 提升）与端到端毫秒数。

### Phase 2：静态权重预重排（Weight Pre-Swizzle）—— 彻底消灭权重运行期 `shfl.sync`
- **物理机制**：
  - 目前激活张量已实现 8B 预洗牌（`sm86_preshuffle_fp8`），但大部分核函数从显存读取**静态模型权重**后，每次调用 WMMA 仍在运行期执行 `__sm86_prep_fp8(w)`（每次消耗 4 条 `shfl.sync` + 6 条 `selp`）。
  - 模型权重在初始化加载后是完全只读的！在 `c32_wave1`（1080p 下 `34,560` 个窗口）等高频核中，同一份权重被重复洗牌了数万次。
- **实施方案**：
  1. 梳理 `c32_wave1`、`c64/c128/c256_wave2`、`c512` 与 `vit_*` 中权重张量的加载方式（如 `w16` 16 字节向量加载或 `i2` 8 字节加载）；
  2. 在权重加载入显存时（或通过一次性初始化预处理 Kernel），直接按 Ampere `m16n8k16` 的 lane 映射关系将权重字节预重排（Pre-swizzle）；
  3. 内核运行期读取权重后直接调用零洗牌的 `sm86_unpack_e4m3x8`（仅 4 条 `prmt` + 4 条 `mul.rn.f16x2 0x5c005c00`）送入 `mma.sync`，实现 **全网 WMMA 内部 0 次 `shfl.sync`**。

### Phase 3：`c32_wave1` 与 `wave2` 占用率突破 + 核内 Shared Memory 原生 Ampere 布局
- **物理机制**：
  - `c32_wave1` 占全网近 40% 时间，其 `Block=32`（单 Warp CTA）且每个线程块占 `10,240 B` Shared Memory，导致每个 SM 最多只能跑 9 个 Warp（`101,376 / 10,240 = 9`，占用率仅 `18.7%`）；
  - `c64/c128/c256_wave2` 中 Stage 1~5 通过 Shared Memory (`plane0`, `plane1`) 交换中间结果时，仍在写入前转回 RDNA4 布局（`__sm86_d_to_rdna4`），读取时再转 Ampere。
- **实施方案**：
  1. 压缩 `c32_wave1` 的 Shared Memory 峰值复用（如从 `10,240 B` 压至 `6,144 B` 或 `8,192 B`）或支持 2-Warp CTA，将每 SM 活跃 Warp 数从 `9` 提升至 `12~16`；
  2. 将 `wave2` 与 `c32_wave1` 的 Epilogue / Stage 间写出直接对齐到 Ampere 布局或用硬件 `f16x2 + 2.0h` 向量化打包替代逐标量 `sm86_f32_to_e4m3_byte`。

### Phase 4：Host 端 CUDA Graph 固化与 D3D12 桥接精简
- **实施方案**：
  - 在 `src/native_hip_network.h` 中，当分辨率与模型档位（`0.5x Small`）固定时，使用 `cuStreamBeginCapture` / `cuGraphInstantiate` / `cuGraphLaunch` 将整帧 31 块的 Kernel 发射序列固化为单个 CUDA Graph，消除近百次 Driver API 启动开销。

---

## 4. 协作与验证纪律

1. **分工**：朱雀（鳩）负责架构设计、瓶颈算账、阶段规划与对外文档；闇（Codex）负责底层核函数改写、编译构建、单元校验与实机 Benchmark。
2. **铁律**：
   - 任何优化必须先过数值校验（`invalid = 0`，PSNR / 图像哈希对照），严禁拿算错画面的速度充数；
   - 每次测量必须在相同功耗/频率稳态下记录 `Min / Median ms` 及 32 核分解表，并将实验结果（无论正负）如实记入 `Development/DevHistory.md`。

## 5. Phase 1 首轮实测状态（2026-10-25，闇）

- 已实现两条 FP16 MMA + `sm86_u4` 核心及 packed SSA/PHI 抵消，40/40 模块构建、1898 entry 加载通过；63 组 K16/K32 映射验证通过。
- Small 31-block 整网 invalid=0；900p/1080p 可见区域 PSNR 46.62/46.19 dB，通过 45 dB 门槛。
- 最终 50 warmup / 80 iterations GPU median：F32 46.190/63.342 ms，候选 45.444/63.264 ms；没有明确端到端性能突破。1080p 21/32 核寄存器下降，但 pool 三核 OccW 16→8、另一核新增 104 B LMem。
- **Phase 1 尚未完成**：边界仍为旧 8-shfl，外围 K32/partition 求和仍保留原 F32/RTZ 语义；下一步先消除 packed/legacy 辅助路径的冗余转换并处理 pool 回退，再评估 packed half add 与 4-shfl 布局方案。不能将核心指令标称吞吐翻倍直接写成整网速度翻倍。
- 完整对照：[hip-port/phase1/results.md](hip-port/phase1/results.md)；实现与复测说明：[hip-port/phase1/README.md](hip-port/phase1/README.md)。稳定 assets 与 v0.1.0 发布包未替换。

## 6. Phase 2 三项组合完成与实测（2026-10-25，闇）

- 静态 FP8 权重 CPU Ampere 预洗牌、ones 专用求和、pool/ViT/decoder packed 分段累加已实现；40/40 模块和新 benchmark runner 构建通过，1898 entry 加载验证通过。
- 基础测试的权重置换、ones 四次累加、packed add 均0 bit-diff；ones精确性依赖保留K8舍入。通用RDNA4 `ones_b` 的精确实现是16次广播，不能按1条shuffle估算收益。
- 同轮50 warmup/80 iterations：Phase1→Phase2 GPU median，900p **44.872→42.264 ms（1.0617×）**，1080p **59.806→54.476 ms（1.0978×）**；invalid=0，对F32可见区域PSNR **46.6206/46.1009 dB**。
- pool恢复111regs、三个核OccW8→16，消除104B LMem，活跃核恢复32/32（900p34/34）零LMem。wave2的250regs、contract的217regs/OccW8仍是明确剩余问题；边界4-shfl尚未实现，不宣称当前全网0-shuffle。
- 详见 [phase2完整核表](hip-port/phase2/results.md) 与 [实验/复测说明](hip-port/phase2/README.md)。生产assets与v0.1.0发布包仍未覆盖。

## 7. Phase 3 实测状态（2026-10-25，闇）

- 三项已实现，40/40模块、1898 entry加载通过；SSA/GPU基础验证通过；Q移动到消费循环对共享Q控制在两档均0 bit-diff。
- 延后解包按建议实现，但wave2仍250regs、contract仍217regs，部分关键核机器码与Phase2相同，未得到预计的寄存器收益。
- 900p compact/inter-byte与C256门控放开；C256独立控制更快且逐位一致，保留。共享Q+新门控的900p median **41.009ms**，同轮Phase2 **41.929ms**。
- local-Q确实把SMem降至8192B，五个C32核OccW升至11；up仍受225regs限制为8。但完整Phase3 median为900p **41.879ms**、1080p **55.420ms**，不优于共享Q控制 **41.009/54.370ms**。
- 两档invalid=0，PSNR **46.9753/46.1009dB**，32/32零LMem。**不把占用率指标当作速度；当前保留900p门控收益，8KB local-Q仍是实验候选。** 稳定运行时未覆盖。
- [Phase3完整说明](hip-port/phase3/README.md)与[32核对照表](hip-port/phase3/results.md)。

## 8. Phase 4 当前最优基线（2026-10-25，闇）

- 基于共享Q+900p新门控，保留ViT packed_total循环前初始化、Stage3 qt滚动、C64/C128 W16/双qt复用（两个mask=3）。C32源码恢复共享Q默认。
- contract **217→150regs**、project **210→155regs**，OccW8→12；wave2仍250regs/OccW8，168以内目标未达。qt代码体积减约26~27%；显式kt滚动与qt-only SASS相同，未保留。
- 最终50/80同轮：900p **min38.763 / median39.442ms**（基线40.793med）；1080p **min52.252 / median52.845ms**（基线54.126med）。两档对所选基线0bit-diff、invalid=0、32/32零LMem；PSNR保持46.9753/46.1009dB。
- 40/40模块、1918 entry加载通过。当前候选：[Phase4 selected](hip-port/phase4/README.md)，[完整核表](hip-port/phase4/results.md)。实际游戏/共享assets/正式发布包尚未覆盖。

## 9. Phase 5 当前最优基线（2026-10-25，闇）

- 保留4-u32 C/D Benes：half全位模式逐位置与随机16777216个FP32值0bit-diff；WMMA63组通过。实际helper selp48→17、增加4prmt、shfl仍8。
- prefix单独向量化自动169→168regs、OccW8→9。裸寄存器Q虽8KB却涨到178～216regs/OccW8；最终采用非up寄存器Q＋ `(32,9)`，五核167～168regs/OccW11，up保留234regs/10KB/OccW8。
- 仅在已测c32-wave1-fast默认开启mask63与minblocks9，其他C32模式保持共享Q。相同约束的共享Q控制已补齐；额外Q收益小、默认DVFS未锁频，不夸大因果比例。
- 最终50/80：900p **min36.095 / median36.671ms**（同轮Phase4基线39.105med）；1080p **min48.893 / median49.346ms**（基线52.571med）。向量化独立方案1080p min48.513，不能与组合median混拼。
- 两档基线0bit-diff、invalid0、32/32零LMem，PSNR保持46.9753/46.1009dB。最终40模块哈希与长测集合一致；当前默认[Phase5 selected](hip-port/phase5/README.md)，[完整核表](hip-port/phase5/results.md)。外部运行时未覆盖。

## 10. Phase 6 当前推荐基线（2026-10-25，闇）

- IR对齐升级已接在SSA末尾与O3后/llc前；40/40模块、1918 entry加载通过。C64/C128/C256主用W16核的四类scalar u8读写清零，转native v2/v4。
- 默认16B无地址错误、两档0bit-diff；原始方案prefix出现32B local，最终只关闭prefix寄存器Q（fast mask31），以不足0.1ms差换回32/32零LMem。其它非up四核仍8KB/OccW11，prefix10KB/152regs/OccW9，up保持原样。
- 默认50/80：900p **min27.315 / median27.685ms**（同轮Phase5 36.671med）；1080p **min36.538 / median36.891ms**（基线49.394med）。速度比1.3246×/1.3389×；invalid0、基线0bit-diff、PSNR不变。
- ViT contract/project106/101regs、OccW16；wave2仍242～250regs/OccW8，未加新的强制bounds。900p达到20～30ms，1080p尚未达30ms；C32约占核累计一半。
- [Phase6说明](hip-port/phase6/README.md)、[32核表](hip-port/phase6/results.md)、[40模块PTX统计](hip-port/phase6/ptx-counts.md)。当前推荐 `phase6/artifacts/selected/modules/`；原始带32B local的更低延迟控制仍保留。外部运行时未覆盖。

## 11. Phase 7 默认：无分支FP8与常量裁剪（2026-10-25，闇）

- 保留1+2；GPU原语4262720样本0bit-diff，40/40模块、1918entry加载通过。prefix静态PTX bra617→10、min/max528/530→288/290，MMA仍84。不能按PTX条数推算动态SASS或帧提速。
- 第一轮50/80：900p **min27.344 / median27.636ms**（同轮基线27.908med），1080p **min36.371 / median36.722ms**（基线36.946med）。反向复测27.564/36.599med，后跑基线28.173/37.330med；只属小幅收益，默认DVFS未锁频。
- 全部对Phase6输出0bit-diff、invalid0、32/32零LMem；PSNR46.9753/46.1009dB不变。C512QKV151regs/OccW12有收益，但splitFFN186regs/OccW8、ViTproject138regs/OccW12有回退，后续应按核检查而非盲目推广单一asm。
- 跨h2预解包控制0bit、零LMem，但median27.788/36.904ms更慢，**不进默认**。当前推荐 `phase7/artifacts/selected/modules/`（step12第一轮测量别名）。[说明](hip-port/phase7/README.md)、[32核表](hip-port/phase7/results.md)、[指令表](hip-port/phase7/ptx-counts.md)。外部运行时仍未覆盖。

## 12. Phase 8 当前默认：D→AB直通，零LMem（2026-10-25，闇）

- 2-shfl bridge GPU验证256/256位置及4194304个随机half量化值0bit-diff；C32 expand/AV、wave2 expand/contract/result/AV已接入。原始40/40模块、1918entry编译加载通过，最终修正3模块从默认源码重编，其余37复用。
- bounds单独造成spill；两敏感模块局部恢复旧FP8表达式并保留bounds，splitFFN **106regs/OccW16/LMem0**、ViTproject **101/16/0**。C32mapped共享Q（fast mask29）换回零spill，146regs/10KB/OccW9，其余目标布局优化保留。
- 最终独立50/80：900p **min26.486 / median26.837ms**，1080p **min35.237 / median35.790ms**；核累计25.025536/33.181696ms。最后配对Phase7 median27.382/36.354ms，约2.03%/1.58%提速。默认DVFS未锁频，静态shuffle削减不等同帧提速。
- 两档对Phase7/6 0bit-diff、invalid0、32/32活跃核LMem0、PSNR不变。更快带8B local控制单列保留，默认不采用。当前推荐 `phase8/artifacts/selected/modules/`；[说明](hip-port/phase8/README.md)、[32核表](hip-port/phase8/results.md)、[指令表](hip-port/phase8/ptx-counts.md)。外部运行时尚未覆盖。

## 13. Phase 9 当前默认：V直通+逐核FP8+全非Up register-Q（2026-10-25，闇）

- Graph已解锁Small/wave-owned/W16/direct路径，实测build1/replay130，动态输入与Raw/恢复均逐位一致；多个50/80对照没有明显提速，保持显式opt.graph/环境开关，默认未强开。
- V走2-shfl，Q/K不改；prefix/mapped/wave2静态shfl再减20，MMA不变。最终mapped局部低寄存器编码、其它C32无分支，Qmask63：**五个非Up C32均8KB/Occ11/LMem0**，整网32/32零LMem。qt3剥离更慢且仍spill，未保留。
- 最终50/80无Graph：900p **min26.265/median26.612ms**、1080p **min34.924/median35.318ms**；核累计24.837120/32.576256ms，Wall median26.722/35.407。Graph GPU median26.614/35.420，Wall26.727/35.555；同轮基线GPU median26.641/35.486。未达24/32，不能将独立插桩差额全算launch气泡。
- 两档0bit-diff、invalid0、PSNR不变；40模块/1918entry加载通过（原构建37成功，三个共享Q变体修复补编，最终C32再编）。当前推荐 `phase9/artifacts/selected/modules/`；[说明](hip-port/phase9/README.md)、[32核表](hip-port/phase9/results.md)、[指令表](hip-port/phase9/ptx-counts.md)。外部运行时未覆盖。

## 14. Phase 10 当前默认：9核上限＋单次FP8饱和（2026-10-25，闇）

- 9个目标入口maxnreg验证通过：C64/C128七核168regs/Occ12/LMem0，C512QKV128/Occ16/0，C32Up168/Occ9/0。五个非Up仍8KB/Occ11/0。仅caps整帧收益小，主要提速来自第二锤。
- FP8内部绝对值min448，删除p_sat/p_nan与冗余外夹断；保留调用点原signed-zero语义及残差夹断。4242851有限样本0bit，NaN差异另记。三个敏感低寄存器入口以短分支避免新spill，保留新饱和逻辑。
- 最终50/80、Graph off：900p **min23.461/median23.750ms**，1080p **min30.944/median31.631ms**；核累计21.753888/28.430336，Wall med23.850/31.712。与同轮Phase9 med26.361/35.028相比约9.9%/9.7%时间下降，未锁频。**两档median已低于24/32ms**，不是全部帧都低于预算。
- 两档0bit-diff、invalid0、32/32零LMem、PSNR不变。40模块/1918entry完整编译加载，修正3模块另编，当前默认两个Phase10开关均True。推荐 `phase10/artifacts/selected/modules/`；[说明](hip-port/phase10/README.md)、[32核表](hip-port/phase10/results.md)、[指令表](hip-port/phase10/ptx-counts.md)。外部运行时仍未覆盖。

### Phase 10 三档实测补齐（2026-10-25）

单位均为ms。CUDA均使用Phase10最终selected模块、0.5x Small31、Style1、Graph off、50 warmup/80 iter；720p本次补测，900p/1080p沿用上一轮最终独立复测，未混入其它控制轮次的min或核累计。PROFILE_TOTAL是单独插桩帧。PTX列为历史GPU median标尺，本轮未统一输入/处理尺寸重跑DLL，不计算严格同条件加速比。

| 档位（CUDA处理尺寸） | CUDA GPU min | CUDA GPU median | CUDA Wall median | CUDA PROFILE_TOTAL | invalid | PTX历史GPU median |
|---|---:|---:|---:|---:|---:|---:|
| 720p（1280×768） | 13.843 | **14.103** | 14.182 | 14.001120 | 0 | 15.83 |
| 900p（1600×1024） | 23.461 | **23.750** | 23.850 | 21.753888 | 0 | 24.47 |
| 1080p（1920×1152） | 30.944 | **31.631** | 31.712 | 28.430336 | 0 | 32.04 |

720p已补齐：首末帧0bit-diff、invalid0、32/32零LMem，与Phase5旧分散C256参考输出逐位一致。Host增加1280×768的C256 wave2门控解决旧分散核对齐错误，selected模块未改；900p/1080p沿用已归档最终轮次。详见[三档记录](hip-port/phase10/three-tier-results.md)。

### Phase 10 《鬼武者》独立CUDA实机部署（2026-10-25）

- C256门控统一支持TierGeometry/free_geometry，SPLIT=1显式退回。896×512/1280×768 Linux快验无对齐错误、invalid0；Phase10 selected模块未变。
- 当前Host已交叉编译并部署LmxxfNrRuntime.dll（SHA ec94f6db31c9310c32cc93b789b66294a25b00630b121a2d761dda182fcda353），40模块+标记在游戏HIP/sm_86，AMD旧目录移除，93个Small权重/207cso完整。Runtime架构目录探测与CUDA配置加载已修正。
- INI backend=lmxxf、WhitePointSource1、Preset2、Style1；配置0.5/FAST_NUMERIC1，FREE_RES1确保854×480→896×512。Windows D3D12/CUDA PrepareFrame验证modules40/hip1及优化gates开启，API各阶段成功。
- PTX三文件备份在C:\DLSS5-5090-dll\backups\Onimusha-ptx-0.1.0，两个旧NR DLL已移出根目录。部署与哈希[回执](hip-port/phase10/deploy-onimusha/README.md)齐全。下一步由Zero进入游戏验收画质与帧率，发布ZIP未改。

## 15. Phase 11 当前默认：C32 FFN feature直接half2量化（2026-10-25，闇）

- 唯一基线Phase10 selected，40SHA固定；只保留C32 fast Site2 half8→FP8，原RTZ residual/累加/布局保持。有限half16252928字节穷举0bit，实际RTZ生产者后全half模式0bit。A（只删RTZ往返）无稳定收益，保留负结果、不入默认；Graph/跨h2未重试。
- 最终默认实际重编/加载40/40模块、1918entry；39模块机器码未变，C32最终/候选57节一致。三档相对Phase10 0bit、invalid0、首末帧0bit、32/32零LMem，720 C256 wave2仍启用。F32 900/1080可见46.975322/46.100947dB不变；720 bit相同保证共同参考PSNR不降，旧未验收F32组合未作绝对金标准。
- 第一对50/80，Phase11 **GPU min/median**：720p13.894/14.406、900p23.205/24.019、1080p31.549/31.928ms；Wall med14.490/24.126/32.041，独立核累计13.586432/22.693888/28.465152ms。配对Phase10 med14.369/24.077/32.161。反向Phase11 med14.580/24.170/32.011，对照14.737/24.471/32.257。
- 收益小：1080两对约0.72%/0.76%，900微小正向；720没有稳定收益结论。默认DVFS约140W未锁频；单帧核累计不当帧均值或launch气泡。源、SSA/SASS、负结果、遥测及哈希均在[Phase11](hip-port/phase11/README.md)，[核级表](hip-port/phase11/results.md)。
- 最终候选 `phase11/artifacts/selected/modules/`；复测入口 `bash Development/hip-port/phase11/run_benchmark.sh`。只清理本轮重复临时产物，最终40模块保留；不改已冻结发布/部署，不push。Phase12优先从AV/V已有half生产点量化着手，逐站证明零误差，并补匹配720 F32参考。

## 16. Phase12 当前默认：C32 AV half2→FP8；逐站验证与720 F32参考审计（2026-10-25，闇）

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
