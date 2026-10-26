# Phase20：一次联合half2激活探索，未升默认

基线Phase19 selected（18e3f46），只做C32+Wave2一个联合候选。直接从Ampere累加器half位计算clamp/abs、两次fma.rn.f16x2、mul.rn.f16x2，再half_pack及既有D→AB。C32保持-0，Wave2消-0；Q/K归一化、其它float/RTZ路径不动。

CUDA后处理替换原FP32激活分支，不走CW_FAST_NUM|4旧分支末尾的float回写。激活核心不含f32展开/算术/标量FP8编码；其它残差/归一化仍有FP32，不能说整个核没有FP32。

## 原语结果

GPU测试全部65536种half编码，其中有限63488种；C32/Wave2各有182个有限输入的输出字节变化（0.2867%），最大相邻1个E4M3幅值编码/ULP。在大数区1ULP对应最大数值差32，非“最大差1.0”。非有限输入字节变化0，按当前软件量化器口径比较，不扩称普遍IEEE FP8语义。

## 三档50warmup/80iter正反ABBA

A=Phase19，B=联合候选；GPU median ms：

|档位|A1|B1|B2|A2|均值A→B|速度比|
|---|---:|---:|---:|---:|---:|---:|
|720p|13.490|13.400|13.423|13.573|13.5315→13.4115|1.0089×|
|900p|22.762|22.552|22.615|22.871|22.8165→22.5835|1.0103×|
|1080p|30.576|30.326|30.366|30.780|30.6780→30.3460|1.0109×|

均值只是两次run median摘要；原始min/median/Wall和独立PROFILE_TOTAL按run保留。Small31/Style1、Graph off、默认DVFS，未锁频，不做等频或launch气泡声明。15次快验/正式运行全部invalid0、first-last0、32/32 LMem0；候选两次输出SHA完全相同。

## 误差与决定

固定peak1、可见区域编码RGB，候选相对Phase19及配对F32累加gold：

|档位|vsP19 PSNR dB|maxabs|vsF32 PSNR：P19→候选|候选vsF32 maxabs|
|---|---:|---:|---:|---:|
|720p|43.582691|0.050379157|43.577948→43.206459|0.052299023|
|900p|46.926900|0.036648065|46.975322→46.671080|0.051891208|
|1080p|46.763612|0.040914565|46.100947→46.312321|0.047206312|

相对P19三档均低于50dB；720/900相对gold分别下降约0.3715/0.3042dB。1080均方分数略好但maxabs较P19对gold的0.041602731更大，不能据单档PSNR改善说无损。逐层稀疏的量化边界变化会经深层传播，不由0.2867%原语变化率推断图像几乎无损。

**不进入默认、不列为无损推荐。** 提速仅约0.9～1.1%，未满足本轮质量条件。`PHASE20_HALF_ACT=False`，Phase19严格0bit默认保持；候选仅在phase20/artifacts/candidate/modules诊断保留，并带APPROXIMATE_ACTIVATION_F16X2标记，不要当Phase19模块。

results.md/json包含全部32核和C32/Wave2逐核耗时/REG/LOCAL/Shared/OccW，summary.json包含双重PSNR与maxabs。只做联合候选，没有归因到单独C32或Wave2；不追加第二候选或重新调参。

## 复测/清理

build.py显式启用实验开关，check_primitives.py生成原语对照；bench.py必须给新variant名。run.py保留本轮固定名，拒绝覆盖。三档gold引用Phase14修正720与Phase1既有900/1080，未更换gold、未放宽门槛。

20项既有Python/LLVM回归通过，输入/输出/模块SHA、参数、遥测与误差保留；重复RGB/临时probe编译产物清理。保护性核对v0.2.0主生产DLL/三ZIP均未变，无外部部署，不push。到此结束探索。
