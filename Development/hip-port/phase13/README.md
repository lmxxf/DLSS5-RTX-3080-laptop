# Phase13：C32 动态阶段审计与720p共同attention错误定位

唯一基线 **Phase12 selected**，起点41220e0、工作树干净。本轮**不保留新性能改动**，最终默认仍是Phase12；全量源码重编及实际CUDA加载40/40、1918entry，40个模块SHA全部与Phase12一致。没有修改生产源码、共享assets、冻结PTX路线、Windows游戏/Magpie或发布ZIP，不push。

## C32真实生产/消费链

prefix从RGBA/noise/残差产生输入，post从low/skip/scales产生输入；FP8片段进入Ampere MMA，expand的FP16 D结果经现有直通映射在正确布局上执行**原float激活多项式**，再E4M3量化给contract。contract的两个独立通道累加链跨h2循环保活，之后RTZ feature写residual并打包，继续Q/K/V生产。第二个qt循环消费寄存器Q及shared K/V，完成QK/softmax、AV、projection/residual和输出。

这是依赖约束：每个contract链的h2、hp累加顺序不能变，float激活不能直接降half，Q/K的行归一化不能当作纯逐元素操作。Phase11/12已经处理的feature/AV站点继续保留；本轮没有重试C32 V、wave2 AV/V、Graph或跨h2预解包。

### 动态采样、SSA和SASS证据

本机无现成Nsight Compute，使用隔离诊断模块：每64个CTA取一个warp，阶段边界`bar.warp.sync + clock64`，lane0记录时间；在**第50次预热完成附近的第51次核调用**抓取（CLOCK_SKIP=50），不是用冷启动结果替代正式计时。prefix540个CTA样本、post547个，4个qt均采。插桩输出对Phase12逐位一致，两个核仍168regs/8192B shared/0B local。

| 每qt阶段 | prefix中位周期 | post中位周期 |
|---|---:|---:|
| 输入/merge | 3707 | 2862.5 |
| FFN expand→float activation→contract | **10432** | **11122** |
| feature pack→QKV→norm | 6525 | 5736 |
| QK→softmax | 3365 | 3191 |
| AV→pack | 1304 | 1322 |
| projection→residual | 1169.5 | 1215 |

post最终head/tail额外中位3587周期；prefix在marker33前返回，**没有编造prefix tail值**。完整p10/p90见`clock-results.json`，冷帧控制见`clock-cold-results.json`。插桩/warp barrier/global stores会扰动调度，这些只是实际执行段的周期诊断，**不是硬件stall计数、纯MMA延迟、未插桩帧时间或可直接相加的SM总占比**。

`audit_ssa.py`重新生成实际SSA：基线与两个变体的prefix/post均为4个`phi <4 x i32>`、0个`phi <8 x float>`，C/D调用计数不变（`ssa-audit.json`）。不能把剩余布局调用一概当冗余删除。`audit_dependencies.py`保存实际HMMA寄存器生产/消费及前后load/convert指令上下文，见`dependency-witnesses.json`。该脚本自己的静态SASS计数prefix12056→12144、post10184→10256，HMMA站点148→152/140→144；是编译/展开形状变化，不当作动态操作数或速度。

## 小步控制：FFN activation即时消费

动态采样显示FFN段最重，因此只试一个可证明的顺序变换，分别作用prefix和post：原来先生成`act[0]、act[1]`，再更新ci0/ci1；候选每个hp的activation产生后立即更新两个ci，不让act0跨整个hp1激活区间存活。每条ci链仍严格依次h0hp0、h0hp1…h3hp1；weight W16的lo/hi、原float多项式、FP16舍入、RTZ和后续布局不变。

`sequence_probe.hip`/`test_sequence.py`验证4096warps×32lane、8次MMA/链，含全部half模式、NaN/Inf/±0，原始u32差异0。两个结构作用域测试及16项既有Python/LLVM回归通过。全网首末帧和Phase12输出也0bit，32/32 LOCAL0。

50warmup/80iter，Graph off，默认DVFS140W上限，同轮及反向：

| 站点 | 正向：基线→候选median | 反向：候选→紧邻基线median | 结论 |
|---|---:|---:|---|
| prefix即时contract | 31.306→31.512 | 32.017→31.946 | 两对更慢，不保留 |
| post即时contract | 31.306→31.645 | 31.816→31.871 | 方向不稳，不保留 |

第一轮两个站点共用同轮起始基线，反向各有紧邻对照；不把它们包装成严格等温ABBA。不追着噪声调参，也不组合两个未过门的变体。Regs/OccW不作速度证据，完整min/median/Wall/独立PROFILE_TOTAL、32核及遥测在`results.md/json`。只记录受测GPU时钟与功耗，不宣称锁频因果。

## 最终三档默认验收

[两轮完整表与遥测](final-results.md)、[全部控制与32核表](results.md)、[质量门](quality.json)、[40模块SHA](selected-modules.sha256.json)、[实际加载证明](cuda-load-verification.json)。最终40模块全部从默认源码重编，**与Phase12机器码相同**；独立运行之间的时间差只是波动，不宣称Phase13提速。

| 档位/轮次 | GPU min / median | Wall median | PROFILE_TOTAL |
|---|---:|---:|---:|
| 720p正向 | 13.975 / 14.123 | 14.198 | 13.440000 |
| 720p反向 | 14.230 / 14.377 | 14.472 | 13.700096 |
| 900p正向 | 23.205 / 23.646 | 23.763 | 21.706752 |
| 900p反向 | 23.397 / 23.932 | 24.067 | 21.781504 |
| 1080p正向 | 31.264 / 31.835 | 31.934 | 28.743680 |
| 1080p反向 | 31.537 / 32.057 | 32.188 | 29.387775 |

两轮三档完整输出对Phase12 0bit、invalid0、首末帧0bit、32/32活跃核LMem0。720固定1280×768、C256wave2门控保持，无misaligned address。900/1080可信F32可见PSNR **46.975322410562406 / 46.100947087035124dB**不变。PROFILE_TOTAL是单独插桩帧，直接读取日志总计，核表逐项六位小数求和另存；不把它与GPU median的差额全部归为launch气泡。

## 720p旁线与Phase14

详见[参考链独立审计](reference-audit.md)，已先单独提交6b61bd9。首次异常在首个ViT块的`vit_attention_fused_256_bytein_bout`，**Phase12和旧F32都存在**。同一实际QKV，旧F32的256 AV对CPU RMSE33.331681，隔离改400后的245760个AV字节对CPU100%一致；900/1080同参考链复现gold0bit。具体旧256的错误索引/布局指令未最终证明，均匀探针通过，不能宣称n%64尾块是根因。

400诊断会改变当前720输出，故不混入本轮严格0bit默认。不报告默认720绝对PSNR，也不使用11.6075dB坏比较淘汰候选。修正图两链43.577948dB只是诊断值，不是当前默认参考验收。

**Phase14建议先做独立正确性修复**：坐标单点Q/K/V核对256的LDS转置、分母和PV布局，以CPU/400为交叉核验，再接受新720输出基线并补F32金标准；检查其它<=256 token几何。性能侧FFN仍值得审计，但本次即时消费已证实无收益，不原样重试。

## 复测入口

```bash
python3 Development/hip-port/hip/build_sm86_modules.py Development/hip-port/hip Development/hip-port/phase13/artifacts/selected/modules
python3 Development/hip-port/phase13/verify_modules.py
bash Development/hip-port/phase13/run_benchmark.sh
python3 Development/hip-port/phase13/final_quality.py
```

`bench.py`拒绝覆盖已有轮次，run_benchmark接受新名字。源码相同、默认模块哈希固定；Host二进制是Phase12原样复制，正式计时未使用诊断Host。遥测命令及复测应分开运行，GPU串行，不与其它GPU工作重叠：

```bash
nvidia-smi --query-gpu=timestamp,clocks.sm,clocks.mem,power.draw,temperature.gpu,utilization.gpu --format=csv,noheader,nounits --loop-ms=500 > Development/hip-port/phase13/telemetry-retest.csv
```

FFN控制重建：`build_candidate.py prefix` / `post`；原语 `test_sequence.py`，结构测试 `test_transform.py`；动态采样先`build_diagnostic_host.py`、`build_instrumented.py`，再`run_clock.py`。实际attention捕获 `run_attention.py`，CPU核验`attention_cpu.py`。完整参考链复现顺序见reference-audit；清理后的候选目录只保留变化模块，重测前需先重组完整40模块。

只清理本轮可复建的大产物：原层dump约1.24GB已统计/哈希后清理，候选/插桩不变模块副本、原始LLVM和预处理源另记cleanup.json；最终40模块/PTX/生成源、改变的候选模块、小样本、哈希、原始日志及遥测保留。所有二进制位于忽略的artifacts，不进Git。
