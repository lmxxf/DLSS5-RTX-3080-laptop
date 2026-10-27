# PTX V2.8：Per-Kernel cap 驻留跃迁控制实验

**结论：不晋升 V2.8 DLL，保持 V2.7 为推荐版。** 十个单核/分层控制以及一个互补组合均未通过三档双向净收益条件。264次50/80正式运行＋11次1/1快验，合计275次末帧全部相对V2.7严格0 bit-diff、maxabs=0、nonfinite=0；720p天空0变号。理论驻留确实提升，但不能保证整帧加速。

| 控制 | 720p耗时下降 | 900p耗时下降 | 1080p耗时下降 |
|---|---:|---:|---:|
|vit_contract|-0.882%|0.194%|0.217%|
|vit_cq|-1.947%|-0.509%|-0.418%|
|vit_cqe|-5.496%|-2.900%|-3.340%|
|head|-0.058%|-0.572%|-0.487%|
|proj|0.129%|0.202%|0.037%|
|pool|-0.200%|0.228%|0.431%|
|ffwd_proj|-0.780%|-0.296%|-0.218%|
|ffwd_proj_inp|-0.154%|-0.506%|-0.156%|
|ffwd_inp|-0.150%|0.085%|-0.233%|
|up|0.133%|-0.268%|0.603%|
|pool+proj+up|-0.175%|0.360%|0.037%|

正数表示更快，负数表示更慢。即便平均值为正，也须看两个方向；例如proj的720p/1080p收益变号。pool在900/1080同向快，但720同向慢；up在720/1080同向快，但900同向慢。零spill的contract在720同向慢约0.88%，直接否定“零spill＋提高理论驻留必快”。

单项完成后，额外仅试pool＋proj＋up一个互补组合（`build_combo.py`、`bench_combo.py`，编译完成后计时，无并行编译）。三档基线→组合为6.01225→6.02275、8.75800→8.72650、11.48025→11.47600ms，720正反+0.100%/−0.448%；未采纳。见[组合对照](combo-bench-results.md)。没有按分辨率切换推荐，也未把负结果DLL冒充V2.8发布。

基线为生产推荐V2.7，SHA256 `28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969`。本轮仅修改指定入口的`.maxnreg`，不改变解码、mapped资格、权重、模型、图或Host选择。保留V2.7的四个C32 cap168，qkv_512/ffwd_512/attention/projection不压cap。

## 实验与核验

十个控制：[candidates.json](candidates.json)。ViT按contract、contract+qkv、contract+qkv+两expand分层；C512分别测head128、proj128、pool168、ffwd_proj168、ffwd_proj_inp168、ffwd_inp168；C32另测up168。各候选只重编对应FB，均O4且放回原槽位，DLL大小266,414,592B。`build.py`可重建全部控制；`run.py`依次查询资源、快验并正式计时。

[ptx-controls.json](ptx-controls.json)验证所有候选PTX屏蔽maxnreg数字后与V2.7完全相同；FB00/04/05基线cubin从原源码重编，均与实际V2.7逐字节一致。[sass-audit.json](sass-audit.json)验证受保护重核的指令序列未变，记录各目标静态LDL/STL。

[resources.md](resources.md)列出完整资源数据。CUDA API查询使用真实block和捕获的dynamic_shared=0，所有目标都实现理论驻留台阶，但代价不同：

- contract cap168实际REG166、STACK0；pool cap168实际REG164、STACK0。
- qkv64B，expand publish/chained168/160B，head136B，proj128B，ffwd_proj及inp版本各208B，ffwd_inp120B，up56B STACK。
- qkv_512仍255REG/88B，attention仍255REG/0B。没有把其他核的spill误记到这两个核上。

理论驻留不是实测active warp：720p ViT96 CTA，2 CTA/SM×48已能容纳整Grid；1080p160 CTA在2和3 CTA/SM下理想容量波次都是2。head两档只有24/48 CTA，原1 CTA/SM即足够；proj为36/80，后者才有2→1容量波次潜力。pool及三种128线程ffwd为36/80，原2 CTA/SM也足够。chained并发/同步、CTA分布仍可能改变收益，不能把独立Grid容量当完整调度模拟。

## 测量口径

`bench_sky.exe`未插桩，Preset2；720p sky，900p/1080p scene。每控制每档正向ABBA、反向BAAB，各进程50 warmup/80 iter，取四个进程GPU median的均值，与各自括号内基线比较。总240正式运行，另11次720p 1/1快验。默认DVFS，记录[telemetry.csv](telemetry.csv)，不把异轮绝对时长当提速。主结果见 [bench-results.md](bench-results.md)、[bench-summary.json](bench-summary.json)，保留每进程日志和输出SHA。

初始分层编译在计时前完成。反向阶段另有一次短暂的CPU基线重编核验，时间范围见cpu-verification-window.json，并可与bench时间记录对照；未运行其他GPU测试。各候选输出逐一对比同warmup/iter/尺寸的V2.7末帧，结论限于这些测试输入。

## 报告审核

[独立审核意见](../../doc/性能评估20261028-0335-审核意见.md)与[核验JSON](../../doc/性能评估20261028-0335-审核核验.json)保留原报告不改。第一节主性能数字正确，但170次包含10次快验；第二节两条合并行约1ns舍入误差，其他14行准确。第三节最大问题是把旧整包失败完全归因于重核：旧资源表本就显示qkv之外多个核spill，且历史ABC控制不能直接搬成V2.7因果证据。新的单核编译再次证实寄存器差距小不代表spill便宜。

十三项既有回归通过。最终质量、推荐选择、保护文件哈希复核见 [validation.json](validation.json)；清理记录见 [cleanup.json](cleanup.json)。主fast、V27及旧参考DLL、三个正式ZIP不覆盖，不部署、不push。
