# PTX V4.3：排除FB00的末轮联合与七分支K=3结算

本轮无晋升，保留V4.0为唯一1.00×；分支5正式Pruned3/3，七个预设分支全部Pruned3/3，Open=0。

## 固定参考与验收

- 唯一分母及输出参考：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`。完整配方重建baseline同SHA，原15槽位O4，Host/权重/参数ABI不变。
- 模型运行计数 {'smoke': 15, 'timed': 72}；严格基线检查39次0bit，新增Pack4及联合48次按预设50dB、1/64、nonfinite0和720p天空变号0质量门验收。所有候选新增FB01 Pack4，保持实证/近似标签，不把所测输出相同推断为任意输入有界。
- 正式计时严格串行50 warmup/80 iter，正向ABBA、反向BAAB；首轮三档六向全胜者全部补repeat，不以三档均值或五向胜出替代逐方向门。

## 构造、隔离与资源证明

- 候选1：FB01四活跃入口Pack4 + FB02/03八活跃入口Quad clean；38活跃入口非NOP144131，相对V4.0净减1330，PRMT净减847，STL/LDL98/98。FB00以及其他未指定模块PTX/cubin/bin逐字节保持V4.0，未指定入口SASS相同。
- 候选2：仅保留FB01 upsample/ds_wait/inpview三个指定入口Pack4，排除outview，并叠加FB02/03 Quad。名为spill3沿用派单范围，但在当前V4.0参考上只有upsample实际减少1/2 STL/LDL，ds_wait/inpview为保持原Spill；没有沿用旧基线的降Spill数。
- 候选3：先将FB01四活跃入口Pack4+Quad作为诊断构造，实际融合164组FB01 Quad；计时前按STACK/STL/LDL不高于V4.0、官方CTA/SM不降筛选，保留3入口，与FB02/03 Quad clean联合。剔除及理由：{'cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8': ['STL', 'LDL']}。不机械卡REG，重编译后再验证资源条件。
- Pack4 Quad位等价继承同一声明绑定、同块源稳定和半字全路径dead-after规则；14项绑定/覆写/守卫/回边测试与33554432对GPU原语通过，独立O4数据切片7核心SASS（旧两Pack4+拼接9）。此为相对既有Pack4的位等价，新增FB01去夹断仍按预设实证质量门验收。
- 诊断版本仅用于资源和模型质量冒烟，未参加正式性能晋升。全部构造、GPU原语与资源API查询先于干净模型冒烟及正式计时。历史A导致回退的叙述是本轮隔离动机，不是仅凭静态计数已确立的因果证明。

## 配对结果（正数表示GPU median下降）

|轮次/候选|720p %|900p %|1080p %|六向全胜|
|---|---:|---:|---:|---|
|timed/fb123_pack4_quad_clean|0.285|0.581|0.041|False|
|timed/fb1_pack4_fb23_quad|0.089|0.438|-0.032|False|
|timed/fb1_spill3_fb23_quad|0.183|0.260|-0.148|False|

三个候选在720p和900p均为双向正收益，但1080p均未全胜。候选1的1080p前向为−0.188%，候选2的1080p正反为−0.110%/−0.187%；候选3三档均值为+0.285%/+0.582%/+0.041%，仍在1080p反向回退−0.182%，仅5/6方向胜出。因此无首轮六向全胜者，repeat名单为空，本轮不晋升。

FB01 Quad clean实际新增融合132组FB01 Quad（加FB23原424组合计556组），非NOP143992、PRMT17669、STL/LDL94/94。资源与质量条件已成立，性能门尚未成立；按预定最后一轮预算结算Pruned3/3，没有将近胜视为通过。

逐方向、min/median/Wall和质量原始记录见timing-summary.json/md、bench/repeat JSON与quality-summary.md；四张体检表见hardware-*.md。静态SASS不是动态issued/stall，驻留为本轮官方API，历史循环观测不冒充本轮NCU计数。默认DVFS，未取得本轮NCU数据。

## 七分支结算

本轮无晋升，保留V4.0为唯一1.00×；分支5正式Pruned3/3，七个预设分支全部Pruned3/3，Open=0。

- 分支5：Pruned 3/3。
- 分支1～4、6、7：维持Pruned3/3。
- 全表Open=0；K=3关闭的是七个实际执行的预设搜索分支，不将有限负样本换算为数学物理性能下限。

十一保护路径SHA不变，无生产覆盖；临时大二进制及帧清理，无单次.log碎文件。三个独立小提交（构造验证、计时四表、文档结算），无Co-Authored-By，不push。
