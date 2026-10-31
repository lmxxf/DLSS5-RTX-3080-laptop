# PTX V4.0：零Spill UP隔离、全路径CFG拓宽与Pack4联合

晋升 joint_up_cfg_pack4_fb2356 为独立V4.0与下一轮唯一1.00×，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`。

## 参考与验收

- 唯一分母和输出参考：V3.8，SHA `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`；源配方重建baseline同SHA，原15槽位O4，Host/权重/参数ABI不变。
- 有效运行计数 {'smoke': 21, 'timed': 120, 'repeat': 24}；精确运行（含基线）123次所测末帧0bit；近似/实证42次按预先固定50dB、1/64、nonfinite0、720p天空变号0质量门验收。
- 全部正式计时串行50 warmup/80 iter，正向ABBA、反向BAAB。任何首轮三档六向全胜候选均补repeat，不以三档均值全正代替逐方向条件。

## 构造与独立核验

- A：选择V3.9 clean中实际发生改写的16个FB02/03/04/05活跃入口，baseline的STACK/STL/LDL均为0；其他入口SASS不变，FB00/01/06等模块PTX/cubin/bin逐字节一致。真实静态非NOP净减1439（641+651+86+61），修正计划中FB04 104、合计1457的计数；模块本身仍可能含未改动的Spill核，不把整个FB04称作零Spill。
- A扩展：只额外开启FB01 inpview，STACK64→56、STL/LDL11/15→10/14；其他FB01入口保持原代码。单因素结果检验FB00/01是否拖累720p，历史归因不当作已成立的因果结论。
- B：全部1031对/2062处原cross_block独立UP均有唯一无守卫拆分定义；split块支配使用块。CFGProof扫描所有可处于split→use路径上的源寄存器定义，包含循环，将守卫写入视为潜在覆写；没有用“两个位置可达定义集合恰好相同”替代路径证明，也未做循环重置放宽。全部通过无覆写证明，审计cross-block-up-audit.json保留逐使用点定义、块编号及证据。
- 拆分删除仅在两半转换均替换且无其他用户时执行。6项原有条件测试及7项CFG测试覆盖分支单边覆写、守卫写入、不可达代码、循环使用后覆写、无覆写循环和未定义半字路径。真实GPU原语33554432个32位模式、67108864个half2输出均与V3.8旧UP解码逐位相同，含7f/ff保留码。
- CFG-all先构造与查询资源，计时前固定REG/STACK/STL/LDL不增加、官方CTA/SM不下降的34个活跃入口，再构造cfg_clean及两个Pack4联合候选。cfg_all只作资源诊断和完整模型质量冒烟，不冒称跑过正式计时。
- C：A与cfg_clean各自叠加FB02/03/05/06经验Pack4，仍保留V3.8原500处零折叠。联合版保留预设近似/实证标签；测试输出相同不证明任意输入的中间激活有界。

## 转换覆盖

|模式|UP替换数|其中跨块|删除拆分数|
|---|---:|---:|---:|
|baseline|0|0|0|
|up_pair_fb2345|586|0|293|
|up_pair_fb1inp_2345|620|0|310|
|up_pair_cfg_all|4744|2062|2372|
|up_pair_cfg_clean|1288|522|644|
|joint_up_fb2345_pack4_fb2356|586|0|293|
|joint_up_cfg_pack4_fb2356|1288|522|644|

## 配对结果（正数为GPU median下降）

|轮次/候选|720p %|900p %|1080p %|六向全胜|
|---|---:|---:|---:|---|
|timed/joint_up_cfg_pack4_fb2356|0.826|1.422|0.610|True|
|timed/joint_up_fb2345_pack4_fb2356|0.578|-0.201|0.104|False|
|timed/up_pair_cfg_clean|0.582|0.419|0.279|False|
|timed/up_pair_fb1inp_2345|0.120|0.146|-0.023|False|
|timed/up_pair_fb2345|-0.204|0.338|-0.243|False|
|repeat/joint_up_cfg_pack4_fb2356|0.497|0.827|0.658|True|

晋升者 `joint_up_cfg_pack4_fb2356` 首轮三档均值下降 **0.826% / 1.422% / 0.610%**，repeat 下降 **0.497% / 0.827% / 0.658%**，两轮12个方向全为正。27次候选末帧检查均对V3.8为0bit/maxabs0；包含经验Pack4，仍保留实证/近似标签，不把所测输出一致升格为任意输入的有界证明。候选共直解1288处UP（含522处跨块）、删除644个拆分，38活跃入口非NOP为145461（相对V3.8净减5211），STL/LDL99/100。

封存 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v40.dll`，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`。后续唯一1.00×为V4.0；本轮全部数据仍以旧V3.8为分母。分支5重置0/3，其他六分支保持Pruned3/3。

逐方向、min/median/Wall与质量原始记录见timing-summary.json/md、bench/repeat JSON和quality-summary.md；四张硬件表见hardware-*.md。静态SASS不是动态issued/stall，驻留为本轮实际官方API查询，历史循环观测不是本轮NCU数据；默认DVFS，未取得本轮NCU计数。

## 分支结算

晋升 joint_up_cfg_pack4_fb2356 为独立V4.0与下一轮唯一1.00×，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`。

- 分支5：Open 0/3。
- 分支1～4、6、7维持Pruned3/3，全表Open=1。

十个生产/发布/基线保护路径SHA不变，无生产覆盖，不push；临时大二进制与帧清理，无单次.log碎文件。按构造证明、测量四表、文档状态三个独立小提交，无Co-Authored-By。
