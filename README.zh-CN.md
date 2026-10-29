# DLSS5@NVIDIA RTX 30 (Ampere `sm_86`)

让 NVIDIA DLSS 5（`nvngx_dlssnr.dll` `310.9.16.0` 的 **31 块 Small 新模型**，"DLSSNR"）满血跑在 **NVIDIA GeForce RTX 3080 Laptop / RTX 30 系（Ampere `sm_86`）** 上。

[English](README.md) · [**📖 完整使用说明（公众号版）**](Development/doc/使用说明.md) · [更新日志](CHANGELOG.zh-CN.md) · [工作计划](Development/WorkingPlan.md) · [开发记录](Development/DevHistory.md)

> 🔗 **AMD Radeon RX 9070 XT / RDNA 4（`gfx1201`/`gfx1200`）姊妹项目：[dlss5-on-amd-9070xt-porting](https://github.com/lmxxf/dlss5-on-amd-9070xt-porting)** —— 我们将 DLSS 5 从零逆向重做到 AMD RDNA 4 显卡上的原生 HIP 推理引擎（720p `2.99 ms`、900p `4.25 ms`、1080p `5.49 ms`）。

把 NVIDIA 原版 `nvngx_dlssnr.dll`（`310.9.16.0`）内置的 15 个 Fatbin PTX 提取出来，将 Ada/Blackwell 专属的硬件 FP8（`e4m3x2`）转换、FP8 `m16n8k32` Tensor Core 指令与异步屏障改写为 Ampere `sm_86` 原生指令，并用两条 **IEEE 754 `f16x2` 硬件代数恒等式** 将生成的 `.cubin` 体积压缩 3.5 倍，使 **15/15 个 Fatbin 全部以满血 `--opt-level=4`（`O4`）编译塞回原 DLL 槽位**（对比网上 `dev-camo/dlssnr-patcher` 因 48 行整数位运算膨胀被迫降级 `O1` 快 **`2.08× ～ 2.25×`**，同时修复了上游 `fp8_pack_sources` 多定义误判导致的 106 条天空红绿横带 Bug）。本仓库只保留 31 块 `0.5x Small` 轻量新模型（`Preset 2`），不分发任何 NVIDIA 的二进制文件。

现在三个包的流水线都是：**按游戏（低）渲染分辨率拿一帧 → 我们的 `sm_86` 满血 `O4` 版 `nvngx_dlssnr.dll` 处理这一帧 → 超分（DLSS SR）放大到显示分辨率。** 三个包是三种接到这个位置的方式：

| 包 | 给谁 | 怎么接 |
|---|---|---|
| **OptiScaler**（常规） | 常规 DX12 游戏（《剑星》等） | OptiScaler 接管游戏的 DLSS 或 FSR 输入，在超分前通过 `nvngx.dll_dlssnr.dll` 调用修补后的 `nvngx_dlssnr.dll`，再由 DLSS SR 放大到全屏 |
| **OptiScaler-REFramework**（RE Engine 专用） | 《鬼武者：剑之道》《生化危机 9》等带反篡改校验的卡普空 RE Engine 游戏 | 在常规 OptiScaler 包基础上增加 REFramework（`dinput8.dll`）绕过校验并加载同目录 `dxgi.dll` |
| **Magpie**（便携窗口缩放） | 任何支持窗口化的游戏（《光环》等），不需要游戏内置 DLSS/FSR | Magpie 抓取游戏低分辨率窗口（如 720p），先跑内置的原生 `DLSSNR`（`Preset 2`）滤镜调用 `nvngx_dlssnr.dll`，再经 `DLSS_SR` 放大到 4K 全屏 |

**当前版本：0.3.0（2026-10-29），PTX V3.1_pack5。** 三包统一 **PTX V3.1_pack5、31块 Small / Preset2 / Style1、15/15 O4 原槽位（`266,414,592` B）**。RTX 3080 Laptop 模型 GPU median（50 warmup / 80 iter）：**研发两轮配对均值 720p `5.75 ms`、900p `8.42 ms`、1080p `11.35 ms`**（1080p 复测轮 `11.12 ms`）；**低温评估四轮均值 720p `5.62 ms`、900p `8.38 ms`、1080p `11.07 ms`**（对比 `v0.2.0` 的 `6.66 / 9.70 / 12.78 ms` 与 `v0.1.0` 的 `15.83 / 24.47 / 32.04 ms`）。本版相对 `V2.9_fast` 的三档 PSNR 为 `61.738 / 60.821 / 59.645 dB`（含新增舍入差异，非 0-bit），默认 OptiScaler 强度保持 `1.0/1.0`（附 `1.5/1.1` 增强风格）；[v0.3.0 发布回执与 SHA256](Development/ptx-patcher/release-rtx30/v030/README.md)。

### v0.3.0 文件校验

`nvngx_dlssnr.dll` SHA256: `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`

| ZIP | SHA256 |
|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip` | `5cd5b76df4287ab7a8c52a81f45fd701fcb053d81bc4b8c4a044afcb43cab470` |
| `OptiScaler-DLSS5-RTX30-0.3.0.zip` | `cb36b3ebd4a4f5413ea814a3138302e5a71ddf4259dbdc0ff8b23f092f0ea573` |
| `Magpie-DLSS5-RTX30-0.3.0.zip` | `46aff5aa9b64ec588779ac52aa7133acfd920a1f2656b786265344598abbb46e` |


---

## 环境要求与安装使用

- **硬件与驱动**：NVIDIA RTX 30 系显卡（Ampere `sm_86`，在 RTX 3080 Laptop GPU 16GB 上完成全套实测；桌面端 RTX 3060～3090 Ti 同属 `sm_86`）及支持 NGX 的 NVIDIA 正式版驱动（实测驱动 `616.92`）。无需安装 CUDA Toolkit、无需开启 Windows 开发人员模式。
- **安装方法**：
  1. **常规 DX12 游戏（`OptiScaler-DLSS5-RTX30-0.3.0.zip`）**：
     先退出游戏。将包内全部文件解压到游戏真正的 `.exe` 所在目录（例如《剑星》为 `StellarBlade\SB\Binaries\Win64\`，注意先备份原目录自带的 `amd_fidelityfx_dx12.dll`，不要只拷 4 个文件，必须把包内 26 KB 的 `amd_fidelityfx_dx12.dll` 加载器与 28 MB 的 `amd_fidelityfx_upscaler_dx12.dll` 等配套文件一起拷入）。进游戏开启 DLSS 或 FSR 超分即可生效。
  2. **卡普空 RE Engine 游戏（`OptiScaler-REFramework-DLSS5-RTX30-0.3.0.zip`）**：
     将包内全部文件解压到游戏 `.exe` 同级目录（例如 Xbox 版《鬼武者：剑之道》为 `C:\XboxGames\Onimusha- Way of the Sword\Content\`）。进游戏开启 DLSS 超分即可生效。
  3. **Magpie 窗口缩放（`Magpie-DLSS5-RTX30-0.3.0.zip`）**：
     将包完整解压到任意独立目录，游戏设为窗口模式（如 `1280×720` 或 `1600×900`）。以管理员运行 `Magpie.exe`，选择默认的 **`DLSS5-RTX30-PTX`** 配置（`DLSSNR [Preset 2, Style 1] → DLSS_SR`），点击“3 秒后缩放”并切回游戏窗口（或按 `Alt+Shift+A`）。
- **快捷键与调参**：
  - **`F6`**：在 OptiScaler 包中实时开关 DLSS 5 神经渲染对比。
  - **`Insert`**：呼出 OptiScaler 菜单，可在 `DLSS Neural Rendering` 面板调节 `Style`（`Standard` / `Natural` / `Cinematic`）、`Intensity`、`TransferStrength`（细节强度）和 `ColourStrength`（色彩强度）。
  - **曝光白点注意**：《鬼武者》（RE Engine）线性 HDR 缓冲原始数值在 `0～512`，必须保持 `WhitePointSource=1`（读取游戏原生曝光，白点约 `512x`），切勿手动改成 `1.0x`（否则未归一化的高光进入 OkLab 会触发全屏发绿）；《剑星》（UE4）预曝光比值约 `1.0x`。常规包默认 `TransferStrength=1.0 / ColourStrength=1.0`，减小转动视角时运动遮罩回退与原图的强度反差；另附 `OptiScaler-增强风格.ini`（1.5/1.1），供喜欢浓烈效果的用户选择。此轮完成配置与API smoke，未重新实玩验收闪烁。

---

## PTX 是怎么构建的 —— 原理与编译流水线

### 1. 为什么原版 `nvngx_dlssnr.dll` 不能在 RTX 30 系上跑？为什么网上的 `dlssnr-patcher` 会慢一倍且天空有红绿色带？

老黄的 `nvngx_dlssnr.dll`（`310.9.16.0`）内置了 15 个 Fatbin 容器（每个容器内含 1 份 `sm_120` Blackwell SASS ELF 和 1 份可重编译的 `.version 9.1` PTX 源码）。RTX 30 系（Ampere `sm_86`）硬件缺少 Ada/Blackwell 的原生 FP8（`e4m3x2`）转换指令、`mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16` 指令、TMA `cp.async.bulk` 以及 `fence.acquire.gpu;`。

网上开源的 `dev-camo/dlssnr-patcher` 在处理 `310.9.16.0` 时有三个致命问题：
1. **未处理 `310.9.16.0` 新增的 `fence.acquire.gpu;`**（位于 Fatbin 5 的 `cc_vit_1d_*` 核），导致 `nvptxcompile` 在 `sm_86` 上直接编译报错退出；
2. **48 行位运算膨胀导致被迫降级 `O1`（性能腰斩）**：它将每条 `cvt.rn.f16x2.e4m3x2` 和 `cvt.rn.satfinite.e4m3x2.f16x2` 展开为 45～48 行纯整数位运算 PTX，导致生成的 `.cubin` 膨胀到 `6.7～8.5 MB`，塞不进 PE 原始的 Fatbin 槽位，只能在全部主干网络（Fatbin 00～06）上回退到 `--opt-level=1`（`O1`，关闭指令调度、循环展开与窥孔优化），耗时翻倍；
3. **`fp8_pack_sources`（`mapped` 捷径）多定义漏检导致 106 条天空红绿横带**：上游为了省去 `cvt.e4m3x2.f16x2 + mov.b32 pack`，只要看到某个寄存器 `%r` 在整个函数里只匹配过一次 `mov.b32 %r, {%rs1, %rs2}`，就直接拿 `%rs1, %rs2` 的源 FP16 寄存器喂给 `mma.sync`。但在 `cc_vit_attention_fp8` 等核里，`%r1352` 在正常分支由花括号向量加载指令 `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]` 从显存读取真实特征，而在越界 fallback 分支才由 `mov.b32 %r1352, {%rs2, %rs2}` 填入常数。上游漏检了向量加载的多重定义，把 `mma.sync` 的操作数替换成了越界常数，在平滑天空上直接打出 106 条周期性红绿横带。

### 2. 我们的五项核心改进（[`Development/ptx-patcher/build_sm86_dlls.py`](Development/ptx-patcher/build_sm86_dlls.py)）

1. **代数恒等式一（`E4M3x2 → FP16x2`，仅 4 条 SASS 指令，254/254 有限值 `0 bit-diff`）**：
   E4M3 的指数偏置是 $7$，FP16 的指数偏置是 $15$，相差 $15 - 7 = 8$。把两个 E4M3 字节通过 `prmt.b32` 摆到 32 位寄存器的高/低 16 位对应字节，分离符号位并将 7 位指数+尾数右移 1 位对齐到 FP16 的 `bit [13:7]`：
   - 当 E4M3 为正规数（$e \ge 1$）时，这恰好是一个指数为 $e$、数值等于 $(-1)^s \cdot 2^{e-15} \cdot (1 + m/8)$ 的 FP16 正规数；
   - 当 E4M3 为次正规数（$e = 0$）时，这恰好是一个 FP16 指数为 $0$、尾数高 3 位为 $m$ 的 FP16 次正规数 $(-1)^s \cdot 2^{-14} \cdot (m/8)$！
   随后只需执行一条硬件向量乘法 **`mul.rn.f16x2 %d, %d, 0x5c005c00;`**（乘以 $2^8 = 256.0_{\text{f16}}$），硬件 FPU 就会把正规数指数变为 $e - 15 + 8 = e - 7$，并自动将次正规数硬件归一化为 $(-1)^s \cdot 2^{-6} \cdot (m/8)$，省去了全部分支判断与 `bfind` 前导零搜索。
2. **代数恒等式二（`FP16x2 → E4M3x2`，硬件次正规数 RNE 舍入，63,488/63,488 有限值 `0 bit-diff`）**：
   在 IEEE FP16 中，常数 `2.0h`（`0x4000`）的最低有效位间距为 $\text{ULP}(2.0_{\text{f16}}) = 2^1 \times 2^{-10} = 2^{-9}$，**分毫不差正好等于 E4M3 次正规数的最小网格间距 $2^{-9}$**！
   因此对次正规数范围直接执行一条 **`add.rn.f16x2 sub2, sub_in, 0x40004000;`**，硬件加法器就会同时对两个通道完成精确的向偶舍入（Round-to-Nearest-Even），结果直接落在 `sub2` 的低字节中；正规数则通过无借位的 `bfe.u32` 提取并钳位至 `0x7e`（`448.0`）。
   这两条恒等式将编译后的 `.cubin` 体积从 `6.7～8.5 MB` 压回 `2.1～2.8 MB`，使 **15/15 个 Fatbin 全部在 `--opt-level=4`（满血 `O4`）下一次编译通过并原位装回 PE 槽位**。
3. **全指令定义扫描与非法 `mapped` 剔除（红绿横带 `106 → 0`）**：
   解析每个 PTX `.entry` 内所有指令的目的操作数（含 `{ %r1, %r2, %r3, %r4 }` 花括号向量加载、谓词指令与普通指令），一旦发现 `pack` 目标寄存器、FP8 中间寄存器或 FP16 源寄存器在函数内存在多重定义（如 `%r1352`），立即拒绝该 `mapped` 转发并回退到寄存器原地解包；真正单定义的本地 `mapped` 则使用 `prmt 0x5410 / 0x7632` 转发，不做跨lane洗牌。修复后天空红绿变号从 **106 次降为 0 次**，高频色差 RMS 降低 **263 倍**。

4. **偶奇 K16 原位拆解**：A/B在同lane使用相同K置换，先算byte0/2、再算byte1/3；编码操作数不再做跨lane SHFL或PRMT，合法mapped仅用5410/7632 PRMT。它改变FP16累加分组；V2.1相对V2输出严格0bit，不能宣称相对0.1.0也逐位相同。
5. **按FB放宽寄存器上限**：仅FB00/03/04/05/06的`.maxnreg`升到255；FB01/02保持原值。FB00/03/06的STACK和LDL/STL归零，FB04/05仍有80/8B最大STACK，不是全DLL零spill。全部255的控制反而略慢，采用实测胜出的hot255组合。

### 3. PTX 修补与构建的完整 6 步流水线

```text
原版 nvngx_dlssnr.dll (310.9.16.0, 266,424,944 B)
  │
  ├─ [Step 1] 扫描 PE 定位 15 个 Fatbin 容器 (find_fatbins)，Zstd 解压提取内部 PTX 源码
  │
  ├─ [Step 2] PTX 语法与同步降级：
  │    • .version 9.1 → .version 9.3, .target sm_120a → .target sm_86
  │    • fence.release.gpu; / fence.acquire.gpu; → fence.acq_rel.gpu;
  │    • elect.sync + cp.async.bulk + mbarrier.expect_tx → 全 lane cp.async.cg 16B + mbarrier
  │    • red.global.v4.f16x2.add.noftz → 4 条独立 red.global.f16x2.add.noftz
  │    • min.relu.s32 → min.s32 + max.s32 0
  │
  ├─ [Step 3] FP8 Tensor Core 与转换重写：
  │    • 全函数单定义扫描过滤 fp8_pack_sources (剔除 %r1352 等向量加载多定义误判)
  │    • mma.m16n8k32.e4m3 → 同lane偶/奇K拆解 + 2 条 mma.m16n8k16.f16.f16.f16.f16 (Full Rate!)
  │    • cvt.f16x2.e4m3x2 → prmt.b32 + mul.rn.f16x2 0x5c005c00
  │    • cvt.e4m3x2.f16x2 → add.rn.f16x2 0x40004000 (次正规) + bfe.u32 (正规)
  │
  ├─ [Step 4] 多进程并行调用 libcuda.so.1 (cuModuleLoadDataEx, CU_JIT_OPTIMIZATION_LEVEL=4)
  │    • FB00/03/04/05/06 maxnreg→255；15/15 Fatbin O4 编译为 sm_86 ELF cubin
  │
  ├─ [Step 5] 调用 libzstd.so.1 (level 22) 压缩 cubin，封装回 Fatbin 槽位，尾部剩余字节填 0
  │
  └─ [Step 6] 修补 PE 导出函数中的 NGX 最低架构检查立即数 (0x120 → 0x80)，
              剥离失效的 Authenticode 证书表，重算并写入 PE Checksum
  │
  ▼
产出满血 O4 版 nvngx_dlssnr.dll (266,414,592 B, SHA256: c7d4c8b6...)
```

### 4. 每个发布文件从哪来与编译命令

| 包里的核心文件 | 源码 / 工具位置 | 构建命令 |
|---|---|---|
| **`nvngx_dlssnr.dll`**（三个包共用，15/15 `O4` `sm_86` 修补版） | `Development/ptx-patcher/build_sm86_dlls.py` + `dlssnr_patcher.py` | `python3 Development/ptx-patcher/v21/build_recommended.py` |
| **`nvngx.dll_dlssnr.dll`**（OptiScaler 两个包共用，NGX 调用名转发桥） | `Development/ptx-patcher/dlssnr_forwarder.cpp` | `x86_64-w64-mingw32-g++ -O2 -shared -static -o nvngx.dll_dlssnr.dll Development/ptx-patcher/dlssnr_forwarder.cpp` |
| **`Magpie.exe`**（Magpie 包专用，将原生 `DLSSNR` 硬编码的 `Preset 0` 改为 `Preset 2`） | `Development/ptx-patcher/magpie-native/patch_preset2.py` | `python3 Development/ptx-patcher/magpie-native/patch_preset2.py --input /path/to/orig/Magpie.exe --output /path/to/out/Magpie.exe` |
| **`bench.exe`**（独立 D3D12 NGX Feature 18 硬件计时测试台） | `Development/ptx-patcher/bench_nvngx.dll.cpp` | `x86_64-w64-mingw32-g++ -O3 -std=c++17 -static Development/ptx-patcher/bench_nvngx.dll.cpp -ld3d12 -ldxgi -o bench.exe` |
| 三个 `v0.2.0` 发布包组装与校验脚本 | `Development/ptx-patcher/release-rtx30/` 与 `magpie-native/deploy_release.py` | 见对应目录下的打包与 SHA256 校验脚本 |

单元测试与回归验证：
```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

---

## 实测性能对照（RTX 3080 Laptop GPU, 16GB, `sm_86`，默认 DVFS）

### 1. 历史方案标尺与当前版本（均为 31 块 `0.5x Small` 模型，`Preset 2`）

| 方案 | 编译器优化 | `1280×720` (720p) | `1600×900` (900p) | `1920×1080` (1080p) | 天空渐变红绿变号 | 相对上游提速 |
|---|:---:|---:|---:|---:|---:|:---:|
| ① 网上 `dlssnr-patcher` 原版位运算 (`stock`) | 主网络被迫回退 `O1` | `37.13 ms` | `49.89 ms` | `67.69 ms` | `106 次`（有色带） | `1.00×` |
| **② 本项目 `ptx-patcher` (`v0.1.0`)** | **15/15 全部满血 `O4`** | **`15.83 ms`** | **`24.47 ms`** | **`32.04 ms`** | **`0 次`（彻底消除）** | **`2.08× ～ 2.35×`** |
| **③ 本项目 `ptx-patcher` (`v0.2.0 / V2.1`)** | **15/15 `O4` + 偶奇 K16 零洗牌 + `255` 寄存器** | **`6.66 ms`** | **`9.70 ms`** | **`12.78 ms`** | **`0 次`（彻底消除）** | **`5.14× ～ 5.58×`** |
| **④ 当前 `ptx-patcher` (`v0.3.0 / V3.1_pack5`)** | **`V2.2~V3.1` 全套升级 + 5-SASS Pack** | **`5.62 ~ 5.75 ms`** | **`8.38 ~ 8.42 ms`** | **`11.07 ~ 11.35 ms`** | **`0 次`（彻底消除）** | **`5.96× ～ 6.61×`** |

### 2. 游戏与窗口实机表现（RTX 3080 Laptop GPU 16GB）

| 游戏 / 场景 | 接入包 | 渲染分辨率 → 输出分辨率 | DLSS 5 模型 GPU 耗时 | 实机表现 |
|---|---|---|---|---|
| **《鬼武者：剑之道》（`v0.2.0 ~ v0.3.0`）** | `OptiScaler-REFramework` | `1280×720` → `2560×1440` (2K Performance) | **`~5.62 ~ 5.75 ms`**（`v0.2.0` 为 `6.66 ms`，`v0.1.0` 为 `16.7～17.5 ms`） | 整机实玩从 `v0.1.0` 的 `30 FPS` → `v0.2.0` 的 `43 FPS` → 未触发 86°C 温控降频时达 **`47 FPS`** |
| **《剑星》(Stellar Blade)（`v0.2.0 ~ v0.3.0`）** | `OptiScaler`（常规包） | `1280×720` → `2560×1440` (2K Performance) | **`~5.62 ~ 5.75 ms`**（`v0.1.0` 为 `18.1～18.6 ms`） | 整机实玩达**接近 `60 FPS`**，默认 `1.0 / 1.0` 平衡配置无视角转动闪烁 |
| **《鬼武者：剑之道》（`v0.1.0` 历史对照）** | `OptiScaler-REFramework` | `854×480` → `2560×1440` (2K Ultra Perf) | `7.3 ～ 9.1 ms` | `v0.1.0` 整机实玩 **46 FPS** |
| **《光环》(Halo) 窗口化（`v0.1.0` 历史对照）** | `Magpie`（便携包） | `1280×720` → `3840×2160` (4K) | `15.87 ～ 16.00 ms`（`v0.3.0` 模型已降至 `5.62~5.75 ms`） | `v0.1.0` 含后级 4K `DLSS_SR` 总 GPU 耗时 `21.2 ms`（`v0.2.0+` 可压入 `16.67 ms` 跑满 60Hz 电视 60 FPS） |

---

## 更新记录

每一版的详细改动（改了什么、效果、文件 SHA256、实验目录）见 [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)。

| 版本 | 日期 | 做了什么 | 结果 |
|---|---|---|---|
| **`0.3.0`** | 2026-10-29 | 集成 `V2.2~V3.1_pack5` 全部 PTX 升级（`cp.async.mbarrier` 绑定、8 指令 `PRMT` 解包、JIT 按需解码与池回收、Low/High K16 + `mapped` 零拷贝直连、C32 四核 `168 cap`、以及 5-SASS Unified Mul Pack `|R2|` 折叠 + `LEA 0x7f007f` 舍入），38 活跃核非 NOP 静态 SASS 降至 `152,076` 条。 | **研发配对 5.75 / 8.42 / 11.35 ms，低温评估 5.62 / 8.38 / 11.07 ms**（比 `v0.2.0` 再快 `~13% ~ 16%`）；[回执](Development/ptx-patcher/release-rtx30/v030/README.md) |
| **`0.2.0`** | 2026-10-26 | 偶奇K16零洗牌＋按FB maxnreg255；剑星默认1.0/1.0，附增强风格1.5/1.1；三个新ZIP及SHA（[Gofile 下载](https://gofile.io/d/OOeOcxn6)）。 | **6.66 /9.70 /12.78ms**；《鬼武者》2K性能档 **43 FPS**（原30 FPS），《剑星》2K性能档**接近 60 FPS**；[回执](Development/ptx-patcher/release-rtx30/v020/README.md) |
| **`0.1.0`** | 2026-10-24 | **首发版本（三个发布包全线统一为 15/15 满血 `O4` PTX 路线，仅保留 31 块 `0.5x Small` 新模型）**：<br>1. **PTX 满血 `O4` 编译器（`Development/ptx-patcher/`）**：提出两条 IEEE 754 `f16x2` 硬件代数恒等式（`mul.rn.f16x2 0x5c005c00` 解包 E4M3、`add.rn.f16x2 0x40004000` 舍入 E4M3 次正规数，有限值域 `0 bit-diff`），将 `.cubin` 体积缩小 3.5 倍，15/15 个 Fatbin 全部 `O4` 装回原槽位；修复 `310.9.16.0` 的 `fence.acquire.gpu;` 编译失败。<br>2. **消除天空红绿横带（`sky-audit/`）**：定位并修复上游 `fp8_pack_sources` 未扫描花括号向量加载（如 `FB5 %r1352`）导致将显存特征误替换为越界 fallback 常数的致命 Bug，天空逐行红绿色差变号从 `106 次` 降为 `0 次`，高频色差 RMS 降低 263 倍。<br>3. **三包构建与游戏适配**：<br>  • `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`（SHA256 `8e28417d...`）：适配《鬼武者：剑之道》等 RE Engine 游戏，校准 `WhitePointSource=1`（`~512x` 原生曝光）；<br>  • `OptiScaler-DLSS5-RTX30-0.1.0.zip`（SHA256 `e6067bf0...`）：适配《剑星》等常规 DX12 游戏，配齐完整 FFX 转发库（支持游戏内选 FSR 或 DLSS 自动转接），默认应用单遍增强（`detail=1.5, colour=1.1`）；<br>  • `Magpie-DLSS5-RTX30-0.1.0.zip`（SHA256 `db41eaeb...`）：打通 `Magpie.exe` 原生 `DLSSNR` Feature 18 后端，通过二进制补丁将写死的 `Preset 0` 改为 `Preset 2`（31 块轻量模型），补齐 `nvngx_dlss.dll` 修复 `0xbad0000b` 报错，720p 模型耗时 **`15.9 ms`**。 | 测试台 720p **`15.83 ms`**、900p **`24.47 ms`**、1080p **`32.04 ms`**（比上游 `O1` 快 **2.08×～2.35×**）；《鬼武者》《剑星》《光环》实机验收通过 |

---

## 仓库目录结构

| 目录 / 文件 | 内容 |
|---|---|
| `Development/ptx-patcher/` | 原版 `310.9.16.0` `nvngx_dlssnr.dll` 的 `sm_86` 满血 `O4` PTX 转换器（`build_sm86_dlls.py`、`dlssnr_patcher.py`）、NGX 调用转发桥（`dlssnr_forwarder.cpp`）、硬件计时测试台（`bench_nvngx.dll.cpp`）、天空色带排查回执（`sky-audit/`）、偶奇 K16 零洗牌与寄存器调优（`v2/`、`v21/`）、Magpie 原生 `Preset 2` 补丁（`magpie-native/`）及三包构建脚本（`release-rtx30/`） |
| `Development/doc/` | 用户使用说明与各版本改进详解（[`改进和使用说明_0.2.0.md`](Development/doc/改进和使用说明_0.2.0.md)、[`使用说明.md`](Development/doc/使用说明.md)） |
| `Development/DevHistory.md` | 完整的开发流水账、对照实验数据、失败排查与每个阶段的文件 SHA256 回执 |
| `Development/WorkingPlan.md` | 架构设计与优化路线图 |
| `CHANGELOG.zh-CN.md` / `CHANGELOG.md` | 按版本展开的详细更新日志 |

---

## 作者与许可

- **作者**：Kien —— 方向、游戏接入、实机测试与架构决策；逆向、PTX/CUDA 核优化与打包自动化由 AI 协作者（朱雀 / Claude / Gemini / GPT）共同完成。完整技术故事见[公众号 DLSS5 系列合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzYzMzMwNzk0NA==&action=getalbum&album_id=4687269655390453762#wechat_redirect)。
- **许可**：本仓库代码以 [MIT](LICENSE) 许可发布。NVIDIA 的二进制文件与模型权重不在本仓库分发之列。
