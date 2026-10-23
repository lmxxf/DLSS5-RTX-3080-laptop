# HIP / HLSL同输入层比较（2026-09-15）

本次只做诊断，不改变推理算法或游戏安装。测试当前HIP候选e847b44路径（qkv-modules），与实际HLSL生产类及900flags；RX9070XT，已有预览驱动。两端共享相同逻辑输入和实际层尺寸、权重；数据提前上传到各自的GPU默认内存。输入为两种确定性pattern，不是现场游戏中间张量。

每个案例预热20次，HLSL/HIP/HIP/HLSL四批，每批20次调用，只在批结束等待。下表为最终pattern1两批均值，单位ms；HLSL同时记录GPU timestamp，HIP栏为完整批量墙钟。因此比较的是实现成本，不是孤立硬件指令吞吐率。不能把代表层直接求和当整网总时间。

| 层/边界 | HLSL墙钟 | HIP墙钟 | HIP/HLSL | 不同元素数 |
|---|---:|---:|---:|---:|
| C32 post70，显式pack | 1.705 | 3.320 | 1.95 | 0 |
| C32 post70，HLSL mapped | 1.063 | 3.408 | 3.21 | 0 |
| C32 block1，HLSL mapped | 0.309 | 0.817 | 2.65 | 0 |
| C32 block4，raw-chain | 0.291 | 0.878 | 3.02 | 0 |
| MH block5 C64 | 0.314 | 0.702 | 2.23 | 0 |
| MH block6 C64/shift3 | 0.323 | 0.739 | 2.29 | 330 |
| MH block9 C128 | 0.226 | 0.436 | 1.93 | 496 |
| MH block15 C256 | 0.210 | 0.318 | 1.52 | 129 |
| Split block23 C512 | 0.145 | 0.285 | 1.97 | 0 |
| ViT block31/400 tokens | 0.201 | 0.626 | 3.11 | 0 |

## 数值与比较边界

- C32返回窗口排列的raw half，不计没有消费者的finish；HIP包含raster→window pack。HLSL mode0也显式pack，mode1直接映射raster，mode2直接读取预先上传的half raw tiles，采用三分量残差。HIP按同一残差模式运行。mode1/2保留了HLSL消除搬运的实现优势，不将其藏掉。
- 最初block4错误地用HIP三分量残差对HLSL普通模式，产生大差异；正式测试已按模式对齐。最初先创建小C32实例导致共享scratch不足，已改最大post70先创建。失败轮次不纳入表。
- pattern1的C32、C64 block5、C512、ViT输出逐位相同。block6/9/15仍有少量差异，最大绝对差0.5/2/2；不能把它们说成已证明等价。pattern0在其他层也出现少量差异，ViT7906/409600元素不同（max2），显示既有数值对齐问题仍在。两pattern均无非有限输出。
- HLSL移位/投影融合、输入布局和FFN融合均使用实际生产选择。通道512/1024使用NativeSplitWindow/NativeVitBlock，不用不支持它们的NativeC64Shift硬套。

## 已确认的实现差别

1. C32：HLSL mapped路径省掉显式pack。post70在同一组测试中显式pack约1.705ms、mapped约1.063ms；HIP总计约3.408ms。HIP独立内核批量诊断pack约0.719ms、融合核心约2.649ms，说明差距不全是搬运。HLSL源码保留FFN矩阵结果在寄存器，按wave使用局部scratch；HIP通过half共享数组、逐Q/K/V平面处理，并多次使用全workgroup barrier。HLSL FAST4还按每组两个窗口组织工作，HIP每组一个窗口。这里只确定结构差别，未把每种差别的贡献分别量化。
2. MH：运行时打印确认fused_ffn=1、fused_shift=1、fused_qkv_norm=1、fp8_stream=1；fused_proj0=0、attn_fused_qkv=0。HLSL展开放大隐层后直接在LDS里收缩，不把hidden写回显存；HIP虽然已用byte存放，仍是expand、contract两个内核。HLSL输入映射/输出投影融合了shift，HIP仍有独立pack/crop。
3. ViT：运行时确认expand/contract/projection tiled=1、contract SplitK=1、fused_ffn=0。HIP当前每wave16×16输出，contract四个K分段在同一内核串行计算；HLSL有权重预重排和并行Split-K。HIP batch诊断expand约0.216ms、contract约0.125ms、QKV projection约0.201ms，是ViT主要候选。没有将这些孤立核时间与整层直接相加声称精确分解。

## 诊断方法

HLSL细分使用单命令列表中的GPU时间戳。HIP细分在原调用位置重复同一无副作用内核20次，再同步、除以20；连续做三轮。明确包含launch/wait摊销和缓存条件影响，不冒充纯GPU时间；每轮结束逐位验证结果仍等于正常流程，防止重复执行改变输入。原单次同步的HIP细分数值偏高，最终报告采用批量版。

复现：编译Development/HIP/compare_layers.cpp（MinGW C++17，链接d3d12/dxgi/d3dcompiler/dxguid），在9070实验目录运行compare-layers.ps1 -Pattern 0或1。脚本检查游戏退出，读取独立flags和qkv-modules。诊断friend与重复调用仅在DLSS5_LAYER_BENCH宏下开放。原始CSV/log在release/HIP/layers-p0.*、layers-p1.*、layers-final-p1.*；最后一组额外包含hip-phases.csv。所有文件仅为实验产物，游戏DLL/HSACO未更换。
