# DLSS5 RTX 3080 Laptop — v0.1.0

在 NVIDIA GeForce RTX 3080 Laptop（Ampere `sm_86`）上运行 **31 块新版 Small NR 模型**。当前主线是 [Development/ptx-patcher](Development/ptx-patcher)：改写原版 **310.9.16.0 `nvngx_dlssnr.dll`** 内置 PTX，15/15 个 Fatbin 保持 **O4** 并装回原槽位。v0.1.0 的三个发布包均使用这条路线，包括 Magpie 的原生 Feature 18 后端。

[English](README.md) · [工作计划](Development/WorkingPlan.md) · [开发记录与实验条件](Development/DevHistory.md)

## 核心改动

### 用 FP16 硬件实现 FP8 转换

RTX 30 系不能直接执行此模型 PTX 中的 E4M3 转换与 FP8 MMA。上游整数展开会增大代码，部分主网络 Fatbin 只能降到 O1。本项目把转换压缩到 IEEE 754 `f16x2` 运算，并将 FP8 `m16n8k32` 分解为两次 FP16 `m16n8k16`。

1. **E4M3 → FP16：位重排后乘 256。** 把 E4M3 的符号、指数和尾数放进 FP16 对应位置，先形成指数偏低的 FP16 值，再用 `mul.rn.f16x2` 同时乘上两个 `256`（常量 `0x5c005c00`）。FP16 硬件会归一化次正规数；这不是近似查表。
2. **FP16 → E4M3：借 FP16 加法完成次正规数 RNE 舍入。** `2.0h` 的间距为 `2^-9`，恰好等于 E4M3 次正规网格。对该范围的绝对值做 `add.rn.f16x2` 加 `2.0h`（`0x40004000`），便得到所需的向最近偶数舍入。普通数另走紧凑位打包，保留符号与有限值饱和。

转换辅助函数在已覆盖的有限值域达到 **0 bit-diff**：254 个有限 E4M3 编码；FP16 往返转换的 GPU 双通道穷举各覆盖 63,488 个有限编码，均零差异。见 [转换检查](Development/ptx-patcher/sky-audit/existing-roundtrip-gpu.txt)。这不是“整个模型与原厂或上游输出逐位一致”的声明；NaN payload 也不在这项有限值证明内。

### 修复错误的 mapped 转发

上游 `fp8_pack_sources` 只数特定 `cvt`/`pack` 出现次数。例如 FB5 的 `%r1352` 同时由真实显存的向量加载和越界分支的 fallback pack 定义，却被错误转发成 fallback 来源，天空因此出现密集红绿横带。

当前默认统计整个 entry 中的寄存器定义，识别标量、花括号向量目的操作数与内联指令，拒绝 pack 目标、FP8 中间值或 FP16 来源存在多定义的 mapped。单定义跨块转发保留，避免不必要的重复转换。通过检查后沿用原来的 `shfl + shfl + selp`，**不额外量化**。

同一 1280×720 平滑天空测试，逐行红绿色差从 **106 次变号降到 0 次**，高频 RMS 约 `0.0001027`；《鬼武者》和《剑星》随后获得用户实机验收。106 是变号次数，不是完整周期数。严格同块检查与显式量化保留为较慢的诊断选项；默认过滤不等于完整 CFG 支配性证明。见 [控制实验](Development/ptx-patcher/sky-audit/去量化控制变量回执.md)。

## v0.1.0 三个发布包

工程版本从 **0.1.0** 起算；AMD 上游底包的 **0.44** 仅表示来源。发行 ZIP、运行库和模型不提交到 Git，单独分发；包内有 `README.txt`、英文说明、逐文件 `SHA256SUMS.txt`，ZIP 旁有 `.sha256`。

| 包名 | 场景 | 默认处理链 |
|---|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip` | 《鬼武者：剑之道》《生化9》等 RE Engine 游戏 | NR → DLSS SR；含 REFramework `dinput8.dll` |
| `OptiScaler-DLSS5-RTX30-0.1.0.zip` | 《剑星》等常规 DX12 游戏 | DLSS/FFX 输入 → NR → DLSS SR；不含 REFramework |
| `Magpie-DLSS5-RTX30-0.1.0.zip` | 游戏窗口、无游戏内接入的窗口捕获 | Magpie 原生 DLSSNR → DLSS_SR；无 ReShade/add-on |

### REFramework 包

1. 退出游戏，备份同名 mod 文件，把**全部文件**解压到真正游戏 EXE 所在目录。Xbox 版《鬼武者》示例：`C:\XboxGames\Onimusha- Way of the Sword\Content\`。
2. 保留包内 `dinput8.dll`、26 MB 新版 `dxgi.dll`、`nvngx.dll_dlssnr.dll`、修复版 `nvngx_dlssnr.dll` 和辅助 DLL，不混拷旧独立引擎。
3. 默认 `Preset=2`、`Style=1`、单遍，细节/色彩均为 `1.0`。`WhitePointSource=1`、`WhitePointTrim=1` 使用游戏曝光。F6 切换 NR，Insert 打开 OptiScaler。

### 常规 OptiScaler 包

《剑星》解压位置为 `SB\Binaries\Win64\`，即 `SB-Win64-Shipping.exe` 所在目录。**先备份原版 `amd_fidelityfx_dx12.dll`，再复制完整包**：26 KB FFX loader 必须与约 28 MB upscaler、XeSS/NvAPI 辅助库和 `D3D12_Optiscaler` 配套，不能只拷四个文件。

- `Dx12Upscaler=dlss` 指输出后端；`EnableFfxInputs=true`、`UseFfxInputs=true` 和 FSR2/3 输入开启，`EnableHotSwapping=false` 固定输出路线。游戏需有可用的原生 DLSS SR 库与 NVIDIA NGX 驱动。
- 《剑星》完整包已获用户验收；另有实际 Windows FFX→NGX→NR 分发 smoke。具体游戏是否接管 FSR，以日志出现 `reached through the game's FFX input` 和 NR composition 为准。
- 默认细节 `1.5`、色彩 `1.1`，仍是单遍；`OptiScaler-原始平衡.ini` 可恢复 `1.0/1.0`。F6 对比时保持同一场景和质量档位。
- 4K 输出不等于 4K 渲染：FFX 查询实测 Quality 为 2560×1440，Performance 为 1920×1080，Ultra Performance 仅 1280×720。先选 Quality 看清晰度，再按性能取舍。

《剑星》配对白点约 `1x`，《鬼武者》约 `520x`，来源是 `pre-exposure / game exposure`，不是效果强度。不要互抄这两个数。

### Magpie 包：原生 PTX，已替换旧 CUDA 默认路线

退出其它 Magpie 实例，解压并直接运行包内 `Magpie.exe`，选择默认 **DLSS5-RTX30-PTX**，在目标游戏窗口前台启动“3 秒后缩放”。

- 原生 `DLSSNR\DLSSNR_AI_Filter`：Preset 2、Style 1、同尺寸 NR；再由 `DLSS\DLSS_SR` 输出到屏幕。实测为 1280×720 → 3840×2160。
- 包含 `nvngx_dlssnr.dll` 和原生 SR 的 `nvngx_dlss.dll`；不含 ReShade `dxgi.dll`、`dlss5-amd.addon64` 或 `DLSS5-AMD/` 外置权重。旧包请先清掉这些残留，不能只覆盖新文件。
- 定制 Magpie 0.6.6 原本**写死 Preset 0**，JSON 无法指定 2。包内 EXE 使用哈希门控的最小补丁，只改该参数 Set 调用及对应状态文字；自动更新关闭，避免覆盖。见 [补丁脚本](Development/ptx-patcher/magpie-native/patch_preset2.py) 和 [补丁清单](Development/ptx-patcher/magpie-native/preset2-patch.json)。
- 原生后端内置 signed-snippet/caller IAT 兼容。比较请使用 Magpie 自带工具；旧 add-on 的 F6 开关不再适用。切换任务会结束全屏缩放。
- 当前默认链不使用 FSR4 或 XeSSFG。缺少 SR 库曾复现 `0xbad0000b`，补齐后 D3D11 创建与实际窗口链路均成功。

## 实测数据与口径

机器：Windows 11，RTX 3080 Laptop 16 GB（GA104、48 SM、`sm_86`），高性能档约 132 W；记录中的 NVIDIA 驱动为 616.92。未逐卡验收整个 RTX 30 系。

### 上游 O1 与紧凑 O4 的历史同机对照

相同 31 块模型、Preset 2，D3D12 timestamp，最低 GPU 耗时：

| 方案 | 1600×900 | 1920×1080 |
|---|---:|---:|
| 上游整数展开、主网络回落 O1 | 49.89 ms | 67.69 ms |
| 紧凑转换、15/15 O4 | 23.97 ms | 29.97 ms |
| 相对提速 | **2.08×** | **2.25×** |

这是较早阶段的性能对照；当时两边共享错误 mapped，不能用彼此 `0 bit-diff` 证明正确性。修复后的 v0.1.0 后续复核，5 帧预热/20 帧测量，GPU median 为 **15.829 ms（720p 天空）、24.474 ms（900p 原 bench 场景）、32.036 ms（1080p 原 bench 场景）**，仍为 15/15 O4 原槽位。

### 游戏与实际窗口

| 场景 | 实测结果 | 边界 |
|---|---|---|
| 《鬼武者》2K 显示、内部 480p | NR 7.3～9.1 ms，游戏约 46 FPS | 早期集成记录 |
| 《鬼武者》2K 显示、内部 720p | NR 16.7～17.7 ms，游戏约 30 FPS | 早期集成记录 |
| 《鬼武者》4K 显示、内部 720p | 当前日志示例：NR 模型 17.24～17.35 ms，总计 17.51～17.68 ms；用户确认天空色带消失 | 没有另录该次整机 FPS |
| 《剑星》4K 显示、内部约 720p | 当前日志示例：模型 18.18～18.62 ms，总计 18.42～18.86 ms；用户确认完整包正常 | 没有记录整机 FPS；另有 1080p 渲染档 |
| Magpie《光环》720p→4K，旧独立引擎 | 回调间隔中位 49.8 ms，约 20 FPS，31 块/1344×768 处理面 | 用户游戏实际记录，非纯模型 GPU 时间 |
| Magpie **原生 PTX**，720p 动画窗口→4K | NR GPU 窗口均值 **15.868～16.199 ms**；960 次成功、0 失败 | 含后级 SR/同步的 fence 约 21.1～21.5 ms，完整窗口评估约 36 FPS |

**15.9 ms 是原生 Magpie NR 的 GPU 时间，不是《光环》整机 40+ FPS 验收。** 原生路线已正式部署；性能记录中的动画窗口和《光环》不是同帧同负载 A/B。详见 [原生回执](Development/ptx-patcher/magpie-native/测试回执.txt) 与 [日志](Development/ptx-patcher/magpie-native/evidence/magpie.log)。

## 从源码构建与检查

PTX 构建需要 Python 3、NumPy、`libzstd.so.1`，以及 WSL 中可用的 NVIDIA CUDA Driver API/JIT（当前脚本使用 `/usr/lib/wsl/lib/libcuda.so.1`）。不需要 HIP 资产或外置模型权重。

只接受原版 310.9.16.0 输入 SHA256：
`2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f`

```bash
python3 Development/ptx-patcher/build_sm86_dlls.py --input /path/to/original/nvngx_dlssnr.dll --output /path/to/output/nvngx_dlssnr.dll --workers 3
```

默认多定义过滤、无额外 mapped 量化。`--mapped-mode strict` 要求本块来源；`--mapped-mode strict --quantize-mapped` 用于精确量化对照，较慢。构建器保留超槽位时新增 PE 节的能力，但**当前发布 DLL 不需要扩节**。

已知 Magpie EXE 的 Preset 2 补丁：

```bash
python3 Development/ptx-patcher/magpie-native/patch_preset2.py --input /path/to/original/Magpie.exe --output /path/to/output/Magpie.exe
```

输入 EXE 必须匹配补丁清单原 SHA，输出也有固定 SHA；其它 Magpie 版本拒绝套用。

```bash
python3 -m unittest discover -s Development/ptx-patcher -p test_mapped_safety.py -v
```

[发布脚本与回执](Development/ptx-patcher/release-rtx30/) 使用本机外部底包/运行库路径；运行前按自己的目录调整。`sky-audit`、`magpie-fix` 保留阶段实验与失败记录，不把每个旧诊断脚本当成生产入口。

## 包与核心文件校验

| 文件 | SHA256 |
|---|---|
| `OptiScaler-REFramework-DLSS5-RTX30-0.1.0.zip` | `8e28417d2420f11dd3e90044fadad78f3d1c53fbec1ebeb791acb62703285f67` |
| `OptiScaler-DLSS5-RTX30-0.1.0.zip` | `e6067bf09cf5e13ed010d5c90deff695302bbe39b631d7b7fe743ad7b502caac` |
| `Magpie-DLSS5-RTX30-0.1.0.zip` | `db41eaeb406622678dd4f79cc0f5204c13d9a719ea0b0d34f066f173507b5ffb` |
| 修复版 `nvngx_dlssnr.dll` | `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a` |
| Preset 2 `Magpie.exe` | `b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea` |

## 目录

`Development/` 仅保留 `DevHistory.md`、`WorkingPlan.md`、`ptx-patcher/`、`hip-port/`。

主线代码、发布脚本、天空排查、Magpie 原生适配和历史修复证据均在 `Development/ptx-patcher/` 下。

## 附加/实验路线（Additional Route）

[Development/hip-port](Development/hip-port) 保留 RDNA4 Wave32→Ampere 的独立 HIP/CUDA 引擎移植：40 个模块、1,970 个入口、D3D12/CUDA 共享资源桥接。它用于源码研究与无原生 NR 后端的接入实验，**不是 v0.1.0 三个发布包的默认路线**。历史代码仍有旧模型支持，当前发布仅启用 31 块 Small。
