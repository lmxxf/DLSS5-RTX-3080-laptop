# 路线 B V2：偶奇 K16 零洗牌拆解

起点c77a689，原始310.9.16.0输入SHA门控不变。`fast_render_fp8_mma_run`默认改为同lane偶/奇字节解包，A四寄存器和B两寄存器使用同一个K置换。保留multidef_nq资格检查，不加mapped量化；mapped源用5410/7632两条PRMT组合。原拆解保留为`--mma-layout legacy`诊断，不作为默认。没有修改上游通用patcher、正式发布ZIP、游戏或Magpie部署。

## 产物

- `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v2.dll`
- **266,414,592 B，15/15 O4，15/15原槽位，无新增PE节**。
- SHA256 **737af93c2843fe18462c39da36a0a482e4d410493bed0e178fecabf526880f74**。
- 源DLL及旧生产fast哈希重新核验未改。完整身份/PE坐标见identities.json、pe-manifest.json；编译与实际CUDA加载15个Fatbin记录见build.log。

## 正确性先验

GPU遍历每个奇偶位置全部65536个字节对，其中254²=64516个有限E4M3组合均与独立数值解码0bit；保留±0/subnormal。映射PRMT覆盖65536组half原始位标签。独立768个A/B标量槽坐标证明均满足原K=2×K16+parity；64组实际生成MMA，对独立CPU整数矩阵积+非零C的8192个输出全部精确相同。8项mapped资格回归及1项零洗牌代码生成回归通过。

**这不是旧FP16累加顺序的逐位等价证明。** 偶奇置换保持精确实数内积，但改变FP16累加分组/舍入；不将内积交换律扩大成浮点结合律。实际新旧输出有差异，下面保留PSNR，不偷换gold。保留NaN字节不在有限域解码等价声明内。

## 同轮三DLL实测

`bench_sky.exe`，Preset2/Style1；50warmup/80iter；720p天空，900/1080p为同一确定性bench场景。每档old→new→V7再V7→new→old；默认DVFS，不改功耗/锁频。GPU硬件timestamp计时，Wall独立保留；原始遥测逐运行窗口在telemetry-summary.json。

| 档位 | 旧fast median正/反 ms | 新V2 median正/反 ms | V7 median正/反 ms |
|---|---:|---:|---:|
|720p|15.877 /15.956|10.187 /10.249|6.417 /6.477|
|900p|24.514 /24.527|15.266 /15.280|9.328 /9.319|
|1080p|31.959 /32.005|20.359 /20.333|12.311 /12.305|

V2对旧版同方向速度比约1.56～1.61×；V7仍比V2快约1.58～1.66×。完整每次min/median/Wall见[bench-results.md](bench-results.md)，不拼接不同轮次min/median。18次输出全部finite；同DLL正反运行输出全幅0bit相同。

720p天空三者变号均0；HF RMS旧0.000103482、新0.000101989、V7 0.000093139。新旧PSNR分别62.544361/61.663517/58.495481dB，maxabs0.004394531/0.006835938/0.008544922；新对V7为47.913975/39.253644/38.541064dB。peak固定1，域为bench RGB；相互距离不是绝对画质。原版未补丁DLL不能在此sm86运行，没有伪造“对原生新卡原版”的PSNR。没有用V7作gold。

## SASS与栈：消除的是MMA搬运，不是整个核所有SHFL

见[sass-summary.md](sass-summary.md)、sass-resources.json、matched-kernels.json。FB00～06全导出静态SHFL合计：

|FB|旧→新SHFL|旧→新max STACK B|
|---|---:|---:|
|00|26300→1274|264→240|
|01|16627→706|80→120|
|02|14195→706|8→0|
|03|12371→706|232→200|
|04|6563→610|1152→1032|
|05|4963→258|608→480|
|06|834→257|456→168|

这些包含未执行变体，不能当本帧动态指令数。例：FB00 upsample_fp8为1399→80 SHFL、200→48B STACK；同FB outview的STACK反而152→200B。FB05 projection_fp8从264→0B；FB06 decoder从456→160/168B。**并未实现全DLL零STACK**，REG也未统一下降，表内保留回退。cuobjdump的LOCAL:0不等于STACK:0，仍有LDL/STL。新render的编码源没有SHFL/PRMT，mapped源仍有必要PRMT，原网络归约SHFL和其它转换PRMT保留。

## V7剩余速度差：权重扩展已确认，IMMA存在但不能直接作因果归因

V7 SHA `30b6b599dbc593e5f9a8a0ddb2edac6f2f15ad0eaa967cd6bb0ab6bb224825c3`，534,586,880B；22个Fatbin。原00～06保留sm120，新15～21为75/86/120网络变体。`.nrcubin`新增11,541,176B；旧资源节变为无文件数据的`.orsrc`，新`.rsrc`虚拟大小518,221,024B。

资源逐叶解析：Small权重113,893,343→226,693,087B，HT147,695,410→291,526,450B；分别77/153条记录，同名顺序保持，均9条原样未变。大部分是“矩阵加倍、附带scale/metadata不变”的混合记录，不能直接把整条记录当纯FP16。Small里4个纯矩阵记录合计2,097,152个值：原E4M3独立解码为FP16后，**原始位值多重集合与V7全部相同，但线性顺序不一致**；证明有精确FP16预展开及重排，不是简单追加padding。尚未还原完整重排函数，不把其ABI直接搬进生产。见weights.json、weight-records.json、weight-expansion-samples.json；简单bit2移动假设不成立，负结果也保留。

V7 FB18-sm86确有**1040条静态IMMA.16832.S8.S8**，分布在5个C256 **非`_fp8`**变体、每个208条；对应`_fp8`变体无IMMA。摘录见v7-imma-snippets.txt、v7-imma-kernels.json。IMMA存在不自动证明Preset2本次执行它，更不能据此说V7整个网络变INT8。本轮没有运行时核追踪或V7的单因素消融，无法把剩余1.6×拆成“预解码占多少、IMMA占多少”。确切结论是：V7做了更广泛的权重/内核重写，FP16权重预展开有二进制证据；IMMA是另一个需核实实际派发的候选因素，不能二选一归因。

## 复测与清理

```bash
python3 Development/ptx-patcher/v2/check_primitives.py
DLSSNR_BUILD_CACHE="$PWD/Development/ptx-patcher/v2/artifacts/new" python3 Development/ptx-patcher/build_sm86_dlls.py --output /mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v2.dll
python3 Development/ptx-patcher/v2/run_bench.py --tag retest
python3 Development/ptx-patcher/v2/analyze_bench.py --tag retest
```

构建默认输出V2新名字，避免覆盖旧fast。run_bench拒绝覆盖旧日志/输出；保留same-driver/same-core、参数、DLL SHA及每次时窗。inspect_dll.py提取三DLL网络模块；inspect_sass.py生成静态资源与SASS统计；inspect_weights.py使用仓内归档格式解析器对原资源只读核验。

已保留新DLL、所有源码/报告/数值指标、资源表、SASS计数、关键IMMA摘录和SHA。临时解压cubin/PTX/SASS与全部本轮RGB、discord_v7目录旧RGB在记录SHA后清理，见cleanup.json；可按入口重建。未改发布ZIP、外部游戏或Magpie。阶段完成即单独commit，不push。
