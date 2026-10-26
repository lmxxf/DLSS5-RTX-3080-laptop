# Phase19 收官：C64+C128 W16 FFN追加FP16，采用默认

基线Phase18 selected（4900cef）；仅两候选：mask1=C64，mask3=C64+C128。未做CW_FAST_NUM|4非0bit激活实验。

## 实现与边界

复用Phase17精确AmpereFp8HalfBits，把已预洗牌的W16 FFN expand/contract/mix三矩阵追加为FP16，所有旧偏移/尺度保留；消费点ld.global.nc.v4.u32读取sm86_u4送同一MMA。C256回到原FP8读取；Up/其它Frag8路径和attention/diag未扩展。范围没有扩大到其它矩阵或更多候选。

|通道|原FFN缓冲B|新B|追加half元素|
|---|---:|---:|---:|
|64|147712|221440|36864|
|128|590336|885248|147456|

CPU合成原语覆盖源字节模式，确认旧前缀逐字节不变、追加值/区域偏移准确；解码器GPU全字节证明沿用Phase17。两个候选各三档整网快验和ABBA均严格0bit、invalid0、first-last0、32/32 LMem0，所有活跃C64/C128仍≤168regs /OccW≥12。不是以有限域近似换速度。

`AMPERE_WEIGHTS_W19`内容1/3与`w19m1_`/`w19m3_`Wave2导出命名空间配对；新Host交叉核验，错标记及旧Phase18 Host均被拒绝，防止读取旧偏移时静默误用。原C32 V3标记/ABI不变。

## 50warmup/80iter三档ABBA

A=Phase18，B=候选，单位ms；均值仅为两个run median的摘要，不拼min/median或当成单次帧：

|候选|档位|A1|B1|B2|A2|均值A→B|
|---|---|---:|---:|---:|---:|---:|
|C64|720p|13.575|13.606|13.613|13.650|13.6125→13.6095|
|C64|900p|22.895|22.889|22.929|22.993|22.9440→22.9090|
|C64|1080p|30.695|30.709|30.824|31.178|30.9365→30.7665|
|C64+C128|720p|13.939|13.861|13.916|13.937|13.9380→13.8885|
|C64+C128|900p|23.341|23.256|23.229|23.289|23.3150→23.2425|
|C64+C128|1080p|31.208|31.069|31.116|31.214|31.2110→31.0925|

C64-only有方向不稳/接近零，1080p A2漂移较大，不拿其均值单独宣称收益。mask3六次配对均更快，速度比约1.0036/1.0031/1.0038×，选 **C64+C128** 默认；这是小幅0.3～0.4%，不按跨轮绝对耗时选型。默认DVFS，不锁频；遥测和所有min/median/Wall/独立PROFILE_TOTAL及32核原始表保留，不做缓存常驻/等频因果或气泡预算声明。

本次实际只追加4个W16缓冲（block5/65 C64、block9/61 C128）；总1476096→2213376B，新增737280B。不能把全部7个核预算都当成本轮覆盖，也不能由小于4MB推出100%L2驻留。weights.json给出实际上传记录。

## 验收与产物

24次正式ABBA+6次快验全部对Phase18严格0bit。实际加载40模块1918entry，仅c64-wave2-fast变化；默认源码重编SHA与实测相同，20项Python/LLVM回归通过，两个ABI反例拒绝。最终默认`PHASE19_WAVE_HALF=3`，产物`phase19/artifacts/selected/modules`、新Host `phase19/artifacts/benchmark_cuda_nn`必须配套；selected-modules.sha256.json冻结。

重做两候选用build.py，bench.py必须用新variant名防覆盖；run.py保留原固定tag，原始结果不可覆盖。Host原语可编译host_probe.cpp；所有源和参数保留。summary.md/json、results.json、precheck.json和validation.json提供完整口径。

临时重复模块/输出清理，最终模块/PTX/生成源、三份真实候选输出、日志/遥测/SHA保留。保护性核对外部v0.2.0生产DLL/三ZIP哈希未变；不部署、不push。本轮收官，不追加扫描或非0bit实验。
