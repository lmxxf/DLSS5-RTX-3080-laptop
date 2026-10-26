# Phase16：四个 ViT 尾写向量化

基线815d096 / Phase14 selected，Small31、Style1、Graph off。只改CUDA构建定义与ViT byte epilogue，未改算术、权重ABI、Host、gold或外部部署。deep_fast-packed / deep_fast-packed-fast / vit-stream-fast默认开启EXPAND/QKV/CONTRACT/PROJECT四个TAIL_VEC；只重编这3模块，其余37个按SHA复用Phase14，整套40模块实际加载1918入口。

## 实现与指令验证

- expand沿用既有16×64 LDS转置；project新建1024B转置区；contract复用原4096B occ_pad；QKV复用各warp已经结束归一化读取的raw区。warp内同步后每lane写连续16B，地址与量化表达式保持。
- 实际compactw_w16入口已核验，profile显示的短名不是另一个kernel。见isa.json：

| 核 | PTX u8写 基线→候选 | PTX v4.u32 / SASS STG.128候选 | Regs 基线→候选 | Shared 基线→候选 | OccW |
|---|---:|---:|---:|---:|---:|
| expand W16 |32→0|2 /2|80→85|0→1024|16→16|
| contract compact W16 |32→0|2 /2|106→102|4096→4096|16→16|
| project compact W16 |32→0|2 /2|101→103|0→1024|16→16|
| QKV bin W5F8 |16→0|1 /1|119→119|16384→16384|15→15|

保留现行FP16 LDS权重staging；没有实施可选的FP8 LDS瘦身，不将其混入尾写收益。

## 数值和性能

三档各两组ABBA，全部50warmup/80iter；24次正式运行均相对Phase14 default400归档完整输出0 bit-diff、invalid0、first/last0，32/32活跃核LMem0。18项既有Python/LLVM回归通过，另增加1项构建转换回归，防止packed_total只在标量fallback里还原。真实HDR观感不属于本轮性能验收。

| 轮次 | 档位 | A1 /B1 /B2 /A2 GPU median ms | B均值−A均值 ms |
|---|---|---|---:|
| 首组 |720p|14.102 /14.087 /14.083 /14.146|-0.0390|
| 首组 |900p|23.628 /24.193 /23.712 /24.309|-0.0160|
| 首组 |1080p|32.091 /31.915 /32.402 /32.326|-0.0500|
| 确认 |720p|14.173 /14.444 /14.432 /14.899|-0.0980|
| 确认 |900p|25.241 /24.444 /24.437 /24.518|-0.4390|
| 确认 |1080p|32.538 /32.606 /32.463 /32.592|-0.0305|

默认DVFS、未锁频/改功耗。每组两次median的均值只是简表，不能当成单次实测帧统计；第二组900p基线抖动明显，不把0.439ms认作可靠因果收益。结论为**尾写向量化/数值/零spill目标达成，整帧小幅正向但收益接近噪声，不能宣称稳定百分比或按写指令减少量推算加速**。按任务要求保留四处默认开启，不再追噪声重复试验。

四核各自两组ABBA插桩时间完整列于[summary.md](summary.md)，全部32核/每次GPU min、median、Wall、独立PROFILE_TOTAL见[results.md](results.md)。插桩帧与整帧median不混作同一帧；首组1080p A1 expand/contract分别1.434624/1.692672ms，有明显抖动，未拿它们单独算加速。逐运行窗口遥测在telemetry-summary.json，原始CSV保留。

## 开发中捕获的失败

首版contract新分支插在旧Phase2 pass的最终还原之前，读取到初始化total。quick三档差异分别2945598/4909514/6628967元素，未进入正式计时。将两种尾写放进唯一外层!Partial尾部，使旧pass在共同入口还原packed_total，修复后所有正式输出0bit；test_tail_transform.py检查实际生成源码的还原顺序。quick失败日志保留，错误模块不保留。corrected-quick发生于构建末段，视为中间控制；final-quick及正式ABBA均使用完成构建后的固定模块。

## 复测与产物

```bash
python3 Development/hip-port/phase16/build.py
python3 Development/hip-port/phase14/verify_modules.py --modules Development/hip-port/phase16/artifacts/tail/modules
python3 Development/hip-port/phase16/run_benchmark.py --tag my-retest
python3 Development/hip-port/phase16/check_quality.py
python3 Development/hip-port/phase16/inspect_isa.py
```

run_benchmark拒绝覆盖已有运行名；每次调用前核验Phase14模块，run.json冻结实际Host/40模块SHA、环境与时窗。Host复用Phase14正式无强制选桶版本。build只重编3个受影响模块，实际加载检查所有40/1918。最终源码重编需与measured-modules.sha256.json一致。

保留最终40模块/PTX/3份生成源、SHA和日志；清理临时LLVM、phase1中间源和重复RGB。输出清理前逐文件SHA/bitdiff已验证，重测可从唯一Phase14参考重建。不push，不改ptx-patcher、共享assets、游戏/Magpie或发布包。下一阶段按主脑计划为Phase17 C32权重预解码，本轮不启动。
