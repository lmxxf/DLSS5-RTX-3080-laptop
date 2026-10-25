# Phase 5：packed Benes 与零重算寄存器Q

以Phase4 selected为基线，先只测C/D网络，再测Q缓存与约束，最终保留：

1. `__sm86_c_to_ampere` / `__sm86_d_to_rdna4` 使用4-u32半精度Benes网络。
2. 已测的 `c32-wave1-fast` 家族：非up核采用寄存器Q和8KB共享内存，并设置 `launch_bounds(32,9)`；up保留原共享Q及10KB，不强压。

默认构建配置为 `SM86_C32_REGISTER_Q_MASK=63`（cw_kind0～5，Up单列bit6且关闭）、`SM86_C32_MINBLOCKS=9`。其他C32模块（normal、rtz、fast-norm900）仍为共享Q，避免外推未运行配置。

完整向量化阶段40/40模块、1918 entry编译/CUDA加载通过；Q试验分别替换一个C32 fast模块并验证完整40模块集。最终默认源码重编的C32 fast与长测获胜模块**整个cubin逐字节相同**；选定40模块集的所有哈希也完全相同。因此 `selected-bench.log` 引用同一次 `register-q-capped` 长测，不伪装成独立重复测量。

最终模块：`artifacts/selected/modules/`。本轮未替换共享assets、游戏/Magpie运行时或v0.1.0发布包。

## 底层精度验证

- D→RDNA4：65536个warp批次，每个lane/元素位置覆盖全部65536种half位模式，含±0、subnormal、Inf/NaN，共256个位置；对旧scalar实现 **0 bit-diff**。
- C→Ampere：16777216个随机FP32位模式，打包u32结果对旧实现 **0 bit-diff**。
- `wmma_validate_cuda --fp16-acc`：63组K16/K32、非零C、basis、随机测试，failures=0、FP8/FP16路径bitdiff=0。

实际PTX helper计数：两方向均为selp **48→17**（16条数据交换、1条生成prmt selector），增加4条prmt；shfl仍为8条。不能把4-u32网络写成4条shuffle，也不把数据交换节省32条扩大为总指令净省32条。

## 最终同轮长测（50 warmup / 80 iterations）

| 档位 | Phase4基线 min / median ms | 仅向量化 min / median ms | 最终组合 min / median ms |
|---|---:|---:|---:|
| 900p | 38.604 / 39.105 | 36.445 / 37.011 | **36.095 / 36.671** |
| 1080p | 51.792 / 52.571 | **48.513** / 49.793 | 48.893 / **49.346** |

按稳态median选型；1080p仅向量化的min更低，不能把48.513与组合49.346拼成一套结果。

两档对Phase4基线均0 bit-diff、首末帧bit_diff=0、invalid=0、32/32实际CUDA LMem=0。对F32可见区域PSNR保持900p46.9753dB、1080p46.1009dB，maxabs0.04004550/0.04160273。Small31-block、Style1、固定合成RGB输入，实际处理尺寸1600×1024/1920×1152；不外推未运行场景或设置。

GPU events/CPU Wall均不含初始化、权重打包/上传和最终读回；核级数据来自另加的插桩帧。[完整32核表](results.md) / [JSON](results.json)。

## Q与约束的控制变量

裸寄存器Q的8KB方案数值正确、没有新增residual读取或Q计算，但峰值不只是增加逻辑缓存的16个寄存器：实测C32核升到178～216regs，OccW降为8，没有明确收益。零初始化和不初始化都测试了；后者仅在确认第一个循环完整写入四组Q后使用，不存在未写先读。

随后单独测了prefix约束，再将约束扩展至非up核；最后补齐同约束10KB共享Q控制：

| 最终50/80对照 | 900p median | 1080p median |
|---|---:|---:|
| 向量化，10KB共享Q | 37.011 | 49.793 |
| 向量化，10KB共享Q，同样非up约束 | 37.105 | 49.867 |
| 非up寄存器Q，8KB，同样约束 | **36.671** | **49.346** |

最终五个非up活跃C32核为167～168regs、SMem8192B、OccW11；up为234regs、10240B、OccW8。只给prefix加约束不足以修复其他缓存核的峰值，故不采用该中间版本。单独向量化已自动使prefix169→168、OccW8→9，无需为第一项额外加约束。

Q缓存仍在原第一个qt循环完成投影、归一化、量化与预洗牌，只改变存取。显式q_reg0～3避免按动态qt索引的私有数组；第二循环仅选择已写入寄存器。mask和launch bounds由CUDA后置source pass控制，原HIP源保留共享Q路径。

## 遥测与证据

默认DVFS、约140W上限，未锁频，显存7001MHz。四组长负载SM中位数（1080p/900p）：基线1710/1725MHz，向量化1680/1665MHz，同约束共享Q1657.5/1680MHz，寄存器Q组合1680/1695MHz。主要向量化收益明显；Q组合的额外收益小，与Boost变化同量级，不能宣称严格等频的约1%因果收益。控制组、功耗与逐核数据全部保留。

- `layout-validation.json` / `wmma-validation.log`：实际GPU数值验证。
- `helper-ptx-counts.json`：helper静态指令计数，不是动态执行数/SASS pipe利用率。
- `bound-control-machine-code.json`：相同约束控制改变了代码生成，不能省略该对照。
- `modules.sha256.json`、`build-inputs.sha256.json`、`selected-run.json`：完整模块与源码身份及长测引用关系。
- 所有试验source、有效defines和build.json在 `artifacts/<variant>/source/`；裸Q试验10/40，最终四组50/80，pilot日志另存。

复测：`bash Development/hip-port/phase5/run_benchmark.sh`，可传warmup/iterations。依赖本机Phase4基线、Phase1 F32输出和已归档的中间控制模块；源码/Host必须与AMPERE_WEIGHTS_V2布局配对。主脚本复测基线和默认组合，不自动重跑全部调参控制。
