# Phase18：逐站half2打包与C256控制，采用小幅正收益组合

基线Phase17 selected（0c52778）。默认最终仅保留 **C32 V直通、Wave2 Stage5 ByteOut直通、C256 QKV fuse mask7**。其它打包站点、cap与pair方案保留证据，不盲目全开。**C256占用率未突破，最终仍226regs/48KB/OccW8**。

## 语义/原语

七个候选站点各做65536种half位模式×256位置、256单点布局，以及实际MMA步数压力：

|站点|AddZero|MMA步数|
|---|---|---|
|Wave2 contract|true|8|
|Wave2 result|true|4/8/16|
|Wave2 V|true|4/8/16|
|Wave2 AV|true|4|
|Wave2 ByteOut|true|7/11/19|
|C32 Prefix pre|false|1/2|
|C32 V|false|2|

全部与当前标量路径0字节差，覆盖±0、NaN/Inf符号与规范化。true复现+0/fma(x,1,+0)，false保持-0并用half乘1匹配原NaN规范化；不是直接裸halfpack。原语报告primitive-results.json。不改Q/K归一化、float激活多项式、RTZ residual或MMA累加顺序。

共享内存生产者的D字节需D→AB；最终ByteOut必须回RDNA4行列顺序，新增half位排列避免8路f32展开。**最终重排/打包在像素裁剪之前由整个warp共同完成**，裁剪内只写字节。初版放在裁剪分支内，部分lane不参与SHFL，预热挂起约200秒；只终止了该benchmark进程，GPU恢复。修正版经过3档快验再进入正式计时，并新增防回归。初版没有性能成绩、不入默认。见byteout-unsafe-observation.json、test_phase18.py。

## 逐站ABBA

全部七站分别三档A/B/B/A，每次50warmup/80iter，共84次正式运行，全部Phase17全幅0bit、invalid0、first-last0、32/32 LMem0。

|站点|720p meanB−meanA ms|900p|1080p|选择|
|---|---:|---:|---:|---|
|contract|-0.0340|+0.0305|-0.0030|不保留：混合/噪声|
|result|-0.0095|+0.0140|-0.0345|不保留：无稳定净收益|
|Wave2 V|-0.0205|0.0000|+0.0060|不保留|
|AV|-0.0075|-0.0525|-0.0025|不保留：部分档位接近零|
|ByteOut|-0.0655|-0.0385|-0.0585|保留|
|C32 Prefix|-0.0020|-0.0455|+0.0130|不保留|
|C32 V|-0.0630|-0.0325|-0.1100|保留|

这些均值是两次median的简表，不是单次帧统计。逐站**峰值REG/OccW均未下降**，不把省f32转换说成已经降低C256峰值。完整四次median/min/Wall/独立profile与资源在site-summary.md/json、site-results.json和原始日志。

## C256 cap / QKV控制

在ByteOut+C32V（pack2）基础上比较cap168/128、fuse7、pair15，以及全量Wave2打包与cap的耦合：

- **168**：两核STACK0、REG168，仍OccW8；1080p对pack2的ABBA差额+0.0290ms，无可靠净收益，不默认。
- **128**：两核各8B STACK；全量打包+128仍各8B；fuse/pair+128各48B。违反零spill门槛，拒绝计时/推广。
- C256线程块256线程，168不是自动OccW12；保持原Shared48KB，实际占用率按8warp步长。没有用cap成功冒充性能或占用率突破。
- QKV mask7（原3加C256 bit4）复用相同A片段，逐累加器K顺序与归一化保持；mask15是额外pair bit8，必须同时有bit4。两者均经过三档0bit/LMem0。
- 七个资源通过控制做1080p50/80 ABBA，对pack2的均值差：pack-all -0.0485、cap168 +0.0290、fuse7 **-0.2180**、pair15 -0.0645、fuse7-cap168 -0.1620、pair15-cap168 -0.1130、all-cap168 -0.1110ms。pack-all/部分pair有方向不稳，不按单次低值选型；采用fuse7，不将细小名次差当固定因果收益。screen-summary.md保留全部4次median。

## 最终组合 vs Phase17

Small31/Style1，Graph off，默认DVFS，50warmup/80iter，三档正反ABBA：

|档位|A1|B1|B2|A2|两次median均值A→B|速度比|
|---|---:|---:|---:|---:|---:|---:|
|720p|13.817|13.648|13.661|13.852|13.8345→13.6545|1.0132×|
|900p|23.212|22.971|23.217|23.366|23.2890→23.0940|1.0084×|
|1080p|31.091|30.916|31.037|31.294|31.1925→30.9765|1.0070×|

六次配对都更快，三档严格0bit，采用新默认。报告**小幅约0.7～1.3%**，不拿跨轮/跨阶段绝对耗时算新倍数，不作等频声明。final-summary.md/json含15个C32/Wave2活跃核四次插桩与REG/LOCAL/Shared/OccW；逐run日志保留全部32核。PROFILE_TOTAL是独立插桩帧，不当整帧median，也不把差额都当launch气泡。GPU原始遥测和按时窗统计保留。

## 最终默认/复测

`PHASE18_SITES={'c32-wave1-fast':['c32-v'],'c64-wave2-fast':['byteout']}`，`PHASE18_QKV_MASK=7`，`PHASE18_C256_CAP=None`。Host复用Phase17同一二进制，V3权重ABI/标记不变；仅C32 fast和C64-wave2-fast两个模块变化，38模块与Phase17相同，实际加载40模块1918entry，最终源码重编SHA与实测完全一致。

默认独立产物在`phase18/artifacts/selected/modules`，selected-modules.sha256.json冻结；其余试验只留日志/资源/哈希。主入口：

```bash
python3 Development/hip-port/phase18/build_selected.py
python3 Development/hip-port/phase18/check_primitives.py
python3 Development/hip-port/phase18/run_final.py --tag my-retest
```

各站独立重做用build_sites.py（强制QKV原mask3）与新tag；历史run_sites/run_quicks默认名拒绝覆盖。build_selected在清理后可按selection.json重新从源码生成选定两个模块，不需要部署任何外部文件。其它站点没有进入默认，并非未验证。

本轮还通过20项Python/LLVM回归（包括ByteOut必须先全warp重排及cap覆盖不能粘住旧值）。保护性读取核对v0.2.0生产DLL/三ZIP哈希全部不变；无共享assets、游戏/Magpie、发布包写入，无push。临时模块/RGB/SASS重复产物清理，最终40模块/PTX/生成源、三档真实候选输出及全部证据保留。
