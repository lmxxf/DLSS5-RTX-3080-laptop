# Phase 11：只在C32 FFN feature生产点直接从half打包FP8

以冻结的 **Phase10 selected** 为唯一性能基线。本轮只保留一个小改动：C32 fast核的FFN feature（Site2）已有RTZ后的half8，直接成对转FP8，不再先扩展成8个FP32再量化。residual原有RTZ、累加顺序、其它激活/归一化点、布局及权重均保持。

1080p最后两对median分别改善 **0.233ms /0.246ms（约0.72% /0.76%）**；900p微小正向；720p结果在噪声内，不宣称稳定加速。默认Graph off。没有重试跨h2预解包、CUDA Graph，没有碰ptx-patcher、共享assets、Windows部署或v0.1.0 ZIP；不push。

## 初始状态和证据范围

- 工作区初始干净，祖先目录及Development下未找到适用AGENTS.md；初始HEAD见`artifacts/selected/selected-run.json`。
- 已读Development/DevHistory末尾及Phase10 README/results/three-tier-results。性能基线固定为`phase10/artifacts/selected/modules`，40个SHA保存在[冻结清单](phase10-baseline-manifest.json)，每次bench前校验，没有重编或覆盖Phase10。
- 热点为1080p prefix/post，归档值4.580352/4.445184ms，六个C32约13.47ms。本轮重新同场测量，不拿旧轮最小值比较。
- 本机找到Triton附带cuobjdump/nvdisasm，版本见[sass-tool-version.txt](sass-tool-version.txt)。已读真实Phase10 cubin的SASS、生成CUDA/PTX和实验opt LLVM IR；不是只扫描HIP源。

## 小步实验与取舍

### A：移除FFN half→FP32→RTZ half往返，负结果

MMA使用FP16累加，FFN末尾的结果已经是half；尝试仅将`cw_rtz_half8(ffn[ci])`改为原生half向量转换，让LLVM消掉扩展/截断。LLVM verifier确认原生fpext/fptrunc可抵消；每位置穷举65536种half模式，16252928个有限值逐位相同。NaN位模式并非全域一致，诊断保留，没有将有限域结论扩张。

真实SASS中prefix/post各少16条F2FP.RZ、mapped少8条，MMA/shfl/shared读写不变，整网三档0bit、零LMem。然而首扫900p23.805→24.253med反而变慢；1080p初扫较快，反向复测 **32.024→32.032ms** 无收益。**不保留A**，没有因静态指令减少就上线。

首次half-store 1080p原始日志被一次反向复测误覆盖；原首次汇总JSON/MD已保存在first-sweep-results.*，其它原始日志保留，反向运行单独改名。此不完整原始记录不作为保留依据。之后bench.py拒绝覆盖已有运行名，复测均使用新名字。

### B：直接half2→FP8，保留

原Site2执行：RTZ为half8→写residual→half8扩成float8→每字节通用FP32量化。新代码保留前两步，只替换后两步。实现位于`hip/phase11_transform.py`，builder默认仅对`c32-wave1-fast`应用；其它39个模块机器码逐字节相同。最终C32与已测试候选的57个.text代码节全部相同。

成对编码的精确机制：

1. 清除符号，对两个half独立min到448（half位0x5f00）。
2. E4M3 subnormal间隔为2^-9，half的2.0附近ULP正好也是2^-9，故half2加2.0可精确得到相同RNE子正规网格。
3. normal区保留3位尾数，`r=a+0x3f+((a>>7)&1)`；half/E4M3指数偏置差对应输出码减64。用每16位槽加0xc0再取低8位，实现模256减64。
4. 不能让低槽进位污染高槽。clamp后r低槽<=0x5f40，整字右移7后低槽最坏`(0x7f<<9)+(0x5f40>>7)+0xc0=0xff7e<0x10000`；两次舍入加法也未跨16位。CPU测试和混合lane GPU穷举覆盖此条件。
5. 每个半槽按原值是否<2^-6选择sub/normal，恢复原符号，再PRMT成两个字节，沿用原presuffle及featureABI。

GPU原语覆盖65536模式×256位置：**16252928个有限half字节全部0bit-diff**。另外显式模拟实际RTZ生产者后，对全部half输入位模式（含特殊值）的打包结果也完全一致。原语结果见[half-pack-primitive-results.json](half-pack-primitive-results.json)及[RTZ生产者结果](half-pack-rtz-primitive-results.json)。不把这个只适用于该生产点的结果当成所有任意float激活都可改为half。

## SSA/PTX/SASS结果

- [SSA摘要](ssa-audit.json)：prefix/post的K循环仍4个u4 PHI、0个f8 PHI；没有退回8寄存器累加或破坏既有抵消。
- [SASS完整计数](sass-audit.json)：prefix静态槽12227→12117、post10356→10252，各少32条HADD2.F32，引入成对half min/add；HMMA/shfl不变。
- mapped反而7372→7532槽，F2FP.RZ16→24，属于编译器代码增长；真实mapped耗时没有据此被“推导成变慢/变快”。最终以整网及核表为准。
- finish两个核Regs168→162，OccW仍11。其它活跃C32仍168；32/32无LMem。没有把Regs下降当作速度证据。
- [机器码比较](machine-code-comparison.json)：39模块的所有代码节与Phase10相同；C32最终与候选[57节相同](final-vs-candidate-code.json)。

## 最终默认全量重编与配对50/80

[final-build.log](final-build.log)为默认源码 **40/40模块重编、1918entry实际CUDA加载验证通过**。另有verify_modules.py重新加载全部cubin并逐个解析1918入口，即使构建命中缓存也可复核。模块哈希位于artifacts/selected/modules.sha256.json，输入/源码快照同目录及artifacts/build-inputs.sha256.json。

固定Small31、Style1、Graph0、原确定性RGBA公式，默认DVFS、约140W。GPU不含初始化/上传/最后读回，Wall含提交与同步。原720p 1280×768 C256 wave2路径保留，未触及门控。

第一对最终运行（每档Phase10先、Phase11后）：

| 档位（处理尺寸） | Phase10 GPU min /median | Phase11 GPU min /median | Phase11 Wall med | Phase11独立核累计 |
|---|---:|---:|---:|---:|
| 720p（1280×768） | 13.949 /14.369 | **13.894 /14.406** | 14.490 | 13.586432 |
| 900p（1600×1024） | 23.110 /24.077 | **23.205 /24.019** | 24.126 | 22.693888 |
| 1080p（1920×1152） | 31.099 /32.161 | **31.549 /31.928** | 32.041 | 28.465152 |

第二对反向确认（Phase11先、Phase10后；1920→1600→1280）：

| 档位 | Phase10 median | Phase11 min /median | Phase11 Wall med | Phase11独立核累计 |
|---|---:|---:|---:|---:|
| 720p | 14.737 | 14.328 /14.580 | 14.668 | 15.984640 |
| 900p | 24.471 | 23.464 /24.170 | 24.280 | 21.750784 |
| 1080p | 32.257 | 31.553 /32.011 | 32.159 | 28.707840 |

单位ms。720p首对慢0.037ms，反向快0.157ms，没有稳定收益结论。900p分别快0.058/0.301ms，1080p快0.233/0.246ms；不把不同轮次min/median拼接，不宣称锁频因果。所有原始控制和三档32核对照见[results.md](results.md)及[JSON](results.json)。

PROFILE_TOTAL为另外的单插桩帧。第二对720p核累计15.984640ms高于其GPU median14.580ms，存在明显单帧调度波动；照录但不当均值，不计算launch气泡或夸大逐核速度比。第一对900p候选插桩也有波动，不能拿独立核累计替代80帧分布。

## 质量门和参考限制

所有候选、最终默认和反向确认输出均相对唯一Phase10基线 **0 bit-diff、invalid0、first/last0、32/32活跃核LMem0**；最终/反向的原始输出也与Phase10归档输出直接比对。质量摘要见[quality.json](quality.json)。

900p/1080p对已归档F32金标准的可见PSNR分别 **46.975322/46.100947dB**，maxabs0.04004550/0.04160273，均保持。720p输出比特相同，故对任何共同固定F32参考PSNR严格相同；没有补造绝对值。

本轮尝试Phase1旧F32模块配当前Host生成720p参考，出现与Phase10 PSNR11.6075dB/maxabs1的结果；这一历史模块/新Host/720组合并非已验收金标准，原因未在本轮确定，不能用作绝对质量宣称。原输出、日志及[f32-720-reference-audit.json](f32-720-reference-audit.json)保留；未修改Phase1或修复该旁支。它不是性能基线，性能从始至终只有Phase10。

## 遥测、清理、复测

telemetry.csv和每个*-run.json记录时窗、输入模块40哈希、50/80参数。results.json列出该窗口高利用率样本的SM/显存时钟、温度、功耗中位数。窗口含两次运行各自初始化/预热，不能当逐帧等频观测；没有锁频/改电源上限，负载多数接近139～140W。

已按[cleanup-manifest.json](cleanup-manifest.json)删除约979MB重复模块和临时IR/完整派生SASS；验证字节相同后对重复原始输出硬链接去重约551MB，保留全部原始输出路径、日志、哈希与负结果。最终完整40模块保留；候选只保留变化的C32 cubin和源，先运行build_variant.py可从冻结Phase10重建另外39模块。SASS工具可随时从cubin重生反汇编。

完整复测入口：`bash Development/hip-port/phase11/run_benchmark.sh`。它先原语/LLVM检查，默认源码构建40模块并实际加载，然后以新运行名逐档跑冻结Phase10/候选50/80，拒绝覆盖旧日志并采遥测；分析脚本不会改Phase10。需本机冻结基线、模型资产，已归档F32绝对值还需Phase1金标准。此脚本不推送、不部署。

单项重现：先`python Development/hip-port/phase11/build_variant.py half-store --keep-ir`或`half-feature-pack --keep-ir`，再bench.py用一个新variant名和--modules指定候选目录。Graph及跨h2实验没有重试。

## 建议Phase12

优先审计同类**已是FP16的AV/V生产者**，当前Phase8/9虽省了布局往返，仍有half扩float后逐元素量化。可复用本轮half2原语，但先分别证明生产者舍入/NaN规范化与字节布局，逐站单独控制；不要把float激活多项式或Q/K行归一化直接降成half。另需补一个与当前Host/Small图匹配的720p F32参考，之后再做任何精度相关探索。
