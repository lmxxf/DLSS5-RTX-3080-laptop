# PTX V2.7：实测驻留审计与四个 C32 核 cap168

推荐仅将 FB00 的 prefix、inpview_tilesync、ds_wait、outview_wait 四个 C32 核设为 `.maxnreg 168`。post、upsample 及其他模块保持 V2.6。A/B 不入默认。完整入口名、参数、SHA 与配对结果见 [selected.json](selected.json)。

产物：`/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v27.dll`，266,414,592 B，15/15 O4 原槽位；SHA256 `28150da4ea554258b660b610bf23168a266caeda1eb68521d195d2276f0b2969`。`python3 Development/ptx-patcher/v27/build_recommended.py` 从原 DLL 全量重建，并校验与实测候选字节一致。

## 未插桩同轮性能与质量

每次50 warmup/80 iter，正反 ABBA/BAAB；下表是四次进程内 GPU median 的均值，不是所有帧合并中位数。默认 DVFS，必须比较同轮基线。

| 分辨率 | V2.6 ms | V2.7 ms | 耗时下降 | 正/反方向下降 |
|---|---:|---:|---:|---:|
|720p sky|6.07900|6.02200|0.938%|0.926% / 0.950%|
|900p|8.83875|8.77950|0.670%|0.431% / 0.909%|
|1080p|11.61700|11.50375|0.975%|0.987% / 0.962%|

160 次正式50/80运行＋10次1/1快验，全部末帧相对 V2.6 bitdiff=0、maxabs=0、nonfinite=0；720p sky 变号0。只覆盖本测试输入，不外推全部游戏动态场景。详细数据：[results.md](results.md)、[bench.json](bench.json)、[extra-bench.json](extra-bench.json)、[smoke.json](smoke.json)。

A（独立UP五指令）、B（bias合并＋quad-pack）、AB 三档单因素/组合对照均已完成。B、AB 无全档稳定收益；A 在1080p正反变号。四核168上再叠加A，720/1080仍变号，未采纳。只压prefix比四核方案在720/1080分别慢0.195%/0.259%，两个方向均慢。C64 cap192三档均慢约0.38%～0.47%。详细负结果保留。

## Occupancy 与 spill

[CUDA API 查询](occupancy-baseline.json)证实设备48 SM、1536线程/SM、65536寄存器/SM、102400B shared/SM、16 CTA/SM。六个活跃 C32 核原为8 CTA＝8 warp/SM；prefix shared仅2048B，其他0。不能用 `floor(65536/(regs*32))` 当实际驻留数。

四个目标核 cap192/184仍8 warp，cap168才升至12；prefix STACK=0，inpview/ds各8B、outview16B。允许少量spill换驻留，最终由整帧实测裁决，**没有宣称零spill**。post/up仍8 warp。16 CTA上限也意味着单warp设计无法到48 warp。API是理论驻留上限，不是动态 achieved occupancy。

C64 cap168原为6 CTA/12 warp；176/184/192均降至4 CTA/8 warp，活跃最大STACK分别96→72/56/48B。六个cap控制均编译、查询并做720p快验，仅C32-168/C64-192进入全三档正式对照。A/B也未稳定清除FB01 spill。见 [occupancy-caps.json](occupancy-caps.json)、[resources.json](resources.json)。

## 新逐核账本与非 mapped 来源

12次NVAPI D3D12捕获，720/1080各按V22→V24→V26再反序，50 warmup/20 iter，每帧82次发射。详见 [profile-results.md](profile-results.md) 与 CSV。720p FB05仍最大，1080p FB00最大。新同轮V22→V26逐核时间和6.19715→6.01093、11.91921→11.44586ms；V24→V26中FB00节省0.07565/0.17987ms。其他模块有回退，不能藏掉，也不能用插桩账本代替未插桩整帧收益；V22→V26是累计版本变化。

来源审计按每个静态 MMA run 唯一 encoded 寄存器计数，采用完整 CFG may-reaching definitions，并保留原V26 mapped资格。所有活跃非mapped来源均已追清。FB01/02/03峰值各为24 global＋4 shared对，FB04为48＋8，FB05为32＋8，因此池峰值仍56/56/56/112/80个b32。全局来源只能确认地址根（FB01～04 param64+16、FB05 +24），不能一律叫权重。

shared中确有本地FP8量化后的中间特征：FB01 shared写源全部为本地量化，其他混有global/async copy。跨线程布局、同步和量化语义仍须保留，不能把shared读取直接替换为未经量化的half。未发现同基本块纯mov别名导致的重复解码身份；未放宽mapped资格。逐事件证据及汇总见 [source-results.md](source-results.md)、[source-audit.json](source-audit.json)。

## 审核与工程验证

独立[审核意见](../../doc/性能评估20261028-0207-审核意见.md)及核验JSON已落盘，原报告未改。重点纠正驻留公式、C64放宽cap代价、非mapped来源假设和跨版本统计口径。

审计发现旧 opcode 正则漏识别 `::` 限定符，已修复并增加qualified shared/global覆写及小写标签回归。112个入口mapped集合完全不变，修复后全量重建V2.6 SHA仍为 `04b01f0c963061e24d1fd34f5097043d4eeddb001c846d9002e4e2bdc73ad788`。13项回归通过。A/B生成器与既有GPU穷举版本逐字节相同，原语证明复用见 [primitive-reuse.json](primitive-reuse.json)，本轮新增整网0bit验证。

[validation.json](validation.json)记录收尾验收；[cleanup.json](cleanup.json)记录重复DLL、PTX/cubin缓存及RGB清理。保留源码、日志、CSV、JSON与唯一推荐DLL。主fast、旧推荐和三个正式ZIP哈希不变；不部署、不push。
