# 更新日志 (Changelog)

[English](CHANGELOG.md) · [返回首页](README.zh-CN.md)

本文件详细记录每个版本的修改内容、性能实测、配置项与发布包 SHA256 校验值。

---

## 0.3.0 (2026-10-29)

下载：[夸克网盘](https://pan.quark.cn/s/1ace87045701) · [Gofile 镜像](https://gofile.io/d/oR1ZAEvO)

三个正式包统一升级为 **PTX V3.1_pack5**（31 块 Small / Preset 2 / Style 1，15/15 O4 原槽位，`266,414,592` B）：
- **核心管线升级（`V2.2 → V3.1_pack5`）**：
  - `V2.2`：原生 `cp.async.mbarrier.arrive` 异步完成绑定 + 无分支 SWAR `f16x2 → e4m3x2` 量化；
  - `V2.3`：8 指令 `PRMT`（`0x9180 / 0xb3a2`）解包；
  - `V2.4`：按需解码（JIT decode）与死亡临时寄存器池回收；
  - `V2.6`：Low/High K16 布局 + `mapped` 操作数零拷贝直连转发（消除 21,712 处生成路径 `mapped PRMT`）；
  - `V2.7`：C32 四个核 `maxnreg 168` 驻留优化（CUDA Occupancy API 驻留从 8 升至 12 warps/SM）；
  - `V2.9_fast → V3.1_pack5`：利用 `mul.rn.f16x2 0x1c001c00`（$\times 2^{-8}$）统一 Normal/Subnormal 尾数对齐、将 `abs.f16x2` 免费折叠进 `HMNMX2 |R2|` 硬件绝对值修饰符，并用单条 `LEA 0x007f007f` 完成符号对称 Ties-toward-Zero 舍入，使单对打包核心 SASS 从 **13 条 → 9 条 → 5 条**，38 个活跃 FP8 核的非 NOP 静态 SASS 总数降至 **`152,076` 条**（对比 `V2.7` 的 `175,685` 条与 `V2.9_fast` 的 `163,944` 条）。
- **RTX 3080 Laptop 模型 GPU Median 标尺（`bench_sky` 50 warmup / 80 iter）**：
  - 研发两轮同轮配对均值（[`v31/README.md`](Development/ptx-patcher/v31/README.md)）：**720p `5.75 ms` / 900p `8.42 ms` / 1080p `11.35 ms`**（1080p 复测轮 `11.12 ms`）；
  - 低温评估四轮均值（[`性能评估20261029-2000.md`](Development/doc/性能评估20261029-2000.md)，平均 `70.85 °C`）：**720p `5.62 ms` / 900p `8.38 ms` / 1080p `11.07 ms`**（对比 `v0.2.0` 历史标尺 `6.66 / 9.70 / 12.78 ms`）。
  - 相对 `V2.9_fast` 三档 PSNR 为 **`61.738 / 60.821 / 59.645 dB`**（全部 finite，720p 天空测试 0 变号）。三个包 Windows Feature 18 与两个 OptiScaler 包 FFX→NGX→NR 端到端 smoke 全部通过（`nonfinite=0`）。
- **正式三包与 SHA256（[`v030/README.md`](Development/ptx-patcher/release-rtx30/v030/README.md)）**：
  - `OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip`（`375,029,334` B）：`5cd5b76df4287ab7a8c52a81f45fd701fcb053d81bc4b8c4a044afcb43cab470`
  - `OptiScaler-DLSS5-RTX30-0.3.0.zip`（`317,957,671` B）：`cb36b3ebd4a4f5413ea814a3138302e5a71ddf4259dbdc0ff8b23f092f0ea573`
  - `Magpie-DLSS5-RTX30-0.3.0.zip`（`322,882,553` B）：`46aff5aa9b64ec588779ac52aa7133acfd920a1f2656b786265344598abbb46e`
  - 核心 DLL SHA256：`1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`。

## 0.2.0 (2026-10-26)

下载：[Gofile 镜像](https://gofile.io/d/OOeOcxn6)

三个正式包统一PTX V2.1：偶奇K16原位拆解消除MMA操作数洗牌，FB00/03/04/05/06的maxnreg升255，15/15 O4原槽位。三档GPU median **6.66 /9.70 /12.78ms**；V2.1相对V2严格0bit，STACK大幅减少但不是全网零spill。

《鬼武者》根目录和_storage_恢复原版dxgi（aa3761f2…），清理HIP运行时并切回PTX，RTX 3080 Laptop 实机 2K 性能档从 `v0.1.0` 的 `30 FPS` 跃升至 **`43 FPS`**；《剑星》默认TransferStrength/ColourStrength=1.0/1.0（附OptiScaler-增强风格.ini 1.5/1.1），实机 2K 性能档达**接近 `60 FPS`**；Magpie保留Preset2补丁并升级DLL。

相比0.1.0历史耗时约2.38～2.53×；上游O1三档历史比值为5.58/5.14/5.30×。三包Windows Feature18及两个OptiScaler FFX→NGX→NR smoke通过，输出finite；包CRC/逐文件SHA通过。修补DLL Authenticode为NotSigned。

- `OptiScaler-REFramework-DLSS5-RTX30-0.2.0.zip`（375,533,391 B）：`531179b60d55e7147262e488afa760f8fc6422b353882ee5b223c47db3022d94`
- `OptiScaler-DLSS5-RTX30-0.2.0.zip`（318,461,731 B）：`ce7c18e05e286f17b93ee841d2ea9ae829f62cb0a5b3018b93500d3eb902509f`
- `Magpie-DLSS5-RTX30-0.2.0.zip`（323,386,599 B）：`e88a6c86ee6803de64cf6cabb1d3d2af3ef37565c91822a77a5dd8a6ef347739`

Core DLL SHA256: `c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed`.

## 0.1.0 (2026-10-24)

下载：[Gofile 镜像](https://gofile.io/d/s9cpHYH9)

首个正式发布版本。面向 NVIDIA RTX 30 系（Ampere `sm_86`），全线仅启用 `310.9.16.0` 的 **31 块 `0.5x Small` 轻量新模型（`Preset 2`）**，三个发布包统一采用 **15/15 满血 `O4` PTX 改写路线**。

### 1. PTX 满血 `O4` 编译器与代数恒等式（`Development/ptx-patcher/`）
- **修复 `310.9.16.0` 的 `fence.acquire.gpu;` 编译失败**：将 Fatbin 5 新增的 `fence.acquire.gpu;` 与 `fence.release.gpu;` 统一降级为 Ampere `sm_86` 支持的 `fence.acq_rel.gpu;`。
- **两条 IEEE 754 `f16x2` 硬件代数恒等式（有限值域 `0 bit-diff`）**：
  - `E4M3x2 → FP16x2`：`prmt.b32` 重排后用单条 `mul.rn.f16x2 %d, %d, 0x5c005c00`（$\times 256.0_{\text{f16}}$）完成正规数指数修正与次正规数硬件归一化（覆盖全部 254 个有限 E4M3 编码）；
  - `FP16x2 → E4M3x2`：利用 $\text{ULP}(2.0_{\text{f16}}) = 2^{-9}$ 与 E4M3 次正规数网格完全相等的性质，用单条 `add.rn.f16x2 sub2, sub_in, 0x40004000` 同时完成双通道次正规数向偶舍入（GPU 穷举覆盖全部 63,488 个有限 FP16 编码）。
- **15/15 Fatbin 满血 `O4` 原槽位装入**：将 `.cubin` 体积从上游整数展开的 `6.7～8.5 MB` 缩小至 `2.1～2.8 MB`，15 个 Fatbin 全部在 `--opt-level=4` 下编译并装回原 PE 槽位，相比上游 `O1` 提速 **`2.08× ～ 2.35×`**。

### 2. 修复上游 `fp8_pack_sources` 多定义误判导致的 106 条天空红绿横带（`Development/ptx-patcher/sky-audit/`）
- **根因**：上游 `fp8_pack_sources` 未扫描花括号向量加载指令（如 `FB5 cc_vit_attention_fp8` 中的 `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]`），将 `%r1352` 误判为仅由越界 fallback 分支的 `mov.b32 %r1352, {%rs2, %rs2}` 定义，导致 `mma.sync` 丢失显存真实特征并在平滑天空上产生 106 条周期性红绿横带。
- **修复**：对整个 `.entry` 内的全部指令目的操作数（含花括号向量目标）建立定义计数，拒绝任何目标寄存器、中间寄存器或源寄存器存在多定义的 `mapped` 转发；合法单定义 `mapped` 保持零开销转发。
- **效果**：`1280×720` 天空渐变测试中逐行红绿色差变号从 **`106 次` 降为 `0 次`**，高频色差 RMS 从 `0.026994` 降至 `0.0001027`（降低 263 倍），同时保持 `720p 15.83 ms` / `900p 24.47 ms` / `1080p 32.04 ms` 的满血速度。

### 3. 三个正式发布包改动与校验值
- **`OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`**（`376,272,150 B`，SHA256 `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67`）：
  - 适用于《鬼武者：剑之道》《生化危机 9》等 RE Engine 游戏；
  - 含 `dinput8.dll`（REFramework）、`dxgi.dll`（OptiScaler）、`nvngx.dll_dlssnr.dll` 与满血 `O4` 修补版 `nvngx_dlssnr.dll`（SHA256 `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`）；
  - 默认 `Preset=2, Style=1, WhitePointSource=1`（读取游戏曝光）。《鬼武者》2K Ultra Perf（480p）模型耗时 `7.3～9.1 ms`（整机 **46 FPS**），720p 模型耗时 `16.7～17.5 ms`（整机 **30 FPS**）。
- **`OptiScaler-DLSS5-RTX30-0.1.0.zip`**（`319,200,566 B`，SHA256 `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac`）：
  - 适用于《剑星》等常规 DX12 游戏；
  - 配齐完整 FFX loader（26 KB `amd_fidelityfx_dx12.dll`）与 upscaler（28 MB `amd_fidelityfx_upscaler_dx12.dll`），支持游戏内选 FSR 或 DLSS 自动转接至 `DLSS-NR → DLSS SR`；
  - 默认启用单遍增强（`TransferStrength=1.5, ColourStrength=1.1`），另附 `OptiScaler-原始平衡.ini`（`1.0 / 1.0`）。
- **`Magpie-DLSS5-RTX30-0.1.0.zip`**（`324,124,886 B`，SHA256 `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb`）：
  - 适用于任意窗口化游戏（如《光环》720p 窗口 → 4K 全屏）；
  - 启用 `Magpie.exe` 原生 `DLSSNR\DLSSNR_AI_Filter`（Feature 18）后端 + `DLSS\DLSS_SR` 超分，通过 `patch_preset2.py` 将 `Magpie.exe` 硬编码的 `Preset 0` 改为 `Preset 2`（SHA256 `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea`）；
  - 补齐 `nvngx_dlss.dll` 修复 `DLSS_SR` 的 `0xbad0000b` 初始化报错；
  - 720p 下 `DLSSNR` 模型 GPU 耗时 **`15.87～16.00 ms`**（含 4K `DLSS_SR` 总 GPU 耗时 `21.2 ms`）。
