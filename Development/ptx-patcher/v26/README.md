# PTX V2.6：Low/High K16拆解与mapped零拷贝

**推荐V2.6。** 相对唯一基线V2.4，三档同轮GPU median均值下降 **1.96% / 2.27% / 2.30%**，各档正反两方向都胜出。K分组改变导致FP16舍入差，**不是0 bit-diff升级**；所测输出到V2.4/V1的PSNR均在约58～63dB，天空0变号、末帧全部有限。

## 数学与实现

对原K32寄存器的4字节，第一条K16取 `{byte0,byte1}`，第二条取 `{byte2,byte3}`。若原生K16坐标为j，本次实际全局K映射为：

`K_original = 2*j - (j & 1) + 2*phase`，j=0..15，phase=0/1。

两相合起来覆盖0..31，A/B使用相同置换，故精确实数内积不变。它是**线程内Low/High**，不是全局连续0..15/16..31；本轮没有证明它更接近原生Ada/Blackwell的内部累加次序。

- 非mapped：`prmt 0x9180 / 0xb3a2`分别提取低/高字节对与符号，后接mask、shl7、mul scale，仍8条。保持V2.4独立FP8_UP和SWAR pack，其余算术、图、权重、mapped资格和hot255不变。
- mapped：直接把原生 `(low,high)` 寄存器填入两条MMA，不分配解包pair、不发5410/7632。每个底层源按整个run的**半条MMA使用顺序**计算last read。只有源在最后一次读取前被d0/d1写坏时，才在第一次写坏前用一条mov保存。
- 特别处理**同一条原K32内部**的风险：第一条K16可覆写第二条要读的high。因此不能仅检查“更早的原K32”。当前真实模型的mapped源均未触发备份；备份逻辑由独立GPU风险用例验证。
- 非mapped仍按首次使用解包，并在其原始编码寄存器被更早覆写时提前保存；临时槽位在死亡后复用。

实现：[codegen.py](codegen.py)。审计所有15个Fatbin中的MMA生成路径，FB00～06累计去掉 **21,712条mapped PTX PRMT**，实际mapped备份mov为0。对应既有V2.5计数的FB00/1080p约60,218,440次mapped PTX PRMT事件不再生成；**这是基于既有执行事件的代码生成层对应量，不是本轮测得的硬件issued指令削减量**。

## 单算子与别名验证

1. 768个A/B标量槽坐标证明两侧K置换一致。
2. 33,554,432组原始位型解包测试：两种位置完整u16字节对＋干扰半字，Low/High结果与V2.4解包后的对应重排逐位一致。
3. 六个源寄存器的全部64种mapped/encoded分配，每种16组独立整数矩阵，GPU两版都精确等于CPU矩阵积＋0.5，0错误。
4. 5类别名GPU用例，每类128warps：同K32第二半被覆写、延迟使用共享源、low/high同源、延迟encoded源被覆写、全mapped无覆写。对独立“入口全部快照”的Low/High参考全0bit。最后一类确实0临时寄存器、0 PRMT；同K32 high风险只需1条备份mov。
5. 随机有效FP8/FP16矩阵，每类256组。参考为有效FP16输入以float64乘加、最终舍入为float32，不是整网gold：

| 有效输入 | 偶奇RMSE | Low/High RMSE | Low/High / 偶奇 |
|---|---:|---:|---:|
| A/B均编码FP8 | 0.002770765 | 0.002773440 | 1.001 |
| A mapped FP16、B编码FP8 | 0.001121577 | 0.001148855 | 1.024 |
| A/B均mapped FP16 | 0.000508252 | 0.000507191 | 0.998 |

两版误差处于同一量级，**没有声称逐点误差不增或任意输入无误差**；p99/maxabs和所有数据见[primitives.json](primitives.json)、[alias-tests.json](alias-tests.json)。

## 三档整帧正式配对

`bench_sky.exe`，Preset2/Style1；720p为sky、900p/1080p为同一确定性scene。每进程50 warmup / 80 iter，正向ABBA、反向BAAB，默认DVFS。表中是四次进程GPU median/min的均值。

| 输入 | 同轮V2.4 median | V2.6 median | V2.4 min | V2.6 min | 耗时下降 | 正向 / 反向收益 |
|---|---:|---:|---:|---:|---:|---:|
| 1280×720 sky | 6.09950ms | **5.98000ms** | 6.02800 | 5.91325 | **1.959%** | 2.152% / 1.770% |
| 1600×900 scene | 8.92475ms | **8.72200ms** | 8.71250 | 8.52300 | **2.272%** | 2.048% / 2.492% |
| 1920×1080 scene | 11.73225ms | **11.46250ms** | 11.49050 | 11.22550 | **2.299%** | 1.894% / 2.701% |

V1参考固定为备份 `backups/20261026-v020/production/nvngx_dlssnr_sm86_fast.dll`，SHA `3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a`。V1各档另跑正反参考用于输出质量/重复性，未把它的非配对时长混入本轮净收益。

| 输入 | V2.6 vs V2.4 PSNR | maxabs | V2.6 vs V1 PSNR | maxabs |
|---|---:|---:|---:|---:|
| 720p sky | **61.819121dB** | 0.0048828125 | **62.124349dB** | 0.00439453125 |
| 900p scene | **61.767286dB** | 0.005615234375 | **61.854969dB** | 0.006103515625 |
| 1080p scene | **58.421047dB** | 0.009765625 | **60.884550dB** | 0.00732421875 |

PSNR peak=1，域为bench最终RGB；这是到两种移植实现的距离，不是原生sm120或全网FP32绝对画质gold。每个版本在相同warmup/iter配置下重复输出均0bit；**跨版本有舍入差**。共9次初验＋24次V2.4/V2.6计时＋6次V1参考=39次末帧全部finite，天空变号全0；V2.6正式天空HF RMS `0.000102746766`。不能由三种确定性输入保证所有实机动态场景。

[原始记录](bench.json) · [计时与质量表](results.md)

## 40活跃核SASS与资源

| 静态指标（40个唯一活跃核名各计一次） | V2.4 | V2.6 | 变化 |
|---|---:|---:|---:|
| PRMT | 25,483 | **19,864** | -5,619（约22.05%） |
| 总SASS | 183,651 | **178,170** | -5,481（约2.98%） |
| HMMA | 13,188 | **13,188** | 不变 |

PTX事件/虚拟寄存器和编译后SASS/物理资源是不同口径，不能把预计60M PTX事件直接换成同等硬件周期收益。

- FB00解包临时池声明峰值40→24；FB01～06的最大值分别仍56/56/56/112/80/20，因为这些最大run受非mapped输入限制。**mapped本身不再占pair，不等于整个kernel临时寄存器为零。**
- 活跃C32 prefix REG234→196，inpview234→200，ds_wait231→199，outview236→197，upsample229→212；post无同等寄存器下降。
- 全导出FB01最大STACK **224→104B**，LDL+STL **507→381**。活跃outview_wait224→96B，ds/inpview80→64B，但活跃upsample **88→96B回退**。
- FB04最大STACK仍88B，FB05仍16B；FB05静态LDL+STL18→16，其余0/2/3/6保持0 STACK。**未清零全网spill。**
- 本轮沿用hot255：FB00/03/04/05/06=255，FB01/02=168。完成资源复核，没有因新代码而盲目重开cap扫描，也不声称这个组合全局最优。

[代码生成审计](codegen-audit.json) · [SASS](sass-audit.json) · [资源](resources.json)

## 产物与复现

推荐 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v26.dll`，**266,414,592B（254.07MiB），15/15 O4原槽位，无新增PE节**。

SHA256：`04b01f0c963061e24d1fd34f5097043d4eeddb001c846d9002e4e2bdc73ad788`。

`python3 Development/ptx-patcher/v26/build_recommended.py` 全15重建与实测候选SHA/PTX完全一致。新选项必须成对指定 `--mma-layout lowhigh --fp8-decode lowhigh8`，并使用SWAR、mask8、非quantized mapped；旧版默认可复现。10项既有回归通过。[最终验收](validation.json)

清理重复候选DLL、cubin/PTX、RGB，只保留推荐DLL与文本证据；保留用户启动前的任务单并追加实测结果。主fast、V2.4、V1备份及正式ZIP哈希保持不变。更新DevHistory/WorkingPlan后立即独立commit，无Co-Authored-By，不部署、不push。
