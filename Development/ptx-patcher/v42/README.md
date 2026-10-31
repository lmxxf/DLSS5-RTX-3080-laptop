# PTX V4.2：FB00隔离、FB01降Spill与7-SASS Pack4 Quad

本轮无晋升，保留V4.0为唯一1.00×；分支5 Open2/3。

## 参考与验收

- 唯一分母及输出参考：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`；完整配方重建baseline同SHA，15原槽位O4，Host/权重/参数ABI不变。
- 模型运行计数 {'smoke': 24, 'timed': 120}；严格增量（含基线）93次所测末帧0bit，新Pack4及联合51次按预先固定PSNR≥50dB、maxabs≤1/64、nonfinite0及720p天空变号0验收。
- 计时严格串行50 warmup/80 iter，正向ABBA、反向BAAB；任何首轮三档六向全胜均补repeat，不以三档均值替代逐方向门。

## 构造与核验

- A：只对FB00五个活跃入口新增Pack4，明确排除pre_block。当前V4.0配方上净减168条非NOP，FB00所有入口STACK/STL/LDL不增；排除入口SASS及其余14模块逐字节一致。旧V3.6表确认pre_block是新增3/3 STL/LDL的来源，但不把它直接认作整帧回退唯一原因。
- B：先在V4.0上单独构造FB01四入口Pack4并查询实际资源，按STACK/STL/LDL不增加选择；不机械排除REG增长。四入口均入选，净减488条非NOP，全网STL/LDL99/100→98/98。诊断版仅做资源/质量，正式计时使用clean名称。
- C：Pack4 Quad由两套原有Pack4的HMUL2/LEA/LOP3中间值和末尾0x7531 PRMT构成，不新增去夹断。独立ptxas-O4输出数据依赖切片确认参考为9条、Quad为7条（2 HMUL2+2 LEA+2 LOP3+1 PRMT），排除了地址LEA；LDG64的双寄存器定义也纳入切片。
- 33,554,432组GPU输入相对两次既有Pack4+拼接零差异，包含全部半字位型、对侧污染与旋转，覆盖正负零、subnormal、Inf、NaN；此为相对现有Pack4的位等价，不是对原生FP8有界性的新增承诺。
- 融合使用寄存器声明绑定、同基本块最近DOWN定义、源值不变、半字无中途读取及全CFG路径dead-after证明；14项嵌套绑定/覆写/谓词/回边测试通过。
- 实际全导出融合1232组，其中38活跃入口424组；PRMT净差-847、非NOP净差-842。计划预估848条PRMT，后端实测847条，以完整函数计数为准。逐对位置、源/目标及死后证据见quad-fusion-audit.json。
- Quad clean按实际STACK/STL/LDL不增加选中8个活跃入口，未剖析入口保留基线。所有资源查询及预构造均在干净冒烟/正式计时前完成。
- 联合备选均预先构造；从Quad单因素首轮按最弱方向优先、均值次优先，选 `pack4_quad_clean`，再与固定A/B组成 `joint_A_B_pack4_quad_clean` 独立测试。未选联合仅有资源/质量数据，未冒称正式跑分。

## 配对结果（正数为GPU median下降）

|轮次/候选|720p %|900p %|1080p %|六向全胜|
|---|---:|---:|---:|---|
|timed/joint_A_B_pack4_quad_clean|0.213|0.370|0.275|False|
|timed/pack4_fb0_nopre|0.000|0.956|-0.146|False|
|timed/pack4_fb1_clean|0.262|0.105|0.039|False|
|timed/pack4_quad_clean|0.351|0.174|0.077|False|
|timed/pack4_quad_fb23|-0.081|0.548|0.079|False|

四个单因素均有非正向配对，未触发repeat。优选联合版三档均值下降0.213% / 0.370% / 0.275%，但未通过逐方向门：900p/reverse -0.097%。FB01 clean与Quad clean虽三档均值均为正，也未达到首轮六向全胜，因此本轮无晋升。

全部144次模型运行均过各自质量门。7-SASS位等价与无新增Spill构造条件成立，本轮稳定全档性能条件尚未成立；不把静态指令削减换算为帧级已兑现收益。

逐方向、min/median/Wall与质量原始记录见timing-summary.json/md、bench/repeat JSON和quality-summary.md；四张硬件表见hardware-*.md。静态SASS不是动态issued/stall，驻留为本轮实际官方API，历史循环次数不是本轮NCU计数。默认DVFS，无本轮NCU数据。

## 分支与封存

本轮无晋升，保留V4.0为唯一1.00×；分支5 Open2/3。

- 分支5：Open 2/3。
- 其他六分支保持Pruned3/3，全表Open=1。

十一个生产/发布/基线保护路径SHA不变，不覆盖生产、不push；临时大二进制与帧清理，无单次.log碎文件。按构造验证、计时四表、文档状态三个独立小提交，无Co-Authored-By。
