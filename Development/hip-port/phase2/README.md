# Phase 2：静态权重预洗牌、ones 特化与 packed 分段累加

本轮仅构建独立 CUDA 引擎的实验候选；v0.1.0 PTX DLL、正式包和共享 assets 均未覆盖。

## 实现与数值边界

- Host `AmperePreshuffleTile256` 模拟 32 lane 的精确字节置换；`AmperePreshuffleTile512W16` 分别提取低/高 K16 片段进行置换后交织存回。`FragmentPackedMatrix/W16`、C32/MH residual diagonals、QKV Frag8 在最终打包后执行。float scale/bias/tail 不动。
- GPU 仅在对应的静态 fragment 读取处使用 `sm86_unpack_e4m3x8`；动态 Q/K/V、row-major fallback 保留原 prep。C32 的 W16、MH 的 Fragment、C512 W16、ViT expand/contract/project、decoder W16 与 QKV shared staging 在 `hip/phase2_transform.py` 中显式配对，未全局替换 generic FP8 intrinsic。
- `ones_a`：一个线程对应一个 B 列，合并两个 lane 的 K8 部分和，只需一次 XOR16 shuffle。**FP16 MMA 在前 K8 后已有一次半精度舍入**，因此使用 `half(sum_hi + half(sum_lo + half(c)))`，不能直接用 `half(sum16+c)`。
- `ones_b`：输出线程有八个不同 A 行的结果。精确保留上述两次舍入，需要分别广播八行的低/高 K8 部分和，共 **16 条 idx shuffle**。直接先合并成一行总和的 9-shuffle 候选会改变舍入，已否决；不声称通用 RDNA4 输出布局可用一条 shuffle 完成。
- 删除 `wmma(zero,zero,pre)`，其输入 pre 已由 FP16 MMA 返回 half 精度。
- `sm86_add_u4_f16x2` 使用四条 `add.rn.f16x2`。pool 跨 K32 chunk、ViT contract/stream project 与 decoder W16 跨 partition 保持 packed Ampere 累加器。pool 先前 H/RNE 链中的值均已是 half；四 partition 的 FP32 和改为逐 partition half 和则会改变舍入，整网精度需单独验收。

## 小测试

`python Development/hip-port/phase2/check_primitives.py` 会构建 C++ Host 置换测试和独立 CUDA probe，通过 CUDA Driver 在本机执行：

- 64 个 256B tile（含唯一字节标签），CPU 置换与 GPU preshuffle、原 GPU prep 与 unpack 的逐 bit 对照。
- 64 个 W16 tile 的 lo/hi 使用不同内容，分别与 256B 基准对照。
- 128 组 half 输入和非零 C，含整数、正负随机、非负随机，连续四次 ones 累加，与原 FP16 MMA 逐 bit 对照。
- 4096 个线程片段的 packed add，对照 FP32 加法后 RNE half 打包。

原始结果见 `primitive-results.json`、`primitives.log`。零差异仅针对这些测试，不扩展为所有非有限值/任意溢出状态的断言。

## 构建与 Host 配对

`hip/build_sm86_modules.py` 先展开预处理分支，再对有效 C++ 结构改写；缓存键包括原始源、兼容头、构建器和 Phase 2 pass 内容。40 模块全部成功后生成 `AMPERE_WEIGHTS_V2`。

Host 和模块是一个布局 ABI：新模块必须搭配预洗牌权重；新 Host 默认开启，可用 `DLSS5_AMPERE_WEIGHTS=0` 对照旧模块。Network 初始化检查目录 marker 与该开关一致，防止误配旧模块产生无声画面错误。此实验没有修改磁盘上的模型权重；转换发生在 Host 加载/上传前。

本次重新编译的是 Linux CUDA benchmark runner（同一 RTX 3080 Laptop 经 WSL CUDA Driver 执行），没有部署或重建游戏用 `frame.exe`。产物与完整输出留在被忽略的 `artifacts/` 中。

基准使用 Small 31-block、Style 1、既有确定性 RGB 输入；1080p/900p 的实际处理尺寸为 1920×1152 / 1600×1024。整网 GPU events 与额外核级插桩帧分别报告，精度同时统计 padded 区域和可见区域，PSNR peak=1。

## 最终结果（50 warmup / 80 iterations）

同轮重新测量 Phase 1，与旧记录的频率/温度变化分开：

| 档位 | Phase 1 GPU min / median | Phase 2 GPU min / median | 速度比 | Phase 2 Wall median | 对 F32 可见区域 PSNR / maxabs |
|---|---:|---:|---:|---:|---:|
| 900p | 44.461 / 44.872 ms | 41.743 / 42.264 ms | 1.0617× | 42.360 ms | 46.6206 dB / 0.03485873 |
| 1080p | 59.245 / 59.806 ms | 53.921 / 54.476 ms | 1.0978× | 54.585 ms | 46.1009 dB / 0.04160273 |

两档 invalid=0、首末帧 bit_diff=0。完整 padded 区域 PSNR 为 46.5919 / 46.0816 dB。GPU 与 CPU Wall 都不含初始化、权重打包、输入上传及最终输出读回。

额外插桩帧累计：900p 43.9020→41.6553 ms（34 核），1080p 58.8165→53.6494 ms（32 核）。完整 [32/34 核对照表](results.md) 和 [机器可读数据](results.json) 已保存。

1080p pool 四核均为 111 regs：三个核从 200 regs / OccW8 恢复到 111 / OccW16；C512 的 104B LMem 消除，恢复 32/32 零 LMem（900p 34/34）。仍有回退：wave2 多核达到 250 regs、OccW仍8；compact contract 154→217 regs、OccW12→8；C512 attention/split projection 的 OccW16→12。寄存器下降 14 核、上升 15 核、持平3核，不能概括成“全网寄存器下降”。

功耗/频率使用默认 DVFS，未锁频；高利用率样本功耗中位数137.77W、SM1695MHz、显存7001MHz，完整遥测在 `telemetry.csv`。本轮没有单独隔离三项改动的端到端贡献。代表性 PTX 静态指令计数在 `ptx-instruction-counts.json`（不是动态执行次数或 SASS pipe 利用率）：C128 pool 的 shfl 136→40、selp 813→381；C32 prefix 的 shfl 385→337、MMA96→76；QKV因精确 ones_b 需要广播，其总 shfl 数没有下降，但静态权重 staging 已改为 unpack。

复测入口：`bash Development/hip-port/phase2/run_benchmark.sh`（默认50/80，可传两个数改变预热/测量帧数）。依赖 Phase 1 原始模块与 F32 输出档案；所有二进制和 RGB dump 均在忽略的 `artifacts/` 内。最终40模块构建日志为 `build.log`；三个 `build-*-attempt.log` 保留了预处理与改写器修复过程中的失败记录，不计作最终通过结果。

最终四个长负载段的 SM 时钟中位数：Phase1 1080p/900p=1695/1695MHz，Phase2=1695/1710MHz；对应功耗中位数136.88/139.28W与137.68/138.37W。900p包含约0.9%的Boost时钟差异，不能把全部速度差严格归因于等频指令优化。分段数据见 `telemetry-load-segments.json`。构建缓存复查40/40通过，记录在 `build-cache-check.log`。
