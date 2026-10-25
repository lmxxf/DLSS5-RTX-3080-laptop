# Phase14 独立正确性修复

起点41042b6/6b61bd9已验收，工作树干净；性能/旧输出基线只用Phase12 selected（固定40模块SHA）。不改冻结PTX路线、共享assets、Windows部署或ZIP，不push。

## 精确根因：两处预洗牌ABI漏配

`hip/build_sm86_modules.py` 的预洗牌替换原本按transposed-score写，却通过通用文本模式也命中了 `vit_attention_fused_body`：Q[0/1]及概率xb已执行`sm86_preshuffle_fp8`。但旧256路径的两处消费仍是通用WMMA：

```cpp
// 错：Q、xb已是Ampere A/B字节布局，通用入口又执行__sm86_prep_fp8。
a = WMMA(q[k/16], y, a);
acc[c] = WMMA(xb, y, acc[c]);
// 修复：A侧直接解包，B侧y照旧准备，C/D及数值操作不动。
a = sm86_wmma_fp8_preshuffled_a(q[k/16], y, a);
acc[c] = sm86_wmma_fp8_preshuffled_a(xb, y, acc[c]);
```

400 transposed-score的B侧入口已正确匹配；旧256遗漏了A侧改写。修复用`hip/phase14_transform.py`严格限定该函数，只替换两处消费者，核验两处生产者仍存在、匹配失败即报错。不是改LDS索引、不是降低精度、不是仅对1280×768加分支。旧generic body其它导出也修复相同ABI。

## 坐标证明：排除转置/分母/PV原索引与尾块

`layout_probe.hip` / `trace_layout.py`在16token单tile遍历16×16 query/key，32lane×8元素，含V通道7与23。每坐标分别测原始未预洗牌参考、仅Q二次洗牌、仅P二次洗牌、两者均错及三种匹配入口修复。

- Q=1位于(query3,channel5)、K=2位于(key11,channel5)：正确score在(lane11,element3)为2；重复Q洗牌后该非零项消失，匹配入口恢复。
- P二次洗牌不改score或分母，却破坏PV；固定Q与固定P可以独立恢复，全部修复后原始u32差异0。
- 原`t[(g*8+e)*24+r]`存储为[query,key]、`t[r*24+g*8+e]`读取为[query=r,key=g8+e]的转置逐坐标验证正确；分母等于对应query概率行和，PV等于相应E4M3概率×V，均独立核验。
- n=16就能复现两处ABI错误，不能归因为n%64尾块。另测16..256步长16全部16种合法token数，覆盖48/112/240等尾tile情形；Host只接受n%16=0，未假称支持任意不满16token输入。

证据 `layout-results.json` / `coordinate-counterexample.json`。256坐标中坏Q共256个score元素偏离，坏P共560个PV元素偏离；修复全部逐位一致。

## CPU/400/原始布局交叉覆盖

`coverage.py`共172项：两种累加（本机FP16与冻结F32），每种82组byte测试（全部16种token数×head坐标末token、非均匀归一化随机、subnormal/±0、有限边界、保留字节ABI兼容；另含两份实际240token QKV），外加每种4组浮点NaN/Inf/±0入口测试。修复256与400、原始未预洗牌规范参考**全部字节一致**。

实际首块两份QKV各245760个AV字节，两种累加下256/400差异均0；原F32链实际QKV对应CPU全部245760字节相同。FP16与CPU-F32本来有不同累加舍入，固定自身FP16口径下对400及规范参考严格0bit；不把FP16当F32。

NaN/Inf测试走真实source pack：+0/-0/+Inf/-Inf/±qNaN/±sNaN输入分别得到byte `[0,128,126,254,254,254,254,254]`，随后两路径及浮点/量化输入入口一致。E4M3 FN没有Inf编码；原有packed-MMA快速decoder只保证有限域，7f/ff按±480处理，与scalar NaN decoder不同。本轮保留该既有行为，对原始保留字节仅验证ABI等价，**不冒充IEEE NaN支持证明**。真实8块QKV无保留NaN字节，浮点NaN/Inf先clamp/pack后也无保留NaN字节。

## 新720p F32金标准

冻结Phase1 F32 builder/header+当前raw HIP源码重建未修复control，目标模块SHA与归档原件精确相同；再仅施加两处ABI修复。其余39模块保持归档F32 SHA，AMPERE_WEIGHTS=0，Host按既有F32门控配对。control及修复链先各重现900/1080 F32 gold **0bit**，才接受720新参考。F32指**同一Small31、FP8/F16权重与F32累加参考**，不是全网络FP32权重或改用精确除法。

重建720两条正确路径输出0bit；新gold `artifacts/gold/f32-720p-1280x768.rgb32` SHA256：

`149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5`

进一步抓取修复F32链的block31..38真实QKV/AV，捕获不改变整网输出。独立CPU矩阵算法（QK、clamp/half位映射概率、FP8(prob)×V、分母）与首块245760字节0bit；8块使用CPU精确除法共仅1字节差异，位于block32/token112/head3/channel5：num=2.0142364501953125、den=1.895751953125，精确除法舍入F32为1.0625→FP8 0x38；源码bare `rcp.approx.ftz.f32` 后乘法RNE为1.0625001192092896→0x39。不是新的布局错。

CPU其它部分保持独立，仅单独测一个CUDA RCP原语以匹配源码明确的近似倒数口径后，**8×245760=1966080个AV字节全部一致**。不把完整GPU attention输出喂入CPU参考。见`gold-cpu-results.json`、`rounding-results.json`及相应脚本。

全量默认40模块重编并实际CUDA加载1918entry；7个包含legacy导出的模块变化，33个SHA不变。全量selected三档快验与修复原型0bit，首末帧相同、invalid0、32/32 active LMem0（正式两轮验收随后归档）。

新720 FP16输出相对Phase12旧输出改变2947224个f32元素（完整1280×768×3），这是获授权的正确性变化。相对本轮独立新gold可见1280×720：**PSNR43.57794791233917dB/maxabs0.05093550682067871/invalid0**。数值虽与Phase13隔离诊断相同，本轮重建了F32 control、修复模块、整网参考及8块CPU证明，未拿旧诊断数充验收。900/1080对Phase12仍0bit，F32 PSNR46.975322410562406/46.100947087035124dB不变。

参考 `initial-quality.json`、`gold-manifest.json`、`*-modules.sha256.json`、`cuda-load-verification.json`。256/400速度选择及最终两轮三档数据见本目录README/final-results；旧错误720比较不再用于验收。
