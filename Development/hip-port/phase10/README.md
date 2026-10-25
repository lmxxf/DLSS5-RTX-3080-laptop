# Phase 10：九核寄存器上限＋有限域FP8内部饱和

**最终两档GPU median低于24/32ms：900p23.750ms，1080p31.631ms。** 32/32活跃核LMem0，两档对Phase9输出0bit-diff。默认保留两项优化，Graph关闭。

## 最终独立50 warmup /80 iter

31块Small、Style1、固定合成RGBA输入；实际处理1600×1024 /1920×1152。GPU不含初始化、权重上传、最终读回；Wall含逐帧提交/同步。PROFILE_TOTAL为另一个插桩帧，不与median混成同一帧。

| 档位 | Phase9同轮GPU min /median | Phase10 GPU min /median | Phase10 Wall median | Phase10核累计 |
|---|---:|---:|---:|---:|
| 900p | 25.244 /26.361 | **23.461 /23.750** | **23.850** | **21.753888** |
| 1080p | 34.459 /35.028 | **30.944 /31.631** | **31.712** | **28.430336** |

单位ms。同轮median时间分别减少9.90%/9.70%，速度比1.1099×/1.1074×。默认DVFS未锁频，不宣称严格等频倍数。p90为24.534/32.042ms；“达标”指本轮median，不是全部80帧都低于预算。

同一最终模块集的前一次低寄存器修正实测为900p23.107/23.479、1080p30.751/31.259（min/median），核累计21.728256/28.360704ms；该组单独保留，没有将它的min拼到最终独立复测median。

所有成功整网组对本轮基线及归档Phase9输出bitdiff0、invalid0、first/last0；FNV仍900p `b949727e624db210`、1080p `a8365381a41f7f83`。对F32可见PSNR保持46.9753/46.1009dB、maxabs0.04004550/0.04160273。没有据此宣称与原版PTX DLL在相同输入/处理尺寸下正面对比获胜；本轮未重跑DLL。

## 重锤1：先对相同PTX直接加maxnreg

先复用Phase9 PTX，仅修改9个入口的寄存器上限，再由原O4工具JIT。没有先改变LLVM优化，控制变量清楚。已进入默认builder的llc之后/O4之前，见 `hip/phase10_transform.py:apply_register_caps`；精确入口白名单，幂等，不改其它核。使用用户已验证的 `.maxnreg`，没有把它与前端launch_bounds变化混在一次测试里。

| 活跃核组 | 上限 | 实际Regs | 实际LMem | OccW |
|---|---:|---:|---:|---:|
| C64四核：bi_bo_w16、bi_w16、bi_ho、up_lb_sh | 168 | 168 | 0 | **8→12** |
| C128三核：bi_bo_w16、bi_ho、up_lb_sh | 168 | 168 | 0 | **8→12** |
| c512_qkv_attention_compact_w16 | 128 | 128 | 0 | **12→16** |
| c32_wave1_up_b8_w16 | 168 | 168 | 0 | **8→9** |

完整实际查询见`caps-resources.json`、`optimized-resources.json`及核表。Up保持10KB SMem；没有为了追求11另开Up的register-Q。原五个非Up C32继续8KB/Occ11/LMem0。

首轮50/80，Phase9基线median26.242/34.964ms，只有caps为26.279/34.895ms。资源提升复现了，但整帧单独收益很小；不能把占用率提升50%直接当作加速50%。

## 重锤2：量化器内部单次饱和

CUDA源码后处理 `optimize_fp8` 在预处理和既有布局变换之后替换兼容层中的转换体。fast分支先提取符号与绝对值，在32位bit寄存器上直接执行 `min.f32 a,a,0f43e00000`，然后沿用原RNE/subnormal位运算，去掉p_sat/p_nan。这里是float指令读取同宽bit寄存器，实际CUDA JIT和原语测试已验证，不是整数min近似。

有限域等价机制：绝对值不超过448时输入a保持原值；RNE的 `r=a+((a>>20)&1)+0x7ffff` 最大0x43e7ffff，原饱和区的新表达式 `(r>>20)-960` 正好为126。超过448的有限值先变为448，符号保持，输出仍是±448编码。subnormal路径与舍入tie规则不变。

只在FP8编码前端删外层夹断：cw_z、w2_z、fp8_add0、F/fp8/byte_F/cw_up_F中的对应调用。残差浮点值乘权重等仍需±448的夹断，测试明确保证不删除它们。AMD原HIP源里硬件需要的夹断仍保留；CUDA优化集中在后处理，不改变原HIP权重/接口。

### Signed zero和非有限域

当前CUDA的cw_z原本是clamp(x)，保留-0；直接换成x+0会将字节128改为0。因此最终 **cw_z→x**，原来具有x+0的入口继续保留+0，不额外改变归零语义。原语实测记录128与0的区别。

有限域GPU测试 **4242851个值**：随机全部位区间的有限FP32、全部有限half模式、FP8相邻表示值的中点及±2ULP、正负零/最小subnormal/最大有限值。旧外层clamp+转换与新fast/低寄存器转换，三项bitdiff全部0。见[原语JSON](primitive-results.json)、[脚本](check_primitives.py)。这是采样和边界验证，不冒充穷尽全部2^32位模式。

**有限域约定是实质边界。** NaN的旧外层fmed3、旧raw转换、新内部min的编码不完全相同；原语JSON另列Inf/NaN诊断，未把它们计入有限域0bit结论。正常整网测试invalid0，不代表任意NaN输入的旧位模式都保留。

### 实际指令削减

并非所有模块原来都有外层夹断：当前wave2的w2_z早已为x，那里的收益主要来自内层4条谓词/选择换1条min，按每8元素是24条目标操作，而不是统一40。保留原有外层clamp的点则对应每8元素省40条目标操作。

[PTX统计](ptx-counts.md)：prefix max290→66、setp693→245、selp1112→664，min288保持（夹断从外面移动到里面）；wave2主核min64→256、setp621→237、selp963→579。min增加并不等于整体指令增加。MMA/shfl数量保持原样。静态PTX不是动态SASS，未声称所有核都净省固定1000条。

## 三个低寄存器路径的修正

第一次组合版达到23.702/31.412med，但mapped8B、split FFN56/64B、ViT project16B local重新出现。简化后的C++短表达式可被LLVM变成提前计算的分支，两路临时值增加存活范围；没有把这组当最终零spill结果。

最终仅在已有低寄存器入口中，显式分开subnormal/normal路径。用受约束的 `asm volatile` 保证该路径的计算不被无条件提前：subnormal才做magic add，normal用短整数asm做RNE。不加memory clobber或GPU fence；没有恢复p_sat/p_nan，也没有恢复外层冗余min/max。fast编码路径保持新的无分支版本。

三个模块重编后，mapped168regs/LMem0、split FFN105regs/LMem0/Occ16、ViT project101regs/LMem0/Occ16；有限域原语再次bitdiff0，整网32/32零LMem。

## 完整控制组和产物

[所有控制和32核资源/耗时表](results.md) / [JSON](results.json)明确列出Phase9、caps-only、首次组合（3处spill）、修正组合和最终独立复测。首轮caps核累计900p24.346624ms，1080p32.769024ms，来自各自独立插桩帧，不能拼成该轮median对应的一帧。

`optimized-build.log`：完整40/40模块、1918entry实际CUDA编译/加载通过。`lowreg-fix-build.log`：3个受影响模块另编，剩余37个复用同一已验证优化；最终40模块集整体跑完两档。两个构建脚本均显式设置PHASE10_FP8=True，之后默认标志设为True以匹配已测配置；没有声称又完整重编第二次。最终`selected-bench.log`是独立新测，不是其他日志的别名。

默认目录`artifacts/selected/modules/`，来源/输入/模块SHA256与源快照保留。`PHASE10_CAPS=True`、`PHASE10_FP8=True`均已默认启用。复测：`bash Development/hip-port/phase10/run_benchmark.sh`，会从当前默认源码重编全部40模块，写独立`selected-full-rebuild.log`，然后基线/候选50/80。

最终高利用率窗口SM中位数基线1612.5MHz、候选1567.5MHz，显存7001MHz，功耗约139W；默认DVFS未锁频。遥测晚于首轮baseline/caps，缺少的样本没有补造。窗口合并两档并含部分初始化，不当作逐核等频统计。

原语验证、寄存器上限/归零/残差范围测试、既有布局/SSA/IR/对齐检查和diff-check通过。二进制/原始图像均在忽略的artifacts。共享assets、Windows frame.exe/addon、游戏/Magpie与v0.1.0发布包未覆盖，新模块仍需AMPERE_WEIGHTS_V2 Host。

## 720p补测（2026-10-25）

最终selected模块未改，1280×768、50/80、Graph off：GPU min13.843/median14.103ms，Wall median14.182ms，PROFILE_TOTAL14.001120ms，invalid0、首末帧0bit-diff、32/32零LMem。完整[三档与PTX历史标尺对照](three-tier-results.md)已同步到DevHistory/WorkingPlan；900p/1080p沿用此前最终独立复测。

首次720p进入旧C256分散核，触发misaligned-address。逐核同步定位后，Host仅增加1280×768的C256 wave2门控，调用selected中已存在的核；另外以Phase5无对齐升级模块和原C256分散路径生成参考，720p完整输出0bit-diff。该补测的Host快照/模块哈希在artifacts/720p-host，原900p/1080p来源快照保持不动。正常计时未启用同步诊断。复测脚本bench_720p.sh依赖本机已保存的Phase5参考输出。
