# PTX V3.6：范围特化、原位表示与异步 Shared 协同改写

本轮无晋升，保留 V3.1_pack5 为唯一 1.00×。

## 验证与基线

- 输入固定 V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`，所有候选仍在 15 原槽位 O4，不修改 Host/权重/参数 ABI 或生产部署。
- 所有正式计时串行，50 warmup/80 iter，正反 ABBA/BAAB；首轮三档六方向全胜均补 repeat。精确候选逐位门，实证/近似候选 50dB、1/64、finite/sky0 门在测试前固定。
- 有效过程计数：{'smoke': 60, 'timed': 456}；精确 351 次末帧均 0 bit-diff，近似 165 次逐项保留质量。全量过程输出嵌入 bench.json / repeat.json，没有单次 .log 碎片。

## 分支 5：有界 Pack4/Pack3

- CFG 范围审核覆盖全部 8,944 个存活转换：{'pack3': 680, 'pack4': 0, 'generic': 8264}。处理了命名 half 临时的词法作用域、FP32→FP16 有界转换、常量、min/max/abs、合流、NaN 和负零；未知项不当作证明。证据 pack-range-audit.json。
- pack3 要求非负且 +0，pack4 保留符号。33,554,432 对每个有界域 GPU 原语零差异；独立 ptxas -O4 的输出数据依赖切片（排除地址 LEA）实测核心 4/3 条，见 isolated-sass.json。
- pack_proven 仅使用已证明位点。pack4_all 与各模块 pack4_fbN 是实证探索：输出相同或过质量门并不证明所有中间激活从未超出448。

## 分支 6：原位全字节可逆与精选

- 新逆编码不再将 decoded half 夹到448，能恢复旧解码对7f/ff产生的±480，因此全256个原字节均可逆；GPU33,554,432对含保留码输入零差异。解除V3.5原位必须只含有限pack来源的限制，实际测试FB02/03原位2×及其组合，另有fast版本。
- 精选规则在计时前固定：STACK/STL/LDL不增加、官方CTA/SM不变。满足者为FB03四入口，精确版本与fb3_inplace复用，fast单列。另构造FB02一个完全配对的交换阶段 exact/fast，未把未解析epoch当作已证明。selected-entries.json、epoch-selection.json保留规则与覆盖。

## 分支 7：Shared/Async耦合

- fb45-shared-audit.json列出全部Shared声明、发布周期和混合异步/回退生产者；本模型没有独立的纯Type-I生产周期，不能把fallback st路径误作独立本地阶段。
- 选择在所有返回CTA路径上的发布点，为原字节数组另建half视图；保留原cp.async地址、mbarrier及原字节视图，完成等待后由CTA协同LDS→解码→STS，追加BAR后供已证明clean的MMA读取。无发布证明或静态Shared超过48KiB的入口保留原路径，未偷偷添加Host opt-in。
- 原始每4B额外1 LDS+8条源解码PTX+1 STS.v2，另含索引/循环及每发布点1 BAR。真实cp.async.cg 16B原语跨warp检查零差异，见async-primitive.json；完整FB04、FB05及组合模型实际运行验证，不从微核耗时推整帧收益。

## 配对结果

|轮次/候选|720p下降%|900p下降%|1080p下降%|质量门|
|---|---:|---:|---:|---|
|timed/async_fb4|-0.354|-0.617|-0.350|True|
|timed/async_fb45|-4.340|-4.302|-4.273|True|
|timed/async_fb5|-4.071|-3.827|-3.687|True|
|timed/fb23_fast_inplace|0.013|0.134|0.081|True|
|timed/fb23_inplace|-0.298|-0.317|-0.106|True|
|timed/fb2_epoch_fast_shadow|0.144|-0.363|-0.086|True|
|timed/fb2_epoch_shadow|-0.271|-0.421|0.212|True|
|timed/fb2_inplace|-0.330|-0.289|-0.188|True|
|timed/fb3_inplace|-0.079|-0.108|0.167|True|
|timed/fb3_selective_fast_inplace|0.328|0.012|0.232|True|
|timed/pack4_all|0.285|0.589|-0.009|True|
|timed/pack4_fb0|0.218|-0.994|-0.181|True|
|timed/pack4_fb1|0.057|-0.090|-0.145|True|
|timed/pack4_fb2|0.270|-0.072|0.047|True|
|timed/pack4_fb3|0.135|0.033|0.045|True|
|timed/pack4_fb4|-0.122|-0.241|0.034|True|
|timed/pack4_fb5|0.144|-0.134|0.104|True|
|timed/pack4_fb6|0.000|0.056|0.032|True|
|timed/pack_proven|-0.110|-0.009|-0.056|True|

完整正反、min/median/Wall与精度见timing-summary.json/md和嵌入原始输出；资源与四表见resources.json、hardware-*.md。默认DVFS，静态计数不等于动态issued/stall，没有本轮NCU计数。

## 结算

本轮无晋升，保留 V3.1_pack5 为唯一 1.00×。

- 分支5：Open n=1/3。
- 分支6：Open n=1/3。
- 分支7：Open n=1/3。

分支1～4保持原Pruned状态，本轮没有用一次新分支实验提前宣称全空间闭环。九个生产/发布保护路径SHA不变，不部署、不push；清理临时大产物，按构造验证、数据硬件表、文档状态分三提交，无Co-Authored-By。
