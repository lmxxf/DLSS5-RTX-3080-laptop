# Phase 4：分段累加器预初始化、Stage 3 qt 滚动、小通道 W16

当前独立引擎最优基线取自 Phase 3 的 **共享 Q + 900p compact/C256 新门控**。本轮保留其数值输出，C32源码也恢复共享Q默认；不使用Phase3的8KB local-Q实验。

最终保留的三项：

1. ViT contract/project 在partition循环前初始化packed_total，循环内不再读取旧f8 total。
2. wave2 Stage3的两处qt循环禁止展开。
3. c64-wave2与c64-wave2-fast设置 `W2_FFN_W16_SMALL=3`、`W2_FFN_QT_SMALL_MASK=3`，开启C64/C128宽加载与双qt复用。

所有修改已进入默认源码/构建配置。最终 **40/40模块，1918 kernel entry 编译与CUDA加载通过**；完整模块集位于 `artifacts/selected/modules/`。未覆盖共享assets、游戏、Magpie或v0.1.0发布包。

## 最终同轮成绩

Small31-block、Style1、50 warmup/80 iterations。900p处理尺寸1600×1024，1080p处理尺寸1920×1152。GPU event与CPU Wall均不计初始化、权重打包/上传及最终读回。

| 档位 | 共享Q基线 min / median ms | Phase4 min / median ms | median速度比 | Phase4 Wall median |
|---|---:|---:|---:|---:|
| 900p | 40.364 / 40.793 | **38.763 / 39.442** | 1.0343× | 39.521 ms |
| 1080p | 53.460 / 54.126 | **52.252 / 52.845** | 1.0242× | 52.942 ms |

两档对所选基线 **0 bit-diff**、首末帧逐位一致、invalid=0、32/32实际CUDA LMem=0。对F32可见区域PSNR保持 **46.9753 / 46.1009 dB**，maxabs保持0.04004550 / 0.04160273。仅验证本次确定性合成输入与模式，不当作所有图像/设置的画面验收。

[完整32核表与分步数据](results.md) / [JSON](results.json)。额外插桩帧累计：900p40.5350→38.5116ms，1080p53.2900→51.9936ms；不与未插桩整网时间强求相等。

## 分步验证

### 1. ViT预初始化有效，且不改变数值

`vit_contract_blocked_body` 的packed_total初始化放在W16/Frag分支之前、partition循环之外；project初始化放在W16 skip初始化之后、p循环之前。保留独立partial的原有半精度舍入边界。

- contract **217→150 regs，OccW8→12**；project **210→155 regs，OccW8→12**，LMem=0。
- 900p最终核累计：contract2.7556→2.1780ms，project1.0875→0.8940ms。
- 1080p对应3.3720→3.3096ms、1.3834→1.3629ms；资源改善未等比例转化为该尺寸的时间收益。
- 单独预初始化、后续每个有效候选均对基线两档0 bit-diff。

可选的“用running total初始化partial MMA”并非等价代数消除：GPU反例先计算+2048、再−2048，单独partial求和再加初值1得到1，而把1提前塞入MMA累加得到0（256个输出均复现）。因此本轮没有采用这项会改变舍入边界的变形，见 `primitive-results.json`。

### 2. qt滚动缩小了代码，但未把wave2降到168regs

仅禁用Stage3两处qt展开：C64/C128代表核机器码237568→173184B（−27.1%），C256代表核267648→198272B（−25.9%）。GPU输出逐位一致，实际LMem=0。

波峰寄存器仍 **250、OccW8**；“qt展开就是整个峰值的唯一来源”未得到支持。后置SSA中已可见 `<4 x i32>` PHI、相应代表核 `<8 x float>` PHI为0，不能仅凭有packed PHI就推导总Regs必达168以内。

另外独立测试了只滚动QKV kt、滚动Stage1/2/3/5相关kt。**9个实际活跃wave2核的最终机器码均与只滚动qt版本逐字节相同**；故未把这些无额外效果的显式kt pragma保留在默认源码。中间PTX出现local depot不等于GPU实际spill，此处以加载后的CUDA属性和运行结果为准。

### 3. 小通道W16/双qt复用确实更快，保留mask=3

加入两个宏后Host实际选择了C64/C128的 `_w16` 导出；未提供宽导出的HO/up路径仍按其有效代码执行，不将所有核都标成宽加载。

- 1080p：C128 bi_bo累计2.3736→2.0593ms，C64 bi_bo1.5002→1.3486ms。
- 900p：C128 bi_bo1.9272→1.5831ms，C64 bi_bo1.1244→1.0117ms。
- 输出仍0 bit-diff、LMem仍0；wave2峰值250regs/OccW8未解决。

## 证据与复测

- `baseline-bench.log` / `selected-bench.log`：最终50/80。其余候选日志为pilot（qt-only5/10，其余10/40），不能混作同样样本数。
- `wave2-machine-code.json`、`all-active-kt-machine-code.json`：cubin ELF机器码比较，不是PTX字符比较或GPU pipe利用率测量。
- `loop-ssa.json`：清理前捕获的后SSA循环类型；原始更大文件在被忽略的artifacts中。
- `modules.sha256.json`、`build-inputs.sha256.json`、`retained-selection.json`：完整模块集、源与选项。
- 各候选 `artifacts/<variant>/source/` 保存构建输入；父模块集中只替换受影响模块，最终又用默认配置重编了全部40模块。

本轮Host实现未变，实验沿用Phase3 runner；复测脚本会从源码重编。运行 `bash Development/hip-port/phase4/run_benchmark.sh`，默认50/80，可传两个数字。依赖本机Phase3共享Q模块基线和Phase1 F32输出档案；未保留的kt试验不自动重跑。

默认DVFS、约140W上限、未锁频，显存7001MHz。基线1080p/900p长负载SM时钟中位数1710/1740MHz，候选1695/1710MHz；完整功耗和时钟在telemetry文件中。所有速度为同轮实测，不宣称严格锁频因果比例。
