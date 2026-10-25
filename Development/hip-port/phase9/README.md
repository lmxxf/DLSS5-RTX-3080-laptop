# Phase 9：Graph、V直通、五个C32核全部8KB零spill

资源目标达成：五个非Up C32活跃核均 **8KB SMem / OccW11 / LMem0**，整网32/32活跃核LMem0、两档0bit-diff。V已走2-shfl直通，Graph已真实捕获与重放。但本轮没有进入900p24ms /1080p32ms；Graph没有省下预期1.5～2.3ms，默认保持Graph可选。

## 最终默认源码版：50 warmup /80 iter

31块Small、Style1、固定合成RGBA输入；实际处理1600×1024 /1920×1152。GPU不含模型初始化、权重上传与最终读回；Wall包含逐帧CPU提交和同步。PROFILE_TOTAL来自另一个插桩帧，不是GPU median对应帧。

| 档位 | Phase8同轮GPU min /median | Phase9无Graph min /median | 无Graph Wall median | 无Graph核累计 | Graph GPU min /median | Graph Wall median |
|---|---:|---:|---:|---:|---:|---:|
| 900p | 26.369 /26.641 | **26.265 /26.612** | 26.722 | **24.837120** | 26.254 /26.614 | 26.727 |
| 1080p | 34.954 /35.486 | **34.924 /35.318** | 35.407 | **32.576256** | 35.058 /35.420 | 35.555 |

单位ms。最后配对median改善900p0.029ms、1080p0.168ms，幅度很小，不包装成稳定大幅提速。此前同一最终策略实验构建无Graph26.445/35.160med，Graph26.501/35.250med；两组分别保留，不能把实验min拼到最终默认源码median。

最终两档无Graph/Graph输出均对Phase8逐位一致；first/last bitdiff0、invalid0。Graph改动整张输入后，与即时执行输出bitdiff0，恢复输入后也bitdiff0，且全部4915200/6635520个RGB值确实改变，排除重放静态旧结果。FNV仍900p `b949727e624db210`、1080p `a8365381a41f7f83`；F32可见PSNR仍46.9753/46.1009dB，maxabs0.04004550/0.04160273。

[32核表和全控制组时间](results.md) / [完整JSON](results.json)。83次kernel调用在无Graph插桩中已核实；未把两次不同运行的时间差直接归因为83次launch的纯开销。

## 第一拳：Graph解锁和真实验证

Host移除Small/wave-owned、compact contract/projection、final-direct及900p选择路径的7个旧Graph门控。PreflightPdl的Graph return保持；实验temporal等其它不兼容条件保持。hip_api原有CUDA capture/instantiate/launch绑定直接复用。

benchmark设置 `DLSS5_BENCH_GRAPH=1` 切换 `opt.graph`，0或未设置关闭。每档实测 **Small1 /wave_owned1 /final_direct1，builds1 /replays130**；并没有回落71块模型或失去紧凑W16权重。Graph计时不做逐核插桩，GPU/Wall单独报告。`DLSS5_BENCH_GRAPH_VALIDATE=1` 在计时后做输入改变/恢复与Raw路径对照。

首轮Phase8模块无Graph26.637/35.361med，Graph26.675/35.536med；V-only无Graph26.546/35.244，Graph26.545/35.376；最终策略与默认源码重测也未出现明显Graph收益。因此没有把Graph强制设为默认。

原先将GPU median减去独立插桩帧PROFILE_TOTAL所得的1.8/2.6ms，不能全部视作可被Graph消掉的气泡。无Graph接口允许CPU提交与前面的核执行重叠；具体设备发射延迟占比本轮没有用硬件时间线测出。实测只支持“Graph工作正确，但未追回所估全部差额”，不进一步编造某个驱动根因。

## 第二拳：V的2-shfl直通

`hip/phase9_transform.py` 仅在 `part==2` 的V路径上，量化前切换到Ampere D元素顺序，pack后调用 `sm86_d_bytes_to_ab`。覆盖C32 q[ci]及wave2融合/非融合QKV分支；Q/K归一化和各自布局不变。V的乘1/加0和原来的FP8量化表达式保持原有舍入语义。

V-only两档0bit-diff、LMem0。静态PTX相对Phase8，prefix shfl229→209、mapped200→180、wave2主核204→184，MMA不变。静态20条减少对应当前qt循环中两个V片段；qt=0..3动态循环按4次执行，即目标每窗口80条shfl，不是整核总shuffle都减少80。

[PTX统计](ptx-counts.md)同时列出V-only与最终策略，便于区分布局变化和编码器变化。

## 第三拳：按核选择编码器，恢复全register-Q

不同核需要不同的编码路径，统一切换不是答案：

| C32策略 | prefix | mapped | 实测选择 |
|---|---|---|---|
| 全Q+全模块低寄存器FP8 | 8KB/Occ11/16B local | 8KB/11/0 | 保留实验，不默认 |
| 低寄存器FP8+先消费qt3 | 仍16B local，机器码更大 | 8KB/11/0 | 更慢，排除 |
| 全Q+全模块无分支FP8 | 8KB/11/0 | 8KB/11/8B local | 保留实验，不默认 |
| 仅mapped低寄存器、其它保留无分支 | **8KB/11/0** | **8KB/11/0** | **最终默认** |

最终在CUDA的 `cw_pack8` 增加编译期布尔模板参数，只让 `!Up && cw_kind==1` 选择低寄存器编码。prefix、Up和其它类型保留Phase7无分支编码。Kind/Site本来的数值含义不改，没有改动全局量化规则。两种编码算法的字节结果相同。

fast家族Qmask恢复 **63**，原minblocks9保留。最终五个非Up主用核全部8KB、OccW11、LMem0，regs均为168（完整数值见核表）；Up保留10KB/217regs/OccW8。映射核静态bra恢复到442，prefix最终18（其中新增Q缓存控制），不能再声称所有C32核都只有十几条bra。实测寄存器、LMem和时间决定是否保留该局部选择。

C512 splitFFN106regs/Occ16/LMem0、ViTproject101/16/0保持。C64/C128主用wave2因V优化降为225/231regs，C256226，OccW仍8。

## 控制实验与限制

所有阶段均50/80，完整数据见results：包含基线、Graph-only、V-only及Graph、全Q低寄存器、qt3剥离、全Q无分支、prefix共享Q退路、逐核策略及最终默认源码重编。全部这些成功运行的输出0bit-diff；有spill的组明确计数，不把它们的更低min冒充零spill成绩。

最初完整构建有三个不启用register-Q的C32变体被过窄的源码断言拦住，已修正并补编，最终 **40/40模块、1918entry** CUDA加载验证通过。日志分别为`v-build.log`、`v-repair-build.log`。早期不完整目录的失败运行保存在`artifacts/failed/`，成功V测试随后重跑。最终默认C32按新源码再编一次，其余39个复用完整V构建；最终40模块目录完成两档无Graph和Graph验证。

最终基线/候选/Graph高利用率窗口SM时钟中位数1620/1605/1590MHz，显存7001MHz、功耗约139W，未锁频。遥测开始晚于首轮baseline/Graph-only，它们没有遥测样本；没有补造。窗口同时覆盖两档并含部分初始化，不作逐核等频测量。

当前测试处理1600×1024/1920×1152，未重跑同尺寸同输入的原版PTX标尺。**没有达到24/32ms，也没有宣称正面反超原版DLL。**

## 产物与复测

最终模块 `artifacts/selected/modules/`；最终源码快照、模块和输入SHA256、`selected-run.json`记录真实构建/测量，最终日志不是其他运行的别名。当前默认Host Graph可选，保留V和逐核编码+Qmask63。

`bash Development/hip-port/phase9/run_benchmark.sh` 从当前默认源码重编40模块，执行Phase8基线、Phase9无Graph、Graph各50/80，Graph额外做动态输入检查。需已有Phase8基线/F32金标准及本机模型资产；不覆盖先前实验构建日志。

本轮两个V/编码策略测试、既有三个布局/SSA测试、三个IR测试、两个对齐测试和diff-check通过。二进制与rgb32仅在忽略的artifacts目录。共享assets、Windows frame.exe/addon、游戏/Magpie和v0.1.0发布包未覆盖。
