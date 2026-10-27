# PTX V2.2：SWAR 双通道量化 + 原生异步 barrier

推荐 **组合版**，以 V2.1 hot255 为唯一基线，不改图、权重、mapped 条件、偶奇 K16 次序或寄存器上限。hip-port 收官，本轮全部为路线 B。

| 分辨率 / 输入 | 配对 V2.1 | V2.2 | 耗时下降 |
|---|---:|---:|---:|
| 1280×720 sky | 6.7390 ms | 6.2485 ms | 7.28% |
| 1600×900 scene | 9.7835 ms | 9.1223 ms | 6.76% |
| 1920×1080 scene | 12.7797 ms | 11.8595 ms | 7.20% |

每个因子每档正向 ABBA / 反向 BAAB，50 warmup / 80 iter；表为四次进程 GPU median 的均值，min 与逐轮数据见 [完整单因素表](results.md)、[72 次原始结果](bench.json)。默认 DVFS，没有锁频。SWAR 单因素三档均胜出；异步单因素 720p 慢约 0.48%，900p/1080p 快约 0.63%/1.14%，不单独推荐。组合版对配对基线的正反轮均胜出。

- **量化**：8,944 处旧展开每处 29 条 PTX（8 b32＋2 pred），改为 20 条（5 b32、0 pred，含 3 次常数装载）。双通道 abs/min 448、RN 偏置、half2 阈值 mask＋lop3 选择，再合入符号和一次 PRMT。GPU 测试 33,554,432 组双通道，所有 65,536 种 half 位型各与 256 种对侧位型配对并交换位置；63,488 种有限值及所测非有限组合与旧代码均 0 差异。[原语回执](pack-test.json)
- **异步**：316 处 bulk（104/208/4）改为 `cp.async.mbarrier.arrive.shared::cta.b64` 绑定各自 barrier，替换当场 commit/wait。原始 barrier 为 CTA 线程数初始化，每线程 arrive 1；用默认增计数的绑定使异步 arrival 自行配平，**不能直接使用 `.noinc`**。不改原 arrive/test_wait、init、分支或双缓冲切换。[NVIDIA 语义](https://docs.nvidia.com/cuda/archive/12.0.1/parallel-thread-execution/index.html#parallel-synchronization-and-communication-instructions-cp-async-mbarrier-arrive)、[CFG 审计](async-audit.json)
- **控制流**：逐入口跟随分支和循环回边，bulk 到下一 arrive 的最短路径指令距离范围 FB04 3～273、FB05 4～841、FB06 4～86。CFG 保守地保留不可行分支，因此“可退出路径”不是动态提前退出证明；没有据此盲目一对一移动 wait。原生绑定直接跟踪实际拷贝目标，比全局延迟 wait 更准确。FB04 原有另 4 组普通 cp.async 等待保留。
- **完整图**：12 次 1/1 初验、72 次正式 50/80，候选各自与同配置 V2.1 RGB 严格 0 bit-diff、maxabs=0、PSNR=∞、nonfinite=0。天空变号均 0，正式天空高频 RMS 与 V2.1 同为约 0.000101989。初版脚本误把 1/1 与 50/80 的基线末帧比较，检测到时间帧差异后已分开 gold；该控制记录保留，不混入候选质量统计。
- **资源反例**：PTX 临时量减少不等于 O4 spill 减少！组合版 FB01 STACK 120→168 B、LDL+STL 315→462；FB02 0→8 B、0→2；FB04 80 B / 118 不变；FB05 8→16 B、12→18。其余 FB00/03/06～14 为 0 STACK。完整静态全导出数据见 [resources.json](resources.json)，不宣称零栈溢出。

推荐 DLL：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v22.dll`，**266,414,592 B**（254.07 MiB），15/15 原槽位 O4，无新增 PE 节。

SHA256：`2705462fc74ca20208ebb83c08cd0e75613ddc220a7834b1e80f4c9aeb0eb90f`。

复现：`python3 Development/ptx-patcher/v22/build_recommended.py`。独立推荐入口显式设置两个因子与 hot255；主构建器兼容默认仍可复现 V2/V2.1，新增因子必须显式指定输出路径。完整推荐重新编译与实测候选 SHA 相同，CUDA 加载 15/15 通过；既有 10 项回归通过。[验收](validation.json)

本轮不部署、不覆盖 fast.dll、不改发布 ZIP、不 push。V2.1/主 fast 与三个 v0.2.0 ZIP 保护性 SHA 均保持原值。临时 cubin/PTX、因素 DLL 与 RGB 输出由 [cleanup.py](cleanup.py) 清理，保留推荐 DLL、重建入口、日志、JSON 与摘要。
