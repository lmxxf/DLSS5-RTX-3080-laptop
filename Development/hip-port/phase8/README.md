# Phase 8：2-shfl Ampere D → AB 直通与零 spill 修正

保留2-shfl直通方案。最终50/80：**900p min26.486 / median26.837ms，1080p min35.237 / median35.790ms**；独立插桩帧核累计 **25.025536 / 33.181696ms**。两档对Phase7和归档Phase6输出0bit-diff、invalid=0、首末帧逐位一致，32/32活跃核CUDA LMem=0。

## 映射验证与接入

`sm86_d_bytes_to_ab` 已加入compat头。GPU测试用256个不同字节标签检查全部32×8位置的精确排列，再用4194304个随机half模式经实际FP8打包作比较，均0bit-diff。标签测试不受FP8量化碰撞掩盖：第一组直接打包0..255整数标签，结果仍包含256个不同值。独立bridge核实测PTX为2shfl、4selp、4prmt；这10条是布局数据搬运指令，未把lane地址计算的整数ALU算进来。

在已有CUDA源码后处理阶段加入 `hip/phase8_transform.py`，原HIP算法/权重格式保持原接口。C32命中3个代码段（W16/non-W16 expand、AV），wave2命中7个代码段（含两种FFN分支、contract、result、AV）。每个生产端在元素读取前改为 `unpack_acc(c_to_ampere(X))`，pack后使用D-bytes→AB。Q/K归一化、坐标偏置、残差的通道寻址和最终写出没有按此规则改写。

已有SSA pass删除成对C/D映射；小测试验证两个调用都消失，并经LLVM verifier检查。生成PTX中MMA数量不变。只允许同一元素映射在布局置换两侧交换；没有把带行列/通道权重的运算当作纯逐元素操作。

GPU[原语结果](primitive-results.json)、[测试脚本](check_primitives.py)、[bridge指令数](bridge-instructions.json)。这轮真实整网验证使用固定合成RGB、31块Small、Style1，两档处理1600×1024/1920×1152；没有用两张固定输入替代全部游戏内容测试。

## 控制变量与最终成绩

全部50 warmup / 80 iterations，GPU事件计时不含初始化、权重打包上传、最终读回。插桩核表来自额外单帧，不是80帧逐核均值。

| 方案 | 900p min / median ms | 1080p min / median ms | 非零LMem活跃核 |
|---|---:|---:|---:|
| 首轮Phase7基线 | 26.962 / 27.390 | 35.645 / 36.467 | 0 |
| 仅新C32 | 26.351 / 27.170 | 35.551 / 36.094 | 1 |
| C32+wave2新布局 | 26.760 / 26.998 | 35.421 / 35.995 | 1 |
| 新布局+直接强加bounds | 26.901 / 27.170 | 35.658 / 36.045 | 3 |
| 两模块低寄存器FP8表达式，mapped仍寄存器Q | 26.405 / 26.658 | 34.977 / 35.362 | 1 |
| mapped共享Q修正（实验构建） | 26.604 / 26.924 | 35.301 / 35.851 | 0 |
| 最后重跑Phase7基线 | 26.979 / 27.382 | 35.741 / 36.354 | 0 |
| **最终默认源码重编** | **26.486 / 26.837** | **35.237 / 35.790** | **0** |

最终配对median速度比1.0203×/1.0158×。原始带mapped 8B local的方案更快，明确保留为控制，没有把它的min与最终零spill方案median拼在一起。最终`selected-bench.log`是默认源码重编后的独立新运行，不是其他日志的别名。

全部输出对Phase7、归档Phase6逐位一致；FNV仍900p `b949727e624db210`、1080p `a8365381a41f7f83`。对F32可见PSNR46.9753/46.1009dB，maxabs0.04004550/0.04160273。

## 为什么bounds必须配合局部修正

直接按请求加 `(64,8)` / `(32,16)`，确实把OccW提高到16，但CUDA实际报告split FFN56/64B local、ViT project16B local。单靠bounds不能称为性能修复。

最终仅在 `vit-stream-fast`、`c512-m32-deep` 两个模块使用旧的、逐位等价的FP8 C++转换表达式；保留Phase7的常量裁剪、LOP3解包和Phase8 bounds，C32/wave2仍使用无分支FP8 asm。实现集中在 `low_register_fp8`，由builder按模块显式选择。恢复了：

| 核 | Phase7 Regs / OccW / LMem | 直接bounds | 最终 |
|---|---|---|---|
| split_ffn_one_w2f8_w16 / _bin | 186 / 8 / 0 | 128 / 16 / 56或64B | **106 / 16 / 0** |
| vit_stream_project_n64_bb_bout_compactw_w16 | 138 / 12 / 0 | 128 / 16 / 16B | **101 / 16 / 0** |

新布局使C32 mapped在168regs约束下出现8B local。只关闭它的寄存器Q（fast Q mask31→29，关闭kind1；prefix/up原本已共享Q），映射直通本身保留。mapped最终 **146regs / 10KB SMem / OccW9 / LMem0**，代价是从8KB/OccW11退回共享Q。其它三个主用寄存器Q核仍8KB、OccW11。

最终prefix153regs/10KB/OccW9，up217regs/10KB/OccW8。wave2主用C64/C128/C256为241/247/226regs、OccW仍8；不能声称直通已让其跃升占用率。

## 指令数和计时的实际边界

[PTX表](ptx-counts.md)同时列出原始布局方案和最终方案。主用prefix静态shfl269→229；mapped240→200；C64/C128/C256 bi_bo_w16均324→204。MMA分别仍84/80/100条。减少的是目标布局往返，不是核内所有shuffle都减少83%。表中含循环静态展开，不能直接拿条数当本帧动态次数或最终SASS。

第一轮基线插桩核累计900p25.687840ms、1080p33.750016ms；最终候选25.025536/33.181696ms。最终配对基线插桩为27.055104/33.813504ms，其中900p的C64 bi_w16和prefix出现较明显单帧抖动。完整表保留原始值，但不把27.055→25.026解释成稳定的逐核均值加速。

[32核完整分解与资源表](results.md) / [所有控制组JSON](results.json)。端到端分布与插桩单帧分开报告；不混用不同运行的min、median、核累计。

## 构建、产物和复测

原始方案完整 **40/40模块、1918 entry** CUDA编译加载通过，见`build.log`。资源修正后从最终默认源码重编3个变化模块，另37个复用完整构建产物；以最终40模块目录完成两档整网长测，实际执行32种活跃核。源文件快照、输入哈希和最终模块哈希在`artifacts/selected/`及`artifacts/build-inputs.sha256.json`。`selected-build.log`和`selected-run.json`记录来源，未把复用的37个模块说成第二次全部重编。

默认模块集：`artifacts/selected/modules/`。`bash Development/hip-port/phase8/run_benchmark.sh`可按当前默认源码重编全部40模块，再跑Phase7基线与候选50/80；其完整重编写入`selected-full-rebuild.log`，不会覆盖首次带spill的控制构建。

默认DVFS、约140W、显存7001MHz、未锁频。最后两次窗口GPU利用率>=95%样本的SM时钟中位数：基线1620MHz、候选1605MHz；功耗139.51/139.38W，温度63.5/69°C。窗口合并两档且含部分初始化，不冒充逐核等频统计。完整遥测保留。

原语、3个布局/SSA测试、已有3个IR测试及2个对齐测试通过，`git diff --check`通过。新模块仍需AMPERE_WEIGHTS_V2 Host。共享assets、Windows frame.exe/addon、游戏/Magpie与v0.1.0正式发布包未覆盖。
