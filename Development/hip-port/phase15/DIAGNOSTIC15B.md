# Phase15B：1024² codec-ramp质量差异诊断

起点23ca274；只新增/修正phase15诊断脚本和文档。**没有生产默认、内核、权重、gold或45dB门槛修改，没有性能实验/计时，没有push/部署。** 真实HDR素材缺口仍在，本报告不是实机画质验收。

## 结论与边界

本次证据支持**既定FP16累加/量化误差的累积传播，以及图案与几何的交互敏感性**，没有定位到另一处可提交生产修复的索引/布局错误。误差最早可观测于融合prefix/C32的输出，后续C32链和C64/C128编码器已有差异；主要沿深层low分支送到post，输出头不是主要新误差源。

已对代表性矩阵算子、全部实际ViT attention参考及输出头做独立核验；**没有对所有融合编码器的每条MMA做完整CPU形式证明**，不能宣称穷尽排除所有bug。当前没有生产最小修复依据，不建议修改默认；低于45dB的质量限制依然存在。

另外确认一项**诊断工具时序错误**：旧tap在`PrepareForExternalInput()`前开启，first-seen缓存截获了全零预热。本轮在Prepare结束后arm，并读回prefix实际消费RGBA，严格比对冻结输入SHA。历史QKV数值fixture保留，仅纠正phase15的来源描述；旧图像gold本身在Prepare后用实际输入生成，未受此归属错误影响，也未被替换。

## 1. 冻结证据与tap可信性

目标 `1024-square/codec-ramp-wp1` 的工作输入SHA：

`df3f5b8c367b33a9b6c72acc2237a464091628748886949202982b216c7b8a9c`

Native输出SHA `2068016ee637edf827c3014ebf2eae98781a41eeba59adf8dc006120aa9be2ec`，F32输出 `02de4ded9480b1c98b59672bd8d9097cb3ca0eeeba5b27266dedb6adc0c502e3`。重建输入与实际prefix读回RGBA均匹配；所有有冻结结果的对照，tap最终输出全部0bit，输入重复/资源重放也未改输出。

只在忽略目录的Host头副本插入只读Stage/Run读回，不装observer或dump_dir，防止改变raw/inter-byte门控。生产流不写回中间张量。后文同输入重放使用复制输入、自有输出/feature缓冲，不注入原网络。现有post-features导出重放与原post RGB0bit后，才接受其feature用于CPU分析。

旧fixture输入归属有直接SHA证据：720p Prepare产生的F32 QKV仍为`2f235997...60193a`、Native为`0b6457a7...e5efb5`，与历史fixture逐字节相同；实际canonical输入的QKV分别是`2d750f1c...22cb70`、`cec8d872...c5ef3`。Prepare的prefix输入所有字节为零。最小工具建议是**Prepare后启用 + 实际消费输入SHA门控**；本轮新脚本已经落实，不改旧数据或生产默认。

## 2. 首次差异及阶段传播

下面是实际冻结输入的特征NRMSE（相对对应F32特征RMS）。融合prefix内部stem投影和C32没有分开，故只能定位到**最早可观测融合边界**，不虚称已经确定stem内部第一条错误指令。不同阶段特征维度/幅值不同，这些数不能直接相加成图像MSE贡献。

| 边界 | ramp1024 NRMSE | canonical720 NRMSE |
|---|---:|---:|
| prefix/C32 pre-down | 1.72% | 1.70% |
| C32链block4 | 5.11% | 5.37% |
| C64尾block8 | 9.97% | 13.58% |
| C128尾block14 | 14.29% | 13.55% |
| C256尾block22 | 15.81% | 14.28% |
| ViT入口head | 6.27% | 6.77% |
| ViT block31输出 | 7.30% | 7.59% |
| ViT block38输出 | 13.03% | 12.44% |
| decoder39输出 | 12.15% | 11.70% |
| C32 low block69 | 10.29% | 11.27% |

没有到256token首个ViT块才突然出现大跳变。C64/C128的同输入独立F32重放也表明，上游输入差异在相应输出误差中很重要；局部误差与上游误差的交叉项为负，不能简单按MSE相加或宣称唯一百分比。完整边界/八个ViT expand-contract-QKV-attention节点见`diag15b-stages.md/json`；同输入重放见`diag15b-branches.json`。

特征字节按Host合同解码FP8/half/float；Native head/ViT为byte，旧F32参考部分为float，均先转数值域。没有直接拿不同表示的原始字节差当数值错误。

## 3. 主要最终误差从哪里来

通过F32 post独立重放区分上游输入与post局部精度。设N/F为各自产生的low+skip；使用F32权重/算子重放`F(N)`，原生产流始终不变：

`D = Native(N)-F32(F) = [Native(N)-F32(N)] + [F32(N)-F32(F)]`

目标图像RGB MSE：

| 项 | MSE |
|---|---:|
| post同输入局部差异 | 1.310395e-6 |
| 上游输入差异经F32 post传播 | 4.532030e-5 |
| 两项交叉项 | -1.307616e-6 |
| 最终总MSE | **4.532307e-5** |

再分别只替换F32重放的low或skip：low-only MSE **4.495393e-5**，skip-only **2.458037e-6**，二者非线性交互RMS0.002063921。最大独立分量来自**深层主干/decoder产生的low输入**，不是prefix skip单独或最终RGB合成。low分支本身包含早期C32、编码器、ViT和decoder的累积，不能据此错误地锁定一个ViT算子。所有反事实MSE均保留交叉/交互说明，不将它们当可直接相加的“贡献率”。

现有post-features导出在8个Native/F32运行中与原RGB逐位相同。用读回half32特征、实际GPU head权重、原working color独立CPU重算，**整个输出头逐位匹配**，包括同输入F32重放。这里`CW_FAST_NUM=3`下head的`Hrtz`是identity；实际feature RTZ仍按源码保留，没有擅加RTZ或更换倒数算法。该核验将最终差异追溯到不同feature，而非输出头索引/裁剪实现。

## 4. 正常数值差异的独立证据

### 首个ViT expand：原始矩阵加载与CPU舍入核验

不用CPU Ampere预打包布局，独立按原始行主序读取同一captured FP8输入和原始权重，调用对应精度MMA后执行原FMA多项式/FP8量化。四个输入中Native和F32各自均与生产输出逐字节一致，排除所查算子的预洗牌/权重加载/输出布局差异。

每输入检查4个完整token行（含边界/最大局部差异token），共 **65536个预激活值**：CPU按K8分组FP16 RNE模型与GPU逐位相同；另有48个极值/分布点相同。简单K16一次舍入模型通常不匹配。本结论限定于本机这些实际操作数，不外推成所有TensorCore实现的ISA精度保证。所查预激活无NaN/Inf。

目标expand输出特征MSE分解：同输入局部精度8.227442e-4，上游输入5.754867e-2，交叉-8.150032e-4，总5.755641e-2。局部FP16舍入能被独立模型复现，但已经传入的特征差异更大，不能把该算子单独叫“真凶”。详见`diag15b-expand.json`，含CPU点、原始权重SHA与完整行统计。

### 实际输入的ViT attention CPU核验

4个图×8块实际输入（240/256token），独立CPU计算QK、概率位映射、分母与PV，只用独立CUDA单指令匹配原`rcp.approx.ftz.f32`口径：**8126464个F32 AV字节全部一致**。这次样本在Prepare后捕获，包含冻结目标图；没有用GPU attention结果当CPU答案，没有换gold或改近似倒数。`diag15b-attention-cpu.json`。

上述数值证据与逐阶段平滑传播支持既有低精度路径的数值误差解释。尚未对所有融合C32/C64/C128/C256内部做完整CPU证明，因此不把“没发现具体bug”扩大为全网数学形式证明。

## 5. 空间、通道、幅值与几何

| 输入族 | 720p（可见720） | 1024² |
|---|---:|---:|
| canonical解析图案 | 43.577948dB | 43.551106dB |
| 同一codec-ramp源 | 47.234802dB | **43.436806dB** |

canonical换几何几乎不变，ramp却对重采样/几何敏感；不是所有图案在256token一律退化。同一1024²/N256水平反射平移1/8pixel，分别43.592593/43.480834dB，也未出现固定尾块异常。这些是输入敏感性对照，不是严格几何因果证明或平移等变性证明。

目标ramp1024：

- RGB误差SSE比例 **33.30% /33.79% /32.91%**，没有单一色道主导。
- |error|中位0.00420436、99%分位0.01880334、最大0.05438286；最高1%像素仅占6.67% SSE，误差分布较广，不是少数坏点。
- 任一输出恰好裁剪到0/1的分量占3.76%，只占0.56% SSE；饱和裁剪不是主要能量来源。输入工作亮度0.1～0.5区域占约70.4%面积、72.2% SSE。
- 最后64行相对内部MSE比 **1.009**，没有最后16token行的误差尖峰；post 8窗边界/内部比1.118，与canonical720的1.099接近。轻微窗边界相关性不足以证明索引错。
- F32 post特征RMS为2.22090（ramp720为1.55077），特征误差RMS0.23820（ramp720为0.14845）：相对误差约10.7%/9.6%，绝对特征规模更大，经过同一线性输出投影形成更大的RGB误差。不能只由PSNR低倒推出bug。

全空间统计见`diag15b-spatial.json`；共享色标图见`artifacts/diagnostic15b-replay/spatial.png`。图/窗/尾部统计用完整处理面，PSNR使用可见面，避免把720p镜像行当真实可见区。输入工作域仍0..1；本报告没有把原始HDR512直接送入模型或声称检查了真实游戏HDR量程。

## 6. 决定与下一步

**不建议当前提交任何生产“修复”。** 已检查的数值段符合原FP16/FP8及F32近似口径；没有定位到具体错误索引/指令，不能以低于45dB为理由改默认。43.436806dB与43.577948dB仍未过45dB，不更换gold、不放宽门槛，不宣布实机画质验收。性能线继续暂停。

若继续收窄质量来源，优先对早期C32链（role1/4）及C64融合编码器做逐MMA同输入舍入轨迹，核对FP8阈值翻转和传播；这仍是离线质量诊断，无需空等HDR，也不自动开启Phase16或性能实验。真实HDR缺口作为独立验收项保留。

## 可复测入口与保留证据

```bash
OPENBLAS_NUM_THREADS=1 python3 Development/hip-port/phase15/run_diag15b.py --tag diagnostic15b-another
```

完整入口已用`diagnostic15b-replay`实际重放通过，包含输入SHA、Prepare后tap、同输入scratch算子重放、CPU、空间/位移对照与验证。新tag防覆盖；只写phase15 artifacts和诊断摘要。需要本机既有Phase14/Phase1冻结模块及只读权重，旧gold不动。

`diag15b-validation.json`记录范围与限制；大原始层dump可重建，清理后保留目标热点小样本、输入/输出及完整SHA清单。不要在中间dump已清理后直接跑依赖它的子分析脚本，使用完整入口重新生成。临时模块/图均不进入Git。
