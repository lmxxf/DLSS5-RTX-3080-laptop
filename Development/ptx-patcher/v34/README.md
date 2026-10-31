# PTX V3.4：FB01 独立 Quad、局部活性与 Shared 耦合审计

本轮不晋升 V3.4 DLL，继续以 V3.1_pack5 为唯一 1.00×。

quad_fb1 首轮全胜，repeat 720p/1080p 回退 0.166%/0.111%，900p 方向变号，未达到晋升门槛。

**终局条件未成立：分支 4 仍 Open，不能把剩余 Open 数写成 0，更不能据此宣布物理极限。** 容量反证及未排除的耦合表示改写见下文。

## 固定基线与验证

- 本轮唯一输入 V3.1_pack5 SHA `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`；全量重建同 SHA。所有候选 266,414,592B、15/15 O4 原槽位。
- 三档快验 18 次、首轮配对 120 次、repeat 24 次，共 162 次成功运行末帧严格 0 bit-diff / maxabs=0 / nonfinite=0。
- 每项 50 warmup / 80 iter，正向 ABBA、反向 BAAB；首轮三档六方向全胜才 repeat。所有计时进程串行；编译、GPU 原语和资源查询均先完成，没有排除计时样本。核验 [validation.json](validation.json)、[serial-stages.json](serial-stages.json)。
- 默认 DVFS，720p sky、900/1080p scene；min/median/Wall 各自保留。四张表沿用明确标记的历史循环观察及 Grid，官方 API 本轮重新查询；没有新硬件 issued/stall 计数。

## A：FB01 独立纯 Quad 与 Local Quad

quad_fb1 仅 FB01 使用 mask12（quad bit4 + pool bit8）；其余 14 个 Fatbin cubin 与基线逐字节相同。不启用 UP bit1，不改 mapped/图/权重。

Local Quad 使用寄存器声明绑定（含嵌套作用域）、同基本块最近定义、无守卫和中间读写检查，以及沿 CFG 全部后继路径的 dead-after 分析；谓词覆盖不能当作必然 kill，循环回边也参与读取检查。只有双半字在下一次无条件覆盖/返回前均不再被读取才删掉 16 位写回。

14 项结构/CFG 单测，6 个 GPU 融合/拒绝控制各 65,536 个输入模式均逐位一致；覆盖名字重用、内层作用域、源覆写、中间读取、后继读取、条件覆盖和回边。[单测](local-tests.log)、[GPU 控制](local-gpu-tests.json)。

|FB|全导出 Local Quad 对数|38 活跃核对数|
|---|---:|---:|
|0|0|0|
|1|456|164|
|2|616|212|
|3|616|212|
|4|0|0|
|5|0|0|
|6|0|0|

**新增解锁为 0，全导出仍为 1,688 对（456/616/616）。** 任务单提出的全函数计数/深度限制在这些剩余点上不是实际阻断原因：FB00 的拒绝样例是 `mov.b32 {%rs380,%rs381},%r2099` 再按反序拼回，属于已编码位拆装，不是两条 FP16→FP8 cvt；FB04/05/06 的多项定义则不在当前基本块。不能把这些 mov 一律当成可融合的量化对。每核原始拒因、行号与末次定义见 [local-quad-audit.json](local-quad-audit.json) 和 `quad-audit-quad_local-fbNN.json`。

实测候选：全网 quad_local、固定 quad_fb0145（FB00/01/04/05）、以及按“模块内至少一项 REG/STACK 下降且无活跃核增加”筛出的 Local 组合。筛选结果只有 FB01；它与 quad_fb0145 的 15 模块完全等价，因此复用该候选，不另造重复跑分。[计时前选择](quad-selection.json)。

## B1：36 项 pack_multidef

36/36 项均有两条可达定义，唯一可达 pack 为 0。逐项消费者/定义行号、块号、前驱末尾分支及定义集见 [multidef36-audit.json](multidef36-audit.json)。这些事件确实有真实数据路径与 fallback pack 合流，不是函数别处名字重用而当前点唯一可达 pack 的漏优化。本轮没有放宽生产 mapped 集合。

## B2：Shared 生产者/消费者、容量及安全返读

完整库存覆盖 2,320 个 shared_load 解码事件：FB01～05 为 2,304 个，FB06 另附 16 个；每项保留到实际 ld.shared 定义的关联。Shared 符号、所有 st/ld/cp.async、地址定义 DAG、写端值来源、跨线程见证及未解析的配对都写入 [shared-layout-audit.json](shared-layout-audit.json)。

例如 FB01 一组写地址为 `symbol + tid.y*2048 + laneid*16 + {0,512,1024,1536}`，读地址省略或改变 warp 片偏移；具体见证含 reader tid32 读取 writer tid0 的字节。FB04/05 存在本地量化、异步拷贝及多阶段复用耦合。数值见证限定于记录的 CTA 与历史 720p 参数；未解析的异步发布 epoch 没有伪装成“全部不可能”。

### 容量假设被官方 API 否定

|FB|基线 Shared/CTA B（不同入口）|翻倍 payload 后当前 CTA/SM 是否保持|
|---|---|---|
|1|4096|全部保持|
|2|8192|全部保持|
|3|16384|全部保持|
|4|8208, 12312|全部保持|
|5|0, 8208, 16400, 24600|全部保持|

设备实查：Shared 总量 **102,400B/SM**；默认每 block **49,152B**；opt-in 每 block **101,376B**；驱动每 block 保留 **1,024B**。此前把 101,376B 写作 SM 总量不准确。

在真实 baseline cubin 上，以额外 dynamic Shared 模拟 payload 翻倍，并对必要入口设置 opt-in，官方 Occupancy API 显示 FB01～05 全部保留当前 CTA/SM。FB01 4096→8192B 时仍 6 CTA/SM；FB05 24600B 入口额外增加 24576B 后仍 2 CTA/SM。[逐入口 API](shared-capacity-api.json)。

这是保持原 REG/线程数的容量反事实查询，**不是已经完成 FP16 表示重写或证明其速度有收益**。它明确否定“仅因容量翻倍就必然降当前驻留”；完整重写仍会改变地址、转置、异步拷贝、量化边界和可能的 REG/L1 代价。因此不能按任务单的容量否定条件把分支 4 关闭。

### 已实现的安全局部返读候选

库存另找到 36 个同线程向量返读（9 个 FB01～03 入口），不属于上面 2,320 个 MMA non-mapped 解码事件。加入 CFG store 支配、所有到达路径源值不变、TID-only 地址、其他写入不别名等约束后，构建 shared_forward 和 quad_fb1_shared。它们保留量化、所有 Shared store/barrier，仅将满足条件的 LDS 用已量化整数词的寄存器拷贝替换。[完整计划](shared-forward-plan.json)。

实际匹配 block 形状走快路，其他形状仍执行原始 LDS；微核分别验证快路及两个回退形状均 0 bit-diff。[GPU 形状测试](shared-forward-gpu-tests.json)。源 PTX 的 36 条回退 LDS 仍保留，不能按静态 LDS 数宣称动态 issued 数下降。

直接把量化前的 FP16 寄存器传过去不等价：GPU 穷举 half 位型中，示例 1.0625 经当前 pack5+UP 成为 1.0。[量化反例](quantization-counterexample.json)。新返读候选传的是已量化编码词，避开了这个错误。

## 四表与正式配对结果

[基线四表](hardware-baseline.md)，各候选 `hardware-<mode>.md` 与 [resources.json](resources.json) 包含 38 核指令、REG/STACK/STL/LDL、官方驻留及 Grid、SHFL/词法等待距离。

|候选|非 NOP|HMMA|PRMT|STL/LDL|
|---|---:|---:|---:|---:|
|baseline|152076|13188|19861|107/108|
|quad_fb1|151723|13188|19533|106/108|
|quad_local|150882|13188|18685|106/108|
|quad_fb0145|151723|13188|19533|106/108|
|shared_forward|152287|13188|19862|107/108|
|quad_fb1_shared|151938|13188|19534|106/108|

|轮次/候选|720p 下降%|900p 下降%|1080p 下降%|六方向全胜|
|---|---:|---:|---:|---|
|bench/quad_fb0145|0.004|0.506|0.032|False|
|bench/quad_fb1|0.251|0.224|0.342|True|
|bench/quad_fb1_shared|-0.017|-0.066|0.023|False|
|bench/quad_local|-0.053|0.274|0.175|False|
|bench/shared_forward|0.192|0.086|-1.041|False|
|repeat/quad_fb1|-0.166|0.006|-0.111|False|

逐次原始日志、输出 SHA、min/median/Wall 全部保留，[逐方向结果](timing-summary.md)。

## 分支结算

本轮不晋升 V3.4 DLL，继续以 V3.1_pack5 为唯一 1.00×。

- 分支 1：Pruned，n=3/3。
- 分支 2：Pruned，n=3/3。
- 分支 3：Pruned，n=3/3。
- 分支 4：Open，n=2/3。

分支 4 本轮作为一次完整实验批次计数：若未晋升，1→2；没有把两项审计机械计作两次失败并强推到 3。任务单最终剪枝还要求审计证实无剩余静态无损路径；当前容量反证和未完成的耦合 FP16 表示方向使该条件未成立。此处保留 Open，不移交“已达物理极限”终局报告。

生产五处与三个 v0.3.0 ZIP 均不覆盖，九个保护路径 SHA 不变。临时大产物清理见 cleanup.json；只保留文本证据及独立晋升 DLL（若有）。完成后更新 WorkingPlan/DevHistory 并立即独立 commit，不 push，无 Co-Authored-By。

清理完成：290 个文件、1,952,536,226B；九个保护路径再次同 SHA。采样温度 53～75°C，sw_thermal_slowdown 激活 0 点；此遥测覆盖所记区间，不作等频因果结论。

汇总器最终改为锚定协议行名前缀解析方向，避免候选名 shared_forward 中的 forward 混入分组。原始记录未改，纠正前后对照见 [direction-parser-correction.json](direction-parser-correction.json)，晋升裁决不变。

入库日志仅统一 LF/行尾空白，数值文本不变；转换前后 SHA 见 [log-encoding.json](log-encoding.json)。
