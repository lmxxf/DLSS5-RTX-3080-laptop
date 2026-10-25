# Phase 7：无分支 FP8、常量裁剪、C32 不变输入解包

保留 **1+2**，第3项只保留实验脚本，不进入默认源码。没有出现按PTX跳转条数比例计算的巨大提速。本轮两档约27.6/36.7ms，精度完全保持，32/32活跃核无LMem。

## 实现与原语验证

- `sm86_f32_to_e4m3_byte` 改为单个PTX asm，setp/selp保持旧转换的全部分支语义及RNE/特殊值规则。独立转换核0条bra。
- 两个FP8解包位置共8处移位组合改为3条指令。`lop3 0xEA` 必须写成 `(原值 & 0x80008000) | 移位后的幅值`：其真值表是 `(a & b) | c`，输入顺序不可交换。第一轮小测试抓到输入排列错误，修正后才采用完整重编集；最初混合编译过程的模块全部由修正后缓存键重核/重编。
- fmed3仅在b/c编译期常量时直接max/min；动态边界保留原四指令实现。输出约束用early-clobber，避免第一条写出覆盖后续仍需的上边界。独立常量裁剪核1max+1min、0bra。
- GPU小测试4262720样本：随机FP32全位域值、全部65536个half模式、FP8舍入边界邻近ULP及正负两侧；旧/新转换、位处理、两种裁剪全部0bit-diff。这是采样/边界验证，不冒充穷尽全部2^32个float值的证明。见[结果](primitive-results.json)、[脚本](check_primitives.py)。
- 完整 **40/40模块、1918 entry** 编译和真实CUDA加载通过。当前默认只有compat头的1+2变化；Host未改变。

## 50 warmup / 80 iter 控制变量

31块Small、Style1、固定合成输入。900p实际处理1600×1024、1080p处理1920×1152，计时排除初始化/权重打包上传/最终读回。默认DVFS约140W，未锁频。

| 方案 | 900p min / median ms | 1080p min / median ms |
|---|---:|---:|
| 同轮Phase6基线 | 27.421 / 27.908 | 36.467 / 36.946 |
| 1+2（默认） | **27.344 / 27.636** | **36.371 / 36.722** |
| 1+2+跨h2预解包 | 27.499 / 27.788 | 36.390 / 36.904 |
| 1+2反向复测 | 27.113 / 27.564 | 35.816 / 36.599 |
| 后跑Phase6基线复测 | 27.757 / 28.173 | 36.655 / 37.330 |

第一对GPU median改善约0.97%/0.61%，第二对约2.16%/1.96%；时钟和帧间波动存在，不给固定等频速度比。主要成绩仍引用第一对，复测独立列出，不混拼min/median。

各组对本轮及已归档Phase6输出都是0bit-diff；invalid=0、首末帧逐位一致、32/32实际CUDA LMem=0。对F32可见PSNR仍为900p46.9753、1080p46.1009dB，maxabs0.04004550/0.04160273。`selected-bench.log`与输出是第一轮step12的明确别名，不算独立重复。

## 静态指令与资源变化

主用prefix：bra **617→10**，min/max **528/530→288/290**，mma仍84。主用mapped：bra442→18，min/max400/402→224/226，mma仍80。C64/C128 bi_bo_w16：bra540→19，min/max128/130→64/66，mma仍100。余下bra包括实际控制流，未声称整个kernel无分支。

这只是静态PTX，不能据此声称SASS同样减少607次动态分支，更不能按这一比例估计耗时。本机没有可用nvdisasm/cuobjdump，本轮没有把PTX当作最终机器指令计数。实际机器码字节与资源已对照，速度以端到端测量为准。

- C512 QKV：203→151regs，OccW8→12；C32 up234→210，prefix152→151。
- C64/C128/C256 wave2主用核分别248→234、242→240、248→225regs，但仍OccW8。
- 同时有回退：split FFN106→186regs、OccW16→8；ViT project101→138regs、OccW16→12；ViT attention78→119regs（OccW仍16）。这些核的分解耗时也有增加，不能只报受益核。
- 第一轮插桩核累计900p26.256384→25.724960ms、1080p34.411520→33.817600ms。插桩为独立单帧，有调度抖动；反向复测1080p核累计34.890752ms，不能与第一轮最小端到端延迟混合成一帧。

[32核完整对照表](results.md) / [JSON](results.json)，[主用核PTX](ptx-counts.md)，[40模块PTX](ptx-module-counts.md)。模块总量包含未执行入口，不是本帧动态指令总量。

## 第3项为什么未保留

`hoist_input.py` 在CUDA源码后处理阶段，只把W16 expansion的两份`input`转为u4放到h2循环前；权重仍按原路径解包，输入生产、FP8量化、MMA次序不变。完整数值0bit-diff。C32寄存器与OccW基本不变，没有新增LMem，但prefix/mapped/up机器码分别多640B；最终median两档都比1+2慢，所以默认不启用。保留源变换和模块，供后续精确研究LICM/调度，无收益不强行上线。

## 产物与复测

默认40模块：`artifacts/selected/modules/`，哈希与`step12`全部相同；`modules.sha256.json`与`selected-run.json`说明对应的真实测量。第一轮完整构建日志保留，`step12-rebuild.log`是修正LUT操作数后最终完整40/40检查。

`bash Development/hip-port/phase7/run_benchmark.sh` 重编默认1+2与可选预解包，再按50/80跑基线/1+2/预解包。基线依赖Phase6归档，F32对比依赖Phase1归档。`bench_variant.sh step12-repeat 50 80`可独立复测，重复日志不会覆盖第一轮。

遥测见`telemetry.csv`及`telemetry-summary.json`，分窗统计使用GPU utilization>=95%的样本；包含两档及窗口内初始化，不当作逐核固定时钟测量。

本轮更新源码、实验模块与工作记录；共享assets、Windows frame.exe/addon、游戏/Magpie和v0.1.0正式包未覆盖。新模块仍需AMPERE_WEIGHTS_V2 Host。
