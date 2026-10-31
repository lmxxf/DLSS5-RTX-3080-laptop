# PTX V3.7：QKV单核、零常量与FB03逐入口剥离

本轮无晋升，保留 V3.1_pack5 为唯一1.00×。

## 参考与验收

- 输入唯一 V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`；原15槽位O4、Host/权重/参数ABI保持不变。
- 有效运行计数 {'smoke': 42, 'timed': 312, 'repeat': 24}；精确运行（含基线）216次末帧0bit，近似/实证运行162次按预设50dB、maxabs≤1/64、nonfinite0及720p天空变号0验收。
- 正式计时严格串行，50 warmup / 80 iter，正向ABBA、反向BAAB；首轮三档六方向全胜者全部补repeat。不存在以三档均值全正代替六方向门的情况。

## 数据先行：构造与隔离核验

- 分支7：只改FB04的`cc_split_swin_16h_qkv_512_chained_fp8`；循环版复用V3.6发布点与half视图，展开版按实际128线程和8192B符号展开16个4B字，每发布点仍同步一次。isolation-validation.json核对其余37个活跃入口PTX与SASS完全一致。资源差异是静态证据，净收益由整帧计时判断。
- 分支5：680处正零折叠为`mov.b16 dst,0`。zero_check.py另用mov/cvt定义链独立证明，不依赖区间算术；GPU原语对正零输入零差异，独立ptxas-O4输出`STG RZ`且无算术核心。再测试仅FB02/03/05/06或FB03/06的经验Pack4组合，其余位点保留原转换。经验Pack4的输出相同不证明所有输入的中间激活有界。
- 分支6：FB03四入口各自单列；计时前固定REG下降子集ds_wait+upsample及排除inpview的三入口子集；分别再联合QKV展开版与零折叠。selection-audit.json保留选择依据。联合候选属于全部参与分支，不将其收益拆成纯因果份额。
- 原始进程输出内嵌JSON，无单次.log；编译/原语/资源API查询全部在干净冒烟与正式计时前完成。

## 三档配对结果

|轮次/候选|720p下降%|900p下降%|1080p下降%|六方向全胜|
|---|---:|---:|---:|---|
|timed/async_qkv_only|-0.388|0.148|-0.359|False|
|timed/async_qkv_unrolled|-0.554|-0.432|-0.590|False|
|timed/fb3_ds_wait_fast_inplace|-0.416|0.092|-0.248|False|
|timed/fb3_inpview_fast_inplace|0.026|0.824|0.111|False|
|timed/fb3_noinp_fast_inplace|-0.301|0.205|-0.068|False|
|timed/fb3_outview_fast_inplace|-0.897|0.540|0.063|False|
|timed/fb3_regdown_fast_inplace|-0.476|0.362|0.034|False|
|timed/fb3_upsample_fast_inplace|0.039|0.441|0.124|False|
|timed/joint_noinp|-0.441|-0.377|-0.054|False|
|timed/joint_regdown|-0.626|0.024|-0.059|False|
|timed/pack4_clean2356|0.751|0.292|0.271|False|
|timed/pack4_clean36|0.644|0.487|0.354|True|
|timed/pack_zero_const|0.496|0.036|0.393|False|
|repeat/pack4_clean36|0.410|-0.417|0.332|False|

`pack4_clean36`首轮六方向全正（均值 +0.644% / +0.487% / +0.354%），repeat 为 +0.410% / −0.417% / +0.332%；900p 正反分别 −0.437% / −0.397%，因此不晋升。所有378次运行均过各自质量门，失败在性能确认。

QKV循环单核剥离后，三档均值为 −0.388% / +0.148% / −0.359%；展开版为 −0.554% / −0.432% / −0.590%。这轮结果没有支持“整模块回退仅由另外三个核拖累”的归因；清零Spill与静态指令削减已成立，稳定整帧净收益尚未成立。

QKV资源：{'baseline': {'REG': 255, 'STACK': 88, 'STL': 40, 'LDL': 29, 'INSN_NONOP': 4515, 'resident_CTA_per_SM': 2}, 'async_qkv_only': {'REG': 243, 'STACK': 0, 'STL': 0, 'LDL': 0, 'INSN_NONOP': 3675, 'resident_CTA_per_SM': 2}, 'async_qkv_unrolled': {'REG': 243, 'STACK': 0, 'STL': 0, 'LDL': 0, 'INSN_NONOP': 4090, 'resident_CTA_per_SM': 2}}
零折叠：38活跃入口静态非NOP净差 -1888 条。

逐方向、min/median/Wall和质量原始记录见bench/repeat JSON，汇总见timing-summary.md；四张体检表为hardware-*.md。历史循环次数不是本轮动态issued/stall，默认DVFS，未取得NCU计数。

## 分支结算

本轮无晋升，保留 V3.1_pack5 为唯一1.00×。

- 分支5：Open n=2/3。
- 分支6：Open n=2/3。
- 分支7：Open n=2/3。

分支1～4仍Pruned3/3。未晋升候选只消耗本轮局部尝试，不宣称物理上限；保留全部Open分支。九个生产/发布保护路径SHA不变，临时大产物清理，不部署、不push；按构造/验证、测量/四表、文档/状态拆为三个提交，无Co-Authored-By。
