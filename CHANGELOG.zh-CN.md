# 更新日志 (Changelog)

[English](CHANGELOG.md) · [返回首页](README.zh-CN.md)

本文件详细记录每个版本的修改内容、性能实测、配置项与发布包 SHA256 校验值。

---

## 0.1.0 (2026-10-24)

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
  - 补齐 `nvngx_dlss.dll` 修复 `DLSS_SR` 的 `0xbad0000b` 初始化报错，移除旧 ReShade `dxgi.dll`、`dlss5-amd.addon64` 与 `DLSS5-AMD/` 外置碎权重；
  - 720p 下 `DLSSNR` 模型 GPU 耗时从旧独立引擎路线 A 的 `49.8 ms` 暴降至 **`15.87～16.00 ms`**（含 4K `DLSS_SR` 总 GPU 耗时 `21.2 ms`）。

### 4. 附加路线归档（`Development/hip-port/`）
- 保留从 AMD RDNA4 (`gfx1201`) 全栈移植到 Ampere `sm_86` 的 40 模块（1,970 个核入口）HIP/CUDA 独立推理引擎源码（V6 8B 全激活预洗牌 + K32 消洗牌 + 32/32 核零 `LMem` 栈溢出，31 块 900p `43.10 ms`、1080p `57.13 ms`）。
