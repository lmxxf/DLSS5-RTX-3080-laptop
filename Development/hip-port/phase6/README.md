# Phase 6：LLVM IR 对齐升级与原生向量读写

`upgrade_ir_alignments` 已在SSA抵消末尾和第二次O3后、llc前两处调用。共享global至少16B（不降低已有更强对齐），标量i32/float至少4B，8B传输至少8B，16B传输至少16B。可针对模块降16B传输到8B，但本轮默认16B通过实际数值测试，没有采用fallback。

完整 **40/40模块、1918 entry CUDA编译/加载通过**；两档均没有misaligned-address错误，整网与Phase5基线0 bit-diff、invalid=0。该对齐提升依据本工程CUDA tensor布局，不是任意IR都可无条件套用的通用合法化。

## 选型与资源回退处理

原始16B方案使prefix在原寄存器约束下新增32B LMem。分别测试：C32 16B上限降8B、放松C32约束、补half自然2B对齐，都没有取得两档明确更快的结果。没有将这些试验变成默认。

最后只将prefix改回共享Q：`SM86_C32_REGISTER_Q_MASK=31`（prefix bit5和up bit6关闭），其余四个非up核仍为8KB寄存器Q，原有minblocks9不变。此控制**消除了prefix的32B LMem，恢复32/32零LMem**。原始16B版本与它的长测差分别只有1080p0.093ms、900p0.019ms；默认选择零spill版本，保留原始16B方案便于用户比较。

prefix最终152regs/10KB/OccW9；另外四个非up核167～168regs/8KB/OccW11；up仍234regs/10KB/OccW8。对齐本身没有让wave2峰值大降（242～250regs、OccW8），所以本轮没有再盲目强压wave2 launch bounds。

## 长测结果

50 warmup/80 iterations，Small31-block、Style1、确定性合成RGB输入；900p/1080p实际处理1600×1024/1920×1152。GPU与Wall不计初始化、权重打包/上传及最终读回。

原始16B控制：900p min27.336/median27.666ms，1080p min36.292/median36.798ms。默认零spill方案的完整数据与Phase5同轮基线见[32核表](results.md)及[JSON](results.json)。不要把控制组的min与默认方案median拼成一套成绩。

推荐方案两档输出对Phase5基线0 bit-diff，首末帧逐位一致，invalid=0；对F32可见PSNR保持900p46.9753dB、1080p46.1009dB。仅验证当前输入/模式，不当作全部游戏内容的画面验收。

**900p已进入20～30ms区间；1080p仍约37ms，未达到30ms。** C32六个主用核占当前插桩累计约一半，已经成为下一步更明确的瓶颈；静态模块里未执行入口的字节指令不应全部当成本帧动态工作。

## 指令与寄存器证据

- [40模块PTX统计](ptx-counts.md) / [完整opcode JSON](ptx-counts.json)：区分global/shared、ld/st、标量u8与32位元素v2/v4。
- C64/C128主用bi_bo_w16核：global/shared四类标量u8由288/16/168/160降为0，变成原生word向量。其PTX约14213→12870行，而不是沿用更早版本21576行的分母。
- C256 bi_bo_w16也清掉上述四类u8。静态模块仍有合法字节访问、gather及未执行legacy入口，不能声称全模块所有u8都已清零。
- 原始16B全模块LD global u8总计141625→9669，LD shared u8 86848→37640；最终prefix共享Q略改变一个C32模块，最终表使用默认模块数据。
- ViT contract/project降到106/101regs，OccW提升到16；split FFN106regs/OccW16，部分C512/attention也下降。wave2仍高，完整32核表保留实际资源变化。
- 发现prefix部分half标量load在IR中仍为align1，即便附近已有16B assume；half2单独控制保持数值但没有一致速度收益，未扩大默认规则。

## 产物、复测与限制

最终 `artifacts/selected/modules/` 有40个模块，默认源码重编的C32 fast与零spill长测控制整个cubin相同；其余39个模块直接沿用已完整构建的16B集。`selected-bench.log` 明确引用同一次prefix-shared-q长测，不伪造独立重复运行。

`build.log` 为完整40模块构建记录，各C32控制的构建与运行日志保留；哈希、功耗、时钟在对应JSON/CSV中。源码对齐测试通过LLVM verifier，最终模型验证真实运行在RTX3080 Laptop。

复测入口：`bash Development/hip-port/phase6/run_benchmark.sh`，默认50/80，可传两个数字。依赖已归档Phase5基线和Phase1 F32输出，主脚本只复测当前默认，不自动重跑全部控制。

默认DVFS、约140W上限、未锁频；速度为同轮实测，不宣称等频倍数。900p达标、1080p继续优化，不能以目标值替代测量值。

本轮只更新源码与实验模块。外部共享assets、游戏/Magpie、v0.1.0发布包未替换；新kernel仍需配套AMPERE_WEIGHTS_V2 Host。

最终默认（prefix共享Q）的50/80结果：900p **min27.315 / median27.685ms**，1080p **min36.538 / median36.891ms**；CPU Wall median27.781/36.982ms。对同轮Phase5基线median36.671/49.394ms，速度比1.3246×/1.3389×。插桩累计36.1032→26.1212ms、48.5038→34.3603ms。默认32/32零LMem。

遥测CSV覆盖同轮基线和原始16B长测：SM时钟中位数基线1080p/900p1665/1687.5MHz，原始16B均1620MHz；显存7001MHz，负载功耗中位数约138～140W。prefix共享Q最后一组没有额外分段遥测，不冒充等频测量。主要提速幅度远大于这些时钟差异，但不据此构造固定频率速度比。
