# PTX V2.3：真实发射账本与 8 条 FP8 解包

以 V2.2 为唯一基线，推荐 **PRMT8 解包版**。同步消融版本不入默认，mapped 条件不变，外部生产部署/发布包不动。

## 实际走 NVAPI，82 次发射、40 个核名

`bench_sky.exe` 对应的 D3D12 路径调用 `NvAPI_D3D12_CreateCuModule / CreateCuFunction / LaunchCuKernelChain`，不是公开 `nvcuda!cuLaunchKernel`。[NVIDIA 接口定义](https://github.com/NVIDIA/nvapi/blob/main/nvapi.h) 与 [QueryInterface ID 表](https://github.com/NVIDIA/nvapi/blob/main/nvapi_interface.h) 对应本轮拦截的结构和入口。先前普通 CUDA 导出拦截为空；改为 MinHook 拦截 `nvapi_QueryInterface` 返回的三个接口，取真实核名、Grid、Block、动态 Shared。**稳态每帧 82 次，每次链只有一个核**，无需拆链。83 的初计包含一次初始化空链探测。

独立诊断 runner 在原调用前后插 D3D12 硬件 timestamp，50 warmup / 20 iter；trace-only 对照保留相同调用序列而不插逐核时间戳。两种捕获输出逐位相同。下表是 **20 帧逐 FB 累加时间的均值**，可相加；完整账本另给逐调用/逐 FB median，二者不可混加。

| FB | 720p mean ms | 1080p mean ms |
|---|---:|---:|
| 00 C32 | 1.86593 | 4.26317 |
| 01 C64 | 0.53842 | 1.17612 |
| 02 C128 | 0.46807 | 0.98586 |
| 03 C256 | 0.50033 | 1.11677 |
| 04 C512 | 0.63416 | 0.92662 |
| 05 ViT | 1.99562 | 3.13231 |
| 06 转接 | 0.03354 | 0.04413 |
| 13 辅助 | 0.05663 | 0.12662 |
| 14 辅助 | 0.03436 | 0.08909 |
| **核区间合计** | **6.12705** | **11.86068** |

FB07～12 未发射。FB13/14 总共仅约 0.091/0.216ms。实测核间间隙 median 约 **0.0215/0.0241ms**，不能把数毫秒差额归因于 82 次启动间隙。逐核区间包含该核的等待/dispatch-local 成本；时间戳本身会扰动调度和重叠，**不是无扰动 stall 计数器**。正式提速结论只使用未插桩 `bench_sky.exe` 的配对 ABBA。

[720p/1080p 全部调用、Grid/Block 与耗时](kernel-ledger.md) · [JSON](profile.json) · [V2.3 诊断对照](profile-comparison.md)

## 720p 为什么相对更差

- **FB04/05/06 弱缩放是主要观测结果**：按像素比 1080p/720p=2.25 取线性参照，720p 核合计比 `1080p/2.25` 多约 **0.856ms**；其中 FB04～06 的同类差额约 **0.840ms**。这是同轮账本的缩放分解，不是可直接收回的时间预算，也未消除 DVFS 差别。
- ViT expand/contract/QKV/projection 的 Grid 从 **96 CTA → 160 CTA**（4 warp/CTA），attention 从 **64 → 96 CTA**；没有按像素比 2.25 缩放。720p 在 48 SM 上只有约 1.33～2 个 CTA/SM 的总工作量；再叠加 204～255 regs、Shared 和依赖链，吞吐利用率受限。这里有尺寸取整和小 Grid，不是把 ViT 当作严格固定时间。
- 第一层 C32 实际 Grid：720p **168×96**、1080p **240×144**（32 线程/CTA），对应 8×8 窗口覆盖约 1344×768 / 1920×1152；输入可见像素仍为 1280×720 / 1920×1080。边界扩张/取整 CTA 不应漏出工作量账本。
- 真实活跃 prefix/post 的 SASS HMMA 是 **528 / 580**，不是拿普通 C32 核的 512 统一替代。原 Roofline 文档的静态平均辅助指令比也还不是动态、按真实分支/循环/发射加权的读数；“70% 重叠”是建模假设。故 **3.54/5.92/8.33ms 可作优化参照，但本轮没有把 2.7～3.5ms 差额精确认定为某类 stall 或可回收浪费**。精确的 INT/LSU/scoreboard/occupancy stall 拆分仍需硬件性能计数器。

## tilesync / wait / chained：实际存在，不能直接删除

活跃 40 个核名中，10 个含 tilesync、11 个含 wait、11 个含 chained（这些命名分类不覆盖所有核，也不代表整段耗时都是同步）。按帧有 10/11/52 次对应发射。

做了两个隔离诊断，均基于 V2.2，不与解包候选混合：

1. **ready-flag 绕过＋移除 GPU fence**：只将匹配 `ld.relaxed...s32` 后 `setp.gt ..., -1` 的就绪轮询读替换为 0，移除 `fence.acq_rel.gpu`，保留 math、发布 stores/atomics、mbarrier 和 bar.sync。720p 可能降到约 5.63ms，但输出 PSNR 仅 **15.0～16.4dB**；1080p 仅 **23.2～24.4dB**，且无可靠提速。**不合格，不能用其时间差定量声称可删除同步；并发依赖确实影响结果。**
2. **仅去掉 nanosleep**：轮询、fence 和全部同步语义保留，50/20 ABBA。720p **6.1515→6.1520ms**，1080p **11.6585→11.6695ms**；输出全 0bit，无净收益，不保留。没有证据证明休眠本身吃掉数毫秒；也不能由此宣称动态自旋次数为零。

[破坏性消融](sync-probe-bench.json) · [仅去休眠](nosleep-probe-bench.json) · [构建/匹配范围](build_sync_probe.py)

## 真正保留的修改：10 → 8 条解包

`prmt 0xa280 / 0xb391` 将每个字节及其符号复制到对应 half 槽；`and 0x017f017f` 留 7-bit 幅值与 bit8 符号，左移7后乘原 scale。每对两条 PRMT，各配 mask/shift/HMUL2，共8条，保持偶奇K次序与2条MMA顺序，不改算术值。GPU **33,554,432** 组对照，完整穷举两种 parity 的 65,536 字节对并遍历干扰字节，含非有限编码，0bit。[原语](decode-test.json)

SASS 也确实变短，而不是只缩 PTX：prefix **5456→5352**、post **5511→5407**、ViT expand **3289→3225**、contract **4194→4074**；HMMA 数不变，PRMT 数增加。完整 [SASS 审计](sass-audit.json)。全导出 STACK 仍未清零：FB01 **168→192B**、FB04 **80→96B**，FB02 **8→0B**，FB05 **16B 不变**。实际活跃 C64 四核 spill 增加；活跃 C512 QKV 仍80B。[资源](resources.json)

mapped 审计按**真实活跃核名、静态逐 MMA 操作数使用次数**计：39,312 次中 13,600 已转发、25,552 为其他编码源，只有 **160 次**直接因为 pack_multidef 回退（两个 C32 wait 核各64、ViT attention 32）。它们不是已证明安全的160处机会，需 CFG 支配和 FP8 量化语义证明；本轮不因寄存器名相同就放宽。大部分编码输入是权重/外部特征，不是过滤器拒绝的安全 mapped。[审计](mapped-sync-audit.json)

## 推荐与验收

三档正反 ABBA/BAAB 50/80；1080p 首轮一方向有异常慢样本，因此补一整组正反确认，全部保留，不删样本。

| 分辨率 | 配对 V2.2 | V2.3 | 耗时下降 |
|---|---:|---:|---:|
| 720p sky | 6.24950 ms | **6.12575 ms** | 1.98% |
| 900p scene | 9.12125 ms | **8.92525 ms** | 2.15% |
| 1080p scene（原轮＋确认） | 11.80575 ms | **11.68200 ms** | 1.05% |

确认轮单独为 11.73375→11.55650ms；原轮为11.87775→11.80750ms，详见 [完整配对表](results.md)。6次快验＋32次正式输出均相对同配置V2.2 **0bit/maxabs0/PSNR∞/invalid0**。诊断采样与正式计时分开，晚段遥测不冒充全程覆盖。

推荐 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v23.dll`，**266,414,592B，15/15 O4 原槽位**。

SHA256：`b9c463beec6aba945beb2ce31aa96edd52fbae2933cb72cdb6f394b52bda9ca6`。

复现：`python3 Development/ptx-patcher/v23/build_recommended.py`。保留兼容构建默认，推荐入口显式 `--fp8-decode prmt8`；15核全量重建SHA一致。剖析入口 `build_profile.py` 使用固定提交 MinHook（许可证随附），交叉编译独立 `bench_profile.exe`；`run_profile.py events` / `trace` 跑原V2.2。原始CUDA导出钩子排查结果不作为“没有CUDA计算”的证据。

更新两份工程文档、清理临时DLL/RGB/PTX/cubin，只保留推荐DLL和文本证据；不部署、不覆盖fast/ZIP、不push。验收与清理清单分别见 `validation.json` / `cleanup.json`。
