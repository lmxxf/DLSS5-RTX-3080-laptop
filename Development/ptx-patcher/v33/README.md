# PTX V3.3：来源拆分、分相池 / 重解码与纯 Quad

本轮不晋升 V3.3 DLL，继续以 V3.1_pack5 为唯一 1.00×。

纯 quad_all 首轮三档六方向全胜，repeat 的 900p/1080p 分别回退 0.033%/0.148%，正反方向均负，按固定门槛否决。

## 先核数据的验收结果

- 正式候选首轮 240 次，repeat 24 次；三档快验 33 次；专项探针对照 84 次（含 12 次基线、72 次破坏性版本）。
- 所有 309 次严格版本成功运行末帧相对同配置 V3.1_pack5 均为 **0 bit-diff / maxabs=0 / nonfinite=0**。探针版本不参与正确性或晋升。
- 所有计时进程串行，构建、GPU 原语和资源查询全部先结束再计时；独立脚本重读每个原始 SUMMARY、输出 SHA、cubin/SASS/资源、来源计数及阶段时序：[validation.json](validation.json)、[serial-stages.json](serial-stages.json)。没有本轮计时排除或删样本。
- 冻结输入：V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`；全量重建完全同 SHA。所有候选 266,414,592B、15/15 O4 原槽位。
- 默认 DVFS、50 warmup / 80 iter；720p sky、900/1080p scene。原语与实测末帧校验限定在记录输入范围。未使用 NCU 硬件 stall/issued 计数。

## A：Shared / Global 来源专项探针与转发审计

独立 CFG 审计重新核对全部 5,848 个静态 run 解码事件。任务单的 Global 3,528 并非全为纯 load：纯 Global 为 3,304，另有 144 个 Global+本地量化合流和 80 个 Global+常量合流。它们的动态执行频率不能由静态事件数直接推出。

|探针|旁路静态事件数|保留内容|
|---|---:|---|
|probe_shared|2320|所有非 Shared 来源正常解码|
|probe_global|3304|只旁路纯 Global，保留 224 混合事件|
|probe_global_family|3528|Global 家族，含 224 混合事件；与 Shared 正好覆盖全体|
|probe_mixed|224|只旁路两类混合来源|
|probe_both|5624|Shared + 纯 Global，保留混合事件|
|probe_all|5848|全部 non-mapped 解码旁路|

每版本每档 4 个 50/80 进程，正反两个顺序各两遍；下表都是同轮进程 GPU median 的均值差，正值仅表示删除该路径的敏感度，不是可兑现收益。

|宽度|Base ms|Shared Δms|纯 Global Δms|Global 家族 Δms|混合 Δms|全去 Decode Δms|Shared×Global 家族交互项|
|---|---:|---:|---:|---:|---:|---:|---:|
|1280|5.658250|0.324500|0.386000|0.414000|0.069500|0.541250|0.197250|
|1600|8.336250|0.500500|0.809750|0.861750|0.021000|1.028500|0.333750|
|1920|11.049750|0.723250|1.159000|1.204000|0.017500|1.489250|0.438000|

交互项为 `(Base−Shared)+(Base−GlobalFamily)−(Base−All)`。不能把 Shared/Global 两项直接相加分摊既有 0.564/0.992/1.430ms；破坏性输出还改变编译器排程、寄存器与部分静态 HMMA 数。[全部原始探针](probes.json)、[来源计数](probe-events.json)、[探针汇总](probe-summary.json)。

### 144 个混合事件为何不能直接拓宽 mapped

完整反证见 [forwarding-audit.json](forwarding-audit.json)：每项记录消费者、两条可达定义、定义所在块、前驱/后继和指令上下文。示例 FB00 `cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8` 的 `%r4993`，既可由 `ld.weak.global.cg.v4.u32 { %r4993,%r4994,%r4995,%r4996},[%rd17]` 定义，也可由 `mov.b32 %r4993,{%rs18,%rs18}` 的 fallback pack 定义，两者到达同一 MMA 使用。无条件转发 fallback half 会丢掉真实显存路径。

144 项均为 Global+本地量化 may-merge；不是 144 个已证明安全的转发机会。全部 5,848 项中未发现经 mov 隐藏的纯本地 pack 叶源，因此本轮没有生成未经证明的安全转发候选。5812 项原拒因是 not_a_recognized_FP8_pack，36 项是 pack_multidef；这些拒因标签与 144 个混合来源事件不是同一个计数。生产 mapped 集合未放宽。

这否决的是本轮无条件转发假设，Shared 中跨线程/跨 warp 的本地量化存取仍是分支 4 的后续工作，不据此宣告分支 4 见底。

## B：Two-Pass 分相与 Spill 重解码

按 C/D 的 RAW/WAR/WAW 依赖构造层，只在同层独立累加链间先发全部 phase0、再发全部 phase1。各累加器的 K32/K16 加法次序保留；输入若被输出寄存器覆盖则保存 run-entry 原始位型，测试模型实际未新增此类 raw snapshot。跨层仍复用的半片段按真实末次读取保留，不预设任意程序都能减半。

本模型全网 decoded-half 事件保持 11,696 不增；FB00..06 虚拟池峰值 `24/56/56/56/112/80/20 → 12/28/28/28/28/28/6`。超过单纯减半的部分来自依赖分层后的 JIT 生命周期缩短。虚拟池不是物理 REG。[逐核池](pool-summary.md)、[源级事件](source-summary.json)。

- `phase_pass`：全网分相。C512 ffwd 174→144regs，但仍未跨所需驻留台阶；部分原有 Spill 核 STACK 增长。
- `remat_spill / remat_fb1 / remat_qkv`：FB01 与 FB04 qkv 不跨 K32 缓存，源码每半步最多 6 个解码临时。O4 未保留预期的额外重解码，38 核 SASS/资源账本与基线相同；不能把源码池 6 当作真实寄存器开销仅 6。机器码字节仍有变化，故保留实测控制。
- `remat_call`：使用独立设备函数实现每次使用时解码，阻止同一入口内的普通表达式合并。CALL、调用保存与 STACK 的代价一并计入；这是强制重算控制，不冒称零调用开销的纯 ALU 因子。[helper SASS](remat-call-helpers.sass)。
- `phase_guarded`：计时前按“基线与分相后 STACK 都为 0 且 REG 不增加”选定 26 个入口，避免已知的资源回退。[预先固定名单](phase-guarded-targets.json)。
- `phase_quad_fb23 / phase_guarded_quad_fb23`：分别与独立零 Spill Quad 组合，所有 UP 保留旧路径。

21 组别名 GPU 用例（3 个模式各 7 类、每类 128 warp）、4 个独立/相关累加链用例均逐位一致；phase-pass 额外核对半片段解码次数严格不增。[别名](alias-phase_pass.json)、[remat](alias-remat.json)、[设备函数](alias-remat_call.json)、[依赖链](layer-tests.json)。

## C：纯 Quad，明确剥离 UP

`quad_all` 仅 FB01/02/03 使用 mask12（pool bit8 + quad bit4）；`quad_fb23` 仅 FB02/03 使用 mask12，其余 mask8。未启用 UP bit1、未启用 bias bit2。三版本均保留 4,744 处旧独立 UP，见 [UP 剥离实证](up-exclusion-proof.json)。FB02+FB03 全导出共融合 1,232 对；38 活跃核计数另列，不混用范围。

Quad GPU 原语 33,554,432 对与两次 pack5+拼接逐位相同，三档整网也相同。`quad_fb23` 的 FB01 和所有非 FB02/03 cubin 与基线逐字节相同。[原语](primitives.json)、[模块身份](machine-identity.json)。

新证据与旧捆绑候选不同：纯 quad_all 并未增加 FB01 Spill，两个活跃核 STACK 104/80→96/72B，全网 STL 107→106、LDL 108 不变。不能沿用“Quad 必然使 FB01 Spill 增加”的旧解释。

## 四张硬件表与正式配对裁决

[基线四表](hardware-baseline.md)，每版本 `hardware-<mode>.md` 提供完整指令/历史循环、REG/STACK/LOCAL、官方 Occupancy API+有限 Grid、SHFL/词法等待距离。数据 [resources.json](resources.json)。循环观察明确沿用 V2.5；词法等待距离不是动态重叠或 CFG 最短路径。

|候选|38 核非 NOP|HMMA|PRMT|STL/LDL|CALL|
|---|---:|---:|---:|---:|---:|
|baseline|152076|13188|19861|107/108|435|
|phase_pass|151993|13188|19858|108/109|435|
|remat_spill|152076|13188|19861|107/108|435|
|remat_fb1|152076|13188|19861|107/108|435|
|remat_qkv|152076|13188|19861|107/108|435|
|quad_all|150882|13188|18685|106/108|435|
|quad_fb23|151235|13188|19013|107/108|435|
|probe_shared|134147|13412|15334|85/76|435|
|probe_global|125196|13188|13227|57/51|423|
|probe_mixed|151434|13188|19701|107/108|435|
|probe_both|106817|13412|8587|38/27|420|
|probe_all|106147|13412|8429|38/27|420|
|probe_global_family|124526|13188|13069|57/51|423|
|remat_call|203639|13188|17623|495/461|11476|
|phase_quad_fb23|151152|13188|19010|108/109|435|
|phase_guarded|152066|13188|19860|107/108|435|
|phase_guarded_quad_fb23|151224|13188|19012|107/108|435|

|轮次/候选|720p 下降 %|900p 下降 %|1080p 下降 %|三档六方向全胜|
|---|---:|---:|---:|---|
|bench/phase_guarded|-0.105|-0.137|0.270|False|
|bench/phase_guarded_quad_fb23|0.915|0.499|0.115|False|
|bench/phase_pass|0.384|-0.491|-0.050|False|
|bench/phase_quad_fb23|0.254|-0.063|0.027|False|
|bench/quad_all|0.262|0.784|0.404|True|
|bench/quad_fb23|-0.522|0.548|-0.007|False|
|bench/remat_call|-72.757|-70.838|-67.572|False|
|bench/remat_fb1|-0.053|0.387|0.483|False|
|bench/remat_qkv|-0.048|0.626|0.347|False|
|bench/remat_spill|0.057|0.149|0.210|False|
|repeat/quad_all|0.052|-0.033|-0.148|False|

每项以自身同轮 V3.1_pack5 正反 ABBA/BAAB 配对，所有逐次 min/median/Wall、完整 SUMMARY、输出 SHA 均保留；首轮全档双向胜出才补 repeat。完整逐方向表见 [timing-summary.md](timing-summary.md)。

## 分支结算与阶梯封存

本轮不晋升 V3.3 DLL，继续以 V3.1_pack5 为唯一 1.00×。

- 分支 2：Open，n=2/3。
- 分支 3：Pruned，n=3/3。
- 分支 4：Open，n=1/3。

分支 3 的 K=3 是此批机制连续未晋升的搜索剪枝规则，不是物理极限证明；仍有 Open 节点。分支 4 本轮只完成来源探针/安全性反证，没有把破坏性探针当生产候选，也没有实施跨 Shared 的半精度存储重排。

生产五处、原始 DLL、三个 v0.3.0 ZIP 的九个保护路径 SHA 全部不变。临时大产物清理记录见 cleanup.json；仅保留文本证据及晋升独立 DLL（若有）。更新 WorkingPlan/DevHistory 后立即独立 commit，不部署、不 push，无 Co-Authored-By。

清理完成：789 个文件、5,291,002,338B；九个保护路径再次同 SHA。采样温度 51～77°C，sw_thermal_slowdown 激活 0 点；此遥测覆盖所记区间，不作等频因果结论。

入库日志仅统一 LF/行尾空白，数值文本不改；原始及入库 SHA 见 [log-encoding.json](log-encoding.json)。
