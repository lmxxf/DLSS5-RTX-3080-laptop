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

**当前版本：0.1.0（2026-10-24）。** 下载：[Gofile 镜像](https://gofile.io/d/s9cpHYH9)。首发版本：三个发布包全线统一为 **15/15 满血 `O4` PTX 改写路线（`Preset 2` 31 块新模型）**。修复上游 `dlssnr-patcher` 在 `310.9.16.0` 上的 `fence.acquire.gpu` 编译失败、消除 `O1` 性能腰斩、修复 `fp8_pack_sources` 多定义误判引发的 106 条天空红绿横带；在 RTX 3080 Laptop（132W）上 **720p 单帧模型耗时 `15.83 ms`、900p `24.47 ms`、1080p `32.04 ms`（480p 仅 `8.2 ms`）**。[完整说明与版本记录](CHANGELOG.zh-CN.md#010-2026-10-24)。

---

## 环境要求与安装使用

- **硬件与驱动**：NVIDIA RTX 30 系显卡（Ampere `sm_86`，在 RTX 3080 Laptop GPU 16GB 上完成全套实测；桌面端 RTX 3060～3090 Ti 同属 `sm_86`）及支持 NGX 的 NVIDIA 正式版驱动（实测驱动 `616.92`）。无需安装 CUDA Toolkit、无需开启 Windows 开发人员模式。
- **安装方法**：
  1. **常规 DX12 游戏（`OptiScaler-DLSS5-RTX30-0.1.0.zip`）**：
     先退出游戏。将包内全部文件解压到游戏真正的 `.exe` 所在目录（例如《剑星》为 `StellarBlade\SB\Binaries\Win64\`，注意先备份原目录自带的 `amd_fidelityfx_dx12.dll`，不要只拷 4 个文件，必须把包内 26 KB 的 `amd_fidelityfx_dx12.dll` 加载器与 28 MB 的 `amd_fidelityfx_upscaler_dx12.dll` 等配套文件一起拷入）。进游戏开启 DLSS 或 FSR 超分即可生效。
  2. **卡普空 RE Engine 游戏（`OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`）**：
     将包内全部文件解压到游戏 `.exe` 同级目录（例如 Xbox 版《鬼武者：剑之道》为 `C:\XboxGames\Onimusha- Way of the Sword\Content\`）。进游戏开启 DLSS 超分即可生效。
  3. **Magpie 窗口缩放（`Magpie-DLSS5-RTX30-0.1.0.zip`）**：
     将包完整解压到任意独立目录，游戏设为窗口模式（如 `1280×720` 或 `1600×900`）。以管理员运行 `Magpie.exe`，选择默认的 **`DLSS5-RTX30-PTX`** 配置（`DLSSNR [Preset 2, Style 1] → DLSS_SR`），点击“3 秒后缩放”并切回游戏窗口（或按 `Alt+Shift+A`）。
- **快捷键与调参**：
  - **`F6`**：在 OptiScaler 包中实时开关 DLSS 5 神经渲染对比。
  - **`Insert`**：呼出 OptiScaler 菜单，可在 `DLSS Neural Rendering` 面板调节 `Style`（`Standard` / `Natural` / `Cinematic`）、`Intensity`、`TransferStrength`（细节强度）和 `ColourStrength`（色彩强度）。
  - **曝光白点注意**：《鬼武者》（RE Engine）线性 HDR 缓冲原始数值在 `0～512`，必须保持 `WhitePointSource=1`（读取游戏原生曝光，白点约 `512x`），切勿手动改成 `1.0x`（否则未归一化的高光进入 OkLab 会触发全屏发绿）；《剑星》（UE4）预曝光与游戏曝光比值天然为 `1.0x`，常规包已默认将 `TransferStrength` 设为 `1.5`、`ColourStrength` 设为 `1.1` 以增强重打光观感（包内另附 `OptiScaler-原始平衡.ini` 可恢复 `1.0 / 1.0`）。

---

## PTX 是怎么构建的 —— 原理与编译流水线

### 1. 为什么原版 `nvngx_dlssnr.dll` 不能在 RTX 30 系上跑？为什么网上的 `dlssnr-patcher` 会慢一倍且天空有红绿色带？

老黄的 `nvngx_dlssnr.dll`（`310.9.16.0`）内置了 15 个 Fatbin 容器（每个容器内含 1 份 `sm_120` Blackwell SASS ELF 和 1 份可重编译的 `.version 9.1` PTX 源码）。RTX 30 系（Ampere `sm_86`）硬件缺少 Ada/Blackwell 的原生 FP8（`e4m3x2`）转换指令、`mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16` 指令、TMA `cp.async.bulk` 以及 `fence.acquire.gpu;`。

网上开源的 `dev-camo/dlssnr-patcher` 在处理 `310.9.16.0` 时有三个致命问题：
1. **未处理 `310.9.16.0` 新增的 `fence.acquire.gpu;`**（位于 Fatbin 5 的 `cc_vit_1d_*` 核），导致 `nvptxcompile` 在 `sm_86` 上直接编译报错退出；
2. **48 行位运算膨胀导致被迫降级 `O1`（性能腰斩）**：它将每条 `cvt.rn.f16x2.e4m3x2` 和 `cvt.rn.satfinite.e4m3x2.f16x2` 展开为 45～48 行纯整数位运算 PTX，导致生成的 `.cubin` 膨胀到 `6.7～8.5 MB`，塞不进 PE 原始的 Fatbin 槽位，只能在全部主干网络（Fatbin 00～06）上回退到 `--opt-level=1`（`O1`，关闭指令调度、循环展开与窥孔优化），耗时翻倍；
3. **`fp8_pack_sources`（`mapped` 捷径）多定义漏检导致 106 条天空红绿横带**：上游为了省去 `cvt.e4m3x2.f16x2 + mov.b32 pack`，只要看到某个寄存器 `%r` 在整个函数里只匹配过一次 `mov.b32 %r, {%rs1, %rs2}`，就直接拿 `%rs1, %rs2` 的源 FP16 寄存器喂给 `mma.sync`。但在 `cc_vit_attention_fp8` 等核里，`%r1352` 在正常分支由花括号向量加载指令 `ld.weak.global.ca.v4.u32 {%r1352, %r1353, %r1354, %r1355}, [%rd10]` 从显存读取真实特征，而在越界 fallback 分支才由 `mov.b32 %r1352, {%rs2, %rs2}` 填入常数。上游漏检了向量加载的多重定义，把 `mma.sync` 的操作数替换成了越界常数，在平滑天空上直接打出 106 条周期性红绿横带。

### 2. 我们的三项核心改进（[`Development/ptx-patcher/build_sm86_dlls.py`](Development/ptx-patcher/build_sm86_dlls.py)）

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
   解析每个 PTX `.entry` 内所有指令的目的操作数（含 `{ %r1, %r2, %r3, %r4 }` 花括号向量加载、谓词指令与普通指令），一旦发现 `pack` 目标寄存器、FP8 中间寄存器或 FP16 源寄存器在函数内存在多重定义（如 `%r1352`），立即拒绝该 `mapped` 转发并回退到寄存器原地解包；真正单定义的本地 `mapped` 则保留 `shfl + shfl + selp` 零开销转发。修复后天空红绿变号从 **106 次降为 0 次**，高频色差 RMS 降低 **263 倍**。

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
  │    • mma.m16n8k32.e4m3 → 4-lane shuffle + 2 条 mma.m16n8k16.f16.f16.f16.f16 (Full Rate!)
  │    • cvt.f16x2.e4m3x2 → prmt.b32 + mul.rn.f16x2 0x5c005c00
  │    • cvt.e4m3x2.f16x2 → add.rn.f16x2 0x40004000 (次正规) + bfe.u32 (正规)
  │
  ├─ [Step 4] 多进程并行调用 libcuda.so.1 (cuModuleLoadDataEx, CU_JIT_OPTIMIZATION_LEVEL=4)
  │    • 15/15 个 Fatbin 全部以满血 O4 编译为 sm_86 ELF cubin
  │
  ├─ [Step 5] 调用 libzstd.so.1 (level 22) 压缩 cubin，封装回 Fatbin 槽位，尾部剩余字节填 0
  │
  └─ [Step 6] 修补 PE 导出函数中的 NGX 最低架构检查立即数 (0x120 → 0x80)，
              剥离失效的 Authenticode 证书表，重算并写入 PE Checksum
  │
  ▼
产出满血 O4 版 nvngx_dlssnr.dll (266,414,592 B, SHA256: 3f934a0a...)
```

### 4. 每个发布文件从哪来与编译命令

| 包里的核心文件 | 源码 / 工具位置 | 构建命令 |
|---|---|---|
| **`nvngx_dlssnr.dll`**（三个包共用，15/15 `O4` `sm_86` 修补版） | `Development/ptx-patcher/build_sm86_dlls.py` + `dlssnr_patcher.py` | `python3 Development/ptx-patcher/build_sm86_dlls.py --input /path/to/orig/nvngx_dlssnr.dll --output /path/to/out/nvngx_dlssnr.dll --workers 3` |
| **`nvngx.dll_dlssnr.dll`**（OptiScaler 两个包共用，NGX 调用名转发桥） | `Development/ptx-patcher/dlssnr_forwarder.cpp` | `x86_64-w64-mingw32-g++ -O2 -shared -static -o nvngx.dll_dlssnr.dll Development/ptx-patcher/dlssnr_forwarder.cpp` |
| **`Magpie.exe`**（Magpie 包专用，将原生 `DLSSNR` 硬编码的 `Preset 0` 改为 `Preset 2`） | `Development/ptx-patcher/magpie-native/patch_preset2.py` | `python3 Development/ptx-patcher/magpie-native/patch_preset2.py --input /path/to/orig/Magpie.exe --output /path/to/out/Magpie.exe` |
| **`bench.exe`**（独立 D3D12 NGX Feature 18 硬件计时测试台） | `Development/ptx-patcher/bench_nvngx.dll.cpp` | `x86_64-w64-mingw32-g++ -O3 -std=c++17 -static Development/ptx-patcher/bench_nvngx.dll.cpp -ld3d12 -ldxgi -o bench.exe` |
| 三个 `v0.1.0` 发布包组装与校验脚本 | `Development/ptx-patcher/release-rtx30/` 与 `magpie-native/deploy_release.py` | 见对应目录下的打包与 SHA256 校验脚本 |

单元测试与回归验证：
```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

---

## 实测性能对照（RTX 3080 Laptop GPU, 16GB, `sm_86`, 132W）

### 1. 三种技术方案同机同口径对比（均为 31 块 `0.5x Small` 模型，`Preset 2`）

| 方案 | 编译器优化 | `1280×720` (720p) | `1600×900` (900p) | `1920×1080` (1080p) | 天空渐变红绿变号 | 相对上游提速 |
|---|:---:|---:|---:|---:|---:|:---:|
| ① 网上 `dlssnr-patcher` 原版位运算 (`stock`) | 主网络被迫回退 `O1` | `37.13 ms` | `49.89 ms` | `67.69 ms` | `106 次`（有色带） | `1.00×` |
| ② 独立 CUDA 引擎（`Development/hip-port`） | `Clang O3 + PTX O4` | `~31.0 ms` | `43.10 ms` | `57.13 ms` | 无 | `1.18×` |
| **③ 本项目 `ptx-patcher` (`v0.1.0`)** | **15/15 全部满血 `O4`** | **`15.83 ms`** | **`24.47 ms`** | **`32.04 ms`** | **`0 次`（彻底消除）** | **`2.08× ～ 2.35×`** |

> **为什么路线 ③（改写原版 PTX）比路线 ②（从 RDNA4 移植的独立引擎）快 1.8 倍？**  
> 在消费级 GeForce RTX 30 系（GA102/GA104）硬件上，老黄将 **FP32 累加 Tensor Core（`.f32.f16.f16.f32`，路线 ② 所用）硬件吞吐砍半为 Half Rate（256 FLOPs/clock/SM）**，而 **FP16 累加 Tensor Core（`.f16.f16.f16.f16`，原版 PTX 路线 ③ 所用）保持 Full Rate（512 FLOPs/clock/SM）** 且寄存器占用减半。

### 2. 游戏与窗口实机表现

| 游戏 / 场景 | 接入包 | 渲染分辨率 → 输出分辨率 | DLSS 5 模型 GPU 耗时 | 实机表现 |
|---|---|---|---|---|
| **《鬼武者：剑之道》** | `OptiScaler-REFramework` | `854×480` → `2560×1440` (2K Ultra Perf) | **`7.3 ～ 9.1 ms`** | 整机实玩 **46 FPS** |
| **《鬼武者：剑之道》** | `OptiScaler-REFramework` | `1280×720` → `2560×1440` / `3840×2160` | **`16.7 ～ 17.5 ms`** | 整机实玩 **30 FPS**，4K 天空平滑无色带 |
| **《剑星》(Stellar Blade)** | `OptiScaler`（常规包） | `1279×720` → `3840×2160` (4K) | **`18.1 ～ 18.6 ms`** | DLSS 与 FSR 输入自动转接均正常，单遍增强（`1.5 / 1.1`）生效 |
| **《光环》(Halo) 窗口化** | `Magpie`（便携包） | `1280×720` → `3840×2160` (4K) | **`15.87 ～ 16.00 ms`**（旧路线 A 为 `49.8 ms`） | 含后级 4K `DLSS_SR` 总 GPU 耗时 **`21.2 ms`**，60Hz 电视同步下稳定 **30.5 FPS**（动画窗口无锁频下 **36 FPS**） |

---

## 更新记录

每一版的详细改动（改了什么、效果、文件 SHA256、实验目录）见 [CHANGELOG.zh-CN.md](CHANGELOG.zh-CN.md)。

| 版本 | 日期 | 做了什么 | 结果 |
|---|---|---|---|
| **`0.1.0`** | 2026-10-24 | **首发版本（三个发布包全线统一为 15/15 满血 `O4` PTX 路线，仅保留 31 块 `0.5x Small` 新模型）**：<br>1. **PTX 满血 `O4` 编译器（`Development/ptx-patcher/`）**：提出两条 IEEE 754 `f16x2` 硬件代数恒等式（`mul.rn.f16x2 0x5c005c00` 解包 E4M3、`add.rn.f16x2 0x40004000` 舍入 E4M3 次正规数，有限值域 `0 bit-diff`），将 `.cubin` 体积缩小 3.5 倍，15/15 个 Fatbin 全部 `O4` 装回原槽位；修复 `310.9.16.0` 的 `fence.acquire.gpu;` 编译失败。<br>2. **消除天空红绿横带（`sky-audit/`）**：定位并修复上游 `fp8_pack_sources` 未扫描花括号向量加载（如 `FB5 %r1352`）导致将显存特征误替换为越界 fallback 常数的致命 Bug，天空逐行红绿色差变号从 `106 次` 降为 `0 次`，高频色差 RMS 降低 263 倍。<br>3. **三包构建与游戏适配**：<br>  • `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip`（SHA256 `8e28417d...`）：适配《鬼武者：剑之道》等 RE Engine 游戏，校准 `WhitePointSource=1`（`~512x` 原生曝光）；<br>  • `OptiScaler-DLSS5-RTX30-0.1.0.zip`（SHA256 `e6067bf0...`）：适配《剑星》等常规 DX12 游戏，配齐完整 FFX 转发库（支持游戏内选 FSR 或 DLSS 自动转接），默认应用单遍增强（`detail=1.5, colour=1.1`）；<br>  • `Magpie-DLSS5-RTX30-0.1.0.zip`（SHA256 `db41eaeb...`）：打通 `Magpie.exe` 原生 `DLSSNR` Feature 18 后端，通过二进制补丁将写死的 `Preset 0` 改为 `Preset 2`（31 块轻量模型），补齐 `nvngx_dlss.dll` 修复 `0xbad0000b` 报错，移除旧 ReShade/add-on 与外置碎权重，720p 模型耗时从路线 A 的 `49.8 ms` 降至 **`15.9 ms`**。<br>4. **附加路线归档（`Development/hip-port/`）**：完整保留从 AMD RDNA4 移植的 40 模块（1,970 个核入口）CUDA 独立引擎源码（V6 全激活预洗牌 + 32/32 核零 `LMem` 溢出，900p `43.1 ms`），作为研究与扩展路线。 | 测试台 720p **`15.83 ms`**、900p **`24.47 ms`**、1080p **`32.04 ms`**（比上游 `O1` 快 **2.08×～2.35×**）；《鬼武者》《剑星》《光环》实机验收通过 |

---

## 仓库目录结构

| 目录 / 文件 | 内容 |
|---|---|
| `Development/ptx-patcher/` | **当前主推路线**：原版 `310.9.16.0` `nvngx_dlssnr.dll` 的 `sm_86` 满血 `O4` PTX 转换器（`build_sm86_dlls.py`、`dlssnr_patcher.py`）、NGX 调用转发桥（`dlssnr_forwarder.cpp`）、硬件计时测试台（`bench_nvngx.dll.cpp`）、天空色带排查回执（`sky-audit/`）、Magpie 原生 `Preset 2` 补丁（`magpie-native/`）及三包构建脚本（`release-rtx30/`） |
| `Development/hip-port/` | **附加/实验路线**：从 AMD RDNA4 (`gfx1201`) 全栈移植到 Ampere `sm_86` 的独立 HIP/CUDA 推理引擎（40 个内核模块、`hip/sm86_compat.h`、V6 SSA 编译器优化管线 `hip/build_sm86_modules.py`、`LmxxfNrRuntime.dll` 与 `dlss5-amd.addon64` 源码） |
| `Development/DevHistory.md` | 完整的开发流水账、对照实验数据、失败排查与每个阶段的文件 SHA256 回执 |
| `Development/WorkingPlan.md` | 当前架构路线分工与后续工作计划 |
| `CHANGELOG.zh-CN.md` / `CHANGELOG.md` | 按版本展开的详细更新日志 |

---

## 作者与许可

- **作者**：Kien —— 方向、游戏接入、实机测试与架构决策；逆向、PTX/CUDA 核优化与打包自动化由 AI 协作者（朱雀 / Claude / Gemini / GPT）共同完成。完整技术故事见[公众号 DLSS5 系列合集](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzYzMzMwNzk0NA==&action=getalbum&album_id=4687269655390453762#wechat_redirect)。
- **许可**：本仓库代码以 [MIT](LICENSE) 许可发布。NVIDIA 的二进制文件与模型权重不在本仓库分发之列。
