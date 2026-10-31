# PTX V3.8：七分支K=3末轮结算

晋升 zero_const_fb456 为独立V3.8，下一轮唯一1.00×，SHA `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`。

## 固定边界与验收

- 原输入V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`；15原PE槽位O4，Host/权重/参数ABI不变。
- 运行计数 {'smoke': 48, 'timed': 192, 'repeat': 48}；精确运行（含基线）201次末帧0bit；近似/实证87次按预先固定PSNR≥50dB、maxabs≤1/64、nonfinite0与720p天空变号0验收。
- 全部计时严格串行50 warmup/80 iter，正向ABBA、反向BAAB；任何首轮三档六向全胜候选均补repeat，不以三档均值全正替代逐方向门。

## 单因素与联合构造

- 任务A：zero_const_fb26只折叠FB02..06正零，fb456只折叠FB04..06；每个位点重跑独立mov/cvt定义链正零证明。pack4_pure36只改FB03/06且不叠加零折叠；pack4_fb26_clean将fb26正零与FB03/06经验Pack4联合。所有A候选FB00/01的PTX/cubin/bin与基线逐字节一致，其他排除模块也核验一致。经验Pack4输出过门不证明所有中间激活有界。
- 任务B：只改FB03 inpview+upsample两个入口，分别exact和fast；其余36活跃入口PTX/SASS一致。精确版使用全字节可逆Shared表示，fast保留近似标签。
- 任务C：只改FB04 proj_pool_512单入口，其余37活跃入口PTX/SASS一致；复用已审计的发布点和协同解包half视图，计时检验额外刷新与寄存器变化能否被回收。
- 联合：全部8种A×B+pool预先构造、查询资源、冒烟；7个单因素首轮结束后，按预先固定的六方向最弱收益优先、均值次优先选择A/B。实际选中 `joint_zero_const_fb456_fb3_inp_up_fast`，其独立完整首轮及必要repeat全部保留。未在计时中插入编译或GPU资源查询；未选择的7个预构造联合版本仅作构造/质量备选，不冒称跑过正式计时。
- zero-fold-audit.json逐模式/FB保留折叠数量；isolation-validation.json保留排除模块与入口隔离证据。未把FB00寄存器增长或历史单入口回退直接当作已证实的纯因果归因。

## 配对结果（正数表示GPU median下降）

|轮次/候选|720p %|900p %|1080p %|六向全胜|
|---|---:|---:|---:|---|
|timed/async_pool_only|-0.170|-0.728|-0.447|False|
|timed/fb3_inp_up_exact|0.031|-0.071|-0.253|False|
|timed/fb3_inp_up_fast|-0.048|-0.119|0.088|False|
|timed/joint_zero_const_fb456_fb3_inp_up_fast|0.695|0.077|0.061|True|
|timed/pack4_fb26_clean|0.482|0.454|-0.086|False|
|timed/pack4_pure36|0.272|0.065|0.045|False|
|timed/zero_const_fb26|0.356|0.113|0.111|False|
|timed/zero_const_fb456|0.238|0.653|0.133|True|
|repeat/joint_zero_const_fb456_fb3_inp_up_fast|0.196|-1.011|-0.269|False|
|repeat/zero_const_fb456|0.357|0.623|0.264|True|

晋升者 `zero_const_fb456` 仅对FB04/05/06的500个正零转换直接赋0：38活跃入口静态非NOP净减1404条，FB04 QKV的STL/LDL为33/22；没有引入近似舍入或Shared布局改写。首轮三档均值下降 **0.238% / 0.653% / 0.133%**，repeat 下降 **0.357% / 0.623% / 0.264%**，两轮12个方向全部严格为正；候选27次三档输出检查均对V3.1_pack5为0bit。新封存路径 `/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v38.dll`，选择及完整SHA见selected.json；后续以此为1.00×，本轮数据仍使用旧V3.1分母。

联合版repeat的900p/1080p均值分别回退1.011%/0.269%，不晋升。按分支机制归属，仅重置分支5；FB03耦合与pool异步路径所属分支6/7本轮未晋升，达到Pruned3/3。

逐方向、min/median/Wall及质量见timing-summary.json/md、bench/repeat JSON与quality-summary.md。四张体检表见hardware-*.md，静态SASS不等于动态issued/stall，驻留为官方API结果；历史V2.5循环观测不冒充本轮NCU数据，默认DVFS，未取得本轮NCU计数。

## 七分支结算

- 分支1～4：保持Pruned3/3。
- 分支5：Open 0/3。
- 分支6：Pruned 3/3。
- 分支7：Pruned 3/3。

Open=1。本结算关闭按K=3实际执行的七个预设搜索分支，不将有限候选失败换算为数学物理性能下限。

九个生产/发布保护路径SHA不变，无生产部署，不push；临时大二进制与帧输出清理，单次输出只保留汇总JSON，无.log碎文件。按构造/验证、测量/四表、文档/结算三个独立提交，无Co-Authored-By。
