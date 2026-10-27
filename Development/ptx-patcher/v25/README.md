# PTX V2.5：Hybrid分流负结果，补齐实测循环账本

**推荐仍为V2.4。** Hybrid算术完全等价，但全网三档均变慢；仅FB00启用也未得到稳定1080p收益。任务单“净收益才产出推荐DLL”的条件未满足，未创建正式 `nvngx_dlssnr_sm86_v25.dll`，不覆盖已有部署。

## 同轮50/80正反ABBA/BAAB

每行是四次进程GPU median的均值，默认DVFS，不与历史轮次绝对值混比。

| 范围 | 分辨率 | V2.4 ms | Hybrid ms | 耗时变化 |
|---|---|---:|---:|---:|
| 全网 | 1280×720 sky | 6.17950 | 6.20500 | **+0.413%** |
| 全网 | 1600×900 scene | 8.93025 | 9.04750 | **+1.313%** |
| 全网 | 1920×1080 scene | 11.72275 | 11.96775 | **+2.090%** |
| 仅FB00 | 1280×720 sky | 6.16425 | 6.15150 | -0.207% |
| 仅FB00 | 1920×1080 scene | 11.70750 | 11.70525 | -0.019%，方向变号 |

全网版三个档位的正反方向都变慢；FB00-only的1080p为正向慢0.193%、反向快0.230%，min均值也从11.52050变为11.56550ms，没有稳定收益，不再扩展此分支。

6次初验＋24次全网＋16次FB00-only，**46次末帧全部0 bit-diff/maxabs0/PSNR∞/nonfinite0**。33,554,432组GPU对照覆盖两parity完整字节对、高位干扰及非有限编码，V2.4 PRMT8与Hybrid8逐位相同。15/15 O4原槽位、266,414,592B，无新增PE节。[完整表](results.md) · [原语](decode-test.json) · [验收](validation.json)

## 分流确实生成了，但不等于总PRMT减半或性能提升

唯一算术改动为奇半边 `and 0x7f007f00; shr 1; lop3(register,0x80008000,second,0xea); mul`，保留偶半边PRMT与V2.4按需寄存器池、全部mapped/pack/图/权重/cap设置。

| 40活跃核名的静态SASS | V2.4 | Hybrid |
|---|---:|---:|
| PRMT | 25,483 | 19,774 |
| IMAD.SHL.U32 | 12,169 | 6,456 |
| LOP3.LUT | 32,370 | 38,081 |
| SHF.R.U32.HI | 6,355 | 12,067 |
| 总静态条数 | 183,651 | 183,800 |

pre_block PRMT **732→629**、IMAD.SHL **219→115**；post PRMT **828→716**、IMAD.SHL **231→119**。因此“非mapped解包模板中的PRMT减半”成立，**整个核/全网PRMT减半不成立**，mapped的0x5410/0x7632及其它pack/转换仍在。静态总条数还因调度/寄存器分配略增；FB01全导出STACK224→200B，但LDL+STL507→529，其余FB04/05仍88/16B，不宣称零spill。[SASS](sass-audit.json) · [资源](resources.json)

本轮没有测PRMT独占吞吐、管道stall或实际重叠率；任务单的2.0 SM-cyc/PRMT、0.5 SM-cyc/INT是假设成本，不是本机计数器读数。即便采用其FB00预算，HMMA 2.94ms仍大于PRMT 2.104ms，不能仅由第二项较大就证明它在关键路径。IMAD与普通位操作也不能不加区分地当成一条独立同速管道。[NVIDIA管道说明](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)区分相关执行单元；实际分流代价由本轮负结果约束，未声称“完美均衡”。

## 真正的新增证据：运行时MMA/循环计数

没有继续用`Grid×Block×静态文本`冒充动态执行。新增独立诊断链路：

1. NVAPI截取实际82次发射的参数块，捕获第50帧；三档与普通runner相同50/1配置输出0bit。ViT参数乘积实际为 **12×24=288 / 16×28=448 / 20×32=640 tokens**。
2. 给仅诊断用的FB00/04/05内核追加一个UAV指针参数，由专用runner扩展NVAPI参数块；不改变原参数偏移或张量。每帧清零独立4096B缓冲，UAV barrier后复制readback。
3. 每个收敛MMA run由lane0原子累加：FP8 K32按两条HMMA.16816换算，原生FP16 K16按一条计；另计自然计算循环入口，以及MMA解包的PTX PRMT/整数/HMUL2、mapped/unmapped事件。其他原始运算不变。三档1/1诊断末帧与未插桩V2.4参考**严格0bit**；诊断帧1的82个Grid/Block序列与捕获帧50一致。
4. 这些是**实际执行的MMA语义等价次数、循环访问与解包PTX事件**，不是硬件性能计数器的issued指令读数。诊断耗时不用于性能结论。

[诊断构建](build_counters.py) · [UAV/参数扩展runner生成](make_counter_runner.py) · [原始计数](counter-runs.json) · [完整逐核动态账本](dynamic-ledger.md)

### ViT圈数与尾段（所有warp的计数均验证）

| 核 | 主循环实际圈数 | 额外尾段 | 每warp HMMA |
|---|---:|---:|---:|
| expand_publish / expand_chained | 16 | 0 | 2048 |
| contract_chained | 15 | 1 | 2048 |
| qkv_chained | 15 | 1 | 1536 |
| projection_chained / wait | 7 | 1 | 512 |
| attention_chained | 5 / 7 / 10 | 0 | 640 / 896 / 1280 |

expand计数器0起、step64，旧值与960比较，因此执行0..960共16圈。contract的0起step64、比较896，对应15圈主循环，外面另有等量尾块；QKV为step32、比较448，对应15＋1；projection为step32、比较192，对应7＋1。**不能把整核静态HMMA简单乘16**：contract静态256已经包括主循环128＋尾段128，正确是`128×15+128=2048`。

FB04也已实测：两个ffwd核的计算循环为 **7、8圈**；ffwd_proj、ffwd_proj_inpview、proj、outview_wait、final_head为 **8圈**；qkv和proj_pool为 **7圈＋循环外其它计算**。例如qkv每warp为 **1664 HMMA**，不是其静态512直接乘8。逐核均列于动态账本。

### 三档实测MMA工作量与循环修正后的辅助模型

| 宽度 | FB | 实测HMMA等价warp次数 | 计算循环展开的辅助SASS模型 |
|---:|---:|---:|---:|
| 1280 | 04 | 4,694,016 | 33,309,600 |
| 1280 | 05 | 20,185,088 | 162,130,944 |
| 1600 | 04 | 7,155,712 | 50,889,440 |
| 1600 | 05 | 27,000,832 | 216,246,272 |
| 1920 | 04 | 9,699,328 | 69,783,168 |
| 1920 | 05 | 35,389,440 | 286,136,320 |

**两列证据等级不同**：左列来自运行时原子计数；右列用原V2.4 SASS CFG，把自然计算循环按实测warp访问次数展开，循环外按发射warp数计一次。每个FB04/05核、每档模型的HMMA列都与运行时计数严格相等。辅助列采用可达条件块的并集、非MMA循环单次通过，**未测实际谓词/分歧、分离helper子程序及同步重试，既不是精确issued数，也不是包含任意重试的上界**。精确辅助硬件指令/stall仍需要相应硬件计数器，不能以修正K圈数掩盖这一限制。[模型源码及逐opcode结果](dynamic-ledger.json)

按任务单给定的48SM、720p1695MHz/其余1605MHz与4cycles/HMMA假设，FB04/05纯TC预算分别为 **0.231/0.992、0.372/1.402、0.504/1.837ms**。频率是模型输入，未声称为这些诊断进程的稳态实测频率。

FB00另测得HMMA等价次数25,696,224 / 40,691,424 / 54,871,200；1080p解包事件为 **12,892,128个非mapped pair、30,109,220个mapped pair**。非mapped只占约30%；只减其一半PRMT，整个MMA解包PTX PRMT事件仅降约 **14.99%**。这些PTX事件会被编译器折叠，不能直接套SASS吞吐换算硬件周期，也不含run外全部pack/UP指令。

## 收尾与复现

- 实验开关 `--fp8-decode hybrid8 --v24-mask 8`，保留V2.4的SWAR、mapped和hot255；兼容旧默认不变。`build.py`重建全网候选，`build_fb0.py`从相同候选拼FB00-only。
- 参数/计数复现依次使用 `extract_raw.py`、`cfg_loops.py`、`build_profile.py`、`capture_params.py`、`build.py`、`bench.py smoke`、`build_counters.py`、`make_counter_runner.py`、`run_counters.py`、`extract_sass.py`、`dynamic_ledger.py`。MinHook使用V2.3同一固定提交及其[许可证](../v23/MinHook-LICENSE.txt)。诊断DLL必须配专用runner，清理时删除，严禁部署。
- 验收保留V2.4推荐SHA `1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256`。全网候选SHA `2cd74bfc5aec61bbef4bc153237e5d26048af3471b5d7e6dfcbf6b82c9c0bfd7`仅作失败实验身份，不升级推荐。
- 10项既有回归通过。临时DLL/PTX/cubin/RGB/runner清理，保留文本证据、源码与JSON。主fast、V2.4及正式ZIP收尾哈希不变；不部署、不push，无Co-Authored-By。
