# PTX V4.1：V4.0基线上的驻留不变UP补全、正零与FB04 Pack4

本轮无晋升，保留V4.0为唯一1.00×；分支5 Open1/3。

## 参考与验收

- 唯一计时分母与输出参考：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`；完整配方重建baseline同SHA，15原槽位O4，Host/权重/参数ABI不变。
- 运行计数 {'smoke': 27, 'timed': 144}；严格增量（含基线）135次所测末帧0bit，新增实证Pack4/联合36次按预先固定PSNR≥50dB、maxabs≤1/64、nonfinite0及720p天空变号0验收。V4.0已有Pack4作为固定参考，纯UP/零折叠仍要求对其0bit。
- 正式计时严格串行50 warmup/80 iter，正向ABBA、反向BAAB；任何首轮三档六向全胜均补repeat，不以三档均值全正替代逐方向门。

## 构造与核验

- UP：保留V4.0已有34入口的CFG-UP，单列pool、FB06及两者联合增量。新增入口使用同一套唯一无守卫拆分、支配关系、全CFG路径无源覆写证明，所有构造前完成13项安全/CFG测试及33554432个32位模式GPU原语（67108864个half2输出）零差异。
- UP准入按本轮实际cubin与官方API复核：STACK/STL/LDL不增加且CTA/SM不下降，允许REG微增。pool为REG180→181、SASS6001→5841、PRMT472→440、0 Spill/2 CTA；FB06在完整V4.0配方中为REG203→206、SASS3855→3533、PRMT672→608、0 Spill/4 CTA。两者合计使总SASS145461→144979。计划中FB06的198/3988与200/3670来自未叠加Pack4的诊断版本，不沿用其差值预测；实际增量分别160与322。
- 零折叠：V4.0原FB456的500处不变，FB02/03再增加40+40=80处严格正零，合计580；每个替换重新做独立mov/cvt定义链证明。
- Pack4：仅新增FB04八个baseline零STACK/STL/LDL活跃入口，QKV等其余入口不变；保留实证/近似标签，不把测试帧相同推断为任意输入激活有界。
- 联合：三个UP版本各自与零80+FB04 Pack4组成预构造备选，全部在正式计时前构造、查询资源并冒烟。按预注册六方向最弱收益优先、均值次优先，从UP单因素首轮选择 `up_add_fb4pool`，完整测试 `joint_up_add_fb4pool_zero_pack4`；其他两个联合备选仅有资源和质量数据，未冒称正式计时。
- baseline逐字节相同未重计时的候选：[]。排除模块PTX/cubin/bin和未改入口SASS一致性见isolation-validation.json；原配方及实际资源对照见input-resource-audit.json、resource-validation.json。

## 配对结果（正数表示GPU median下降）

|轮次/候选|720p %|900p %|1080p %|六向全胜|
|---|---:|---:|---:|---|
|timed/joint_up_add_fb4pool_zero_pack4|-0.044|0.282|0.077|False|
|timed/pack4_add_fb4_nospill|-0.067|-0.003|-0.002|False|
|timed/up_add_fb4pool|-0.067|-0.030|-0.184|False|
|timed/up_add_fb6|-0.085|0.169|0.118|False|
|timed/up_occ_keep|0.165|-0.248|0.212|False|
|timed/zero_fb23456|0.249|-0.662|-0.129|False|

首轮五个单因素均有负向配对：两核UP联合的三档均值为+0.165%/−0.248%/+0.212%；FB06单独为−0.085%/+0.169%/+0.118%；pool单独为−0.067%/−0.030%/−0.184%；零80为+0.249%/−0.662%/−0.129%；新增FB04 Pack4为−0.067%/−0.003%/−0.002%。按预注册最弱方向规则选出的pool+零80+Pack4联合版为−0.044%/+0.282%/+0.077%，最弱方向−0.248%。无首轮六向全胜者，repeat名单为空，未跳过应跑的确认轮。

全部171次模型运行均过各自质量门。允许REG微增且驻留不降的资源条件已成立，尚未通过本轮稳定整帧收益条件；不以静态指令数量替代性能晋升判断。

逐方向、min/median/Wall与质量见timing-summary.json/md、bench/repeat JSON与quality-summary.md。四张硬件表见hardware-*.md，静态SASS不是动态issued/stall，驻留为本轮实际官方API；历史循环观测不是本轮NCU数据。默认DVFS，无本轮NCU计数。

## 分支与封存

本轮无晋升，保留V4.0为唯一1.00×；分支5 Open1/3。

- 分支5：Open 1/3。
- 其余六分支保持Pruned3/3，全表Open=1。

原十个生产/发布/旧基线路径加V4.0共十一个保护路径SHA不变，无生产覆盖；清理临时大二进制和帧，不留单次.log。按构造验证、计时四表、文档结算三个独立提交，无Co-Authored-By、不push。
