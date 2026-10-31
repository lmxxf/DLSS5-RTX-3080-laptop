# PTX V3.2：Decode 半步池、独立 UP 与 G2 临界核实验

本轮不晋升 V3.2 DLL，继续封存 V3.1_pack5 为唯一 1.00×；分支 3 保持 Open，n=2/3，分支 4 保持 Open、n=0/3。

split+UP 首轮三档六方向全胜后补跑 repeat，但 900p 均值回退 0.161%（正/反下降率 -0.316% / -0.006%），未通过晋升门槛。
本轮按 WorkingPlan 的明确实验批次执行；分支 3 尚未达到 K=3，不剪枝，也不把本轮负结果作为全网终局。生产五处与 v0.3.0 ZIP 均未覆盖，不 push。

## 冻结基线与数据先审

- 唯一参考：V3.1_pack5，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`，266,414,592 B，15/15 O4 原槽位。baseline 全量源码重建 SHA 与封存版完全一致。
- `validate_data.py` 独立重读各进程 SUMMARY、DLL SHA、15 槽 manifest、38 活跃核资源、原语及保护清单，再写本报告；[验证结果](validation.json)。
- 正确性成功运行 363 次（含原始 72 次排除计时、3 次快验），全部相对同 warmup/iter 的 V3.1_pack5 末帧严格 0 bit-diff / maxabs=0 / nonfinite=0。另有 48 次破坏性探针运行，仅供诊断。
- 原始首轮 72 次与资源查询/驱动编译重叠，整轮排除并串行完整补跑（12 次 repair + 60 次 clean）；不删原数据：[排除记录](excluded-timing.json)、[补跑](repair.json)、[有效首轮](first.json)。有效首轮、cap、算术及探针计时均与构建/资源查询/GPU 原语串行进行。
- 默认 DVFS；没有锁频或调功耗。NCU 未安装，未采硬件 stall/issued 计数。历史循环观察来自 V2.5 语义插桩，真实 Grid/Block 来自 V2.3 NVAPI 账本；不冒称本轮重新测得动态指令数。

## 四张硬件体检表

[基线四表](hardware-baseline.md)；每候选 `hardware-<variant>.md` 提供同样四表，机器数据为 [resources.json](resources.json)。

|候选|38 核非 NOP|含 NOP|HMMA|PRMT|SHF|LOP3|STL/LDL|
|---|---:|---:|---:|---:|---:|---:|---:|
|baseline|152076|152807|13188|19861|1445|20753|107/108|
|split|152071|152800|13188|19861|1439|20753|107/108|
|up|150179|150899|13188|19861|1445|19116|108/110|
|split_up|150173|150900|13188|19861|1439|19116|108/110|
|split_up_publish|150217|150940|13188|19860|1439|19141|111/115|
|split_up_contract|150233|150959|13188|19861|1436|19118|110/112|
|split_up_expand|150327|151050|13188|19863|1447|19143|160/166|
|split_up_head|150306|151033|13188|19864|1452|19123|148/152|
|split_up_proj|150318|151048|13188|19864|1447|19124|150/157|
|split_up_pool|150298|151027|13188|19862|1436|19207|108/110|
|shift|152076|152808|13188|19861|1445|20753|107/108|
|split_up_shift|150173|150900|13188|19861|1439|19116|108/110|

四表中的等待距离为 PTX 语句的词法距离，不是 CFG 最短路径或动态重叠；同步代码未改。驻留由实际 cubin 调官方 `cuOccupancyMaxActiveBlocksPerMultiprocessor`，并附有限 Grid 容量波次；不使用寄存器简单除法替代 API。

## 3.1 Phase-Split JIT 池

- 解码调度细化至 `2*i+phase`；每半步最后一次读取后释放，若 encoded 原寄存器将被更早写坏，则提前解码相应半部。mapped 隐式源的原有备份及读取顺序保留。MMA/K 顺序、FP8 舍入、权重与同步不改。
- 7 类独立 GPU upfront-snapshot 反例、每类 128 warp 全部 0 bit-diff，含同 K32 半步覆写、首次使用前 encoded 覆写、mapped 同源/共享源、64-MMA 长 run、全 mapped 零临时池。[原语记录](alias-tests.json)。
- 38 核共 368 个 run、5,848 个 encoded 解码事件，240 个单次使用操作数，模型 backup_moves=0。7 模块池峰值 `24/56/56/56/112/80/20 → 24/56/56/56/112/80/18`。final_head、proj、ffwd 的局部 run 峰值 72→70，但 FB04/05 最大峰值不变；G2 目标物理 REG 未自然跨阶。[逐核池](pool-summary.md)、[全部 run](source-pools.json)。

## 3.2 独立 UP 单因素

- 保持 pack5，单独令 v24_mask=9，覆盖 4,744 处独立转换，不绑定 quad。两种高低位置各 16,777,216 对 GPU 原语（共 33,554,432）与旧 UP 全位一致，含非有限位型既有语义；并非新增 IEEE NaN 支持。
- UP 单因素非 NOP SASS 152,076→150,179，PRMT 不变；STL/LDL 107/108→108/110。不能按省 PTX 条数推算帧收益。[原语](decode-tests.json)、[资源](hardware-up.md)。

## 3.3 解码算术与 G2 控制

- packed 立即数直接用于 `mul.rn.f16x2` 被驱动 JIT 和 ptxas 以参数不匹配拒绝，属于无效 PTX，未计时：[原始失败日志](build.log)。
- 增加严格等价 `shift` 算术因子：`(x & 0x017f017f)<<7 == (x<<7)&0xbf80bf80`，掩码移至左移之后；单因素及 split+UP+shift 分别构建，33,554,432 对 GPU 对照零差异。它没有改变解码精度。[原语](shift-tests.json)。
- 在 split+UP 上独立控制 6 个临界核，不组合堆 cap。API 跨阶均成立，但附带的资源代价如下：

|控制|实际 REG|STACK B|CTA/SM|STL/LDL|
|---|---:|---:|---:|---:|
|split_up_publish: cc_vit_1d_ffn_expand_publish_fp8|168|16|3|3/5|
|split_up_contract: cc_vit_1d_ffn_contract_chained_fp8|168|8|3|2/2|
|split_up_expand: cc_vit_1d_ffn_expand_chained_fp8|168|152|3|52/56|
|split_up_head: cc_split_swin_16h_final_head_512_wait_fp8|128|136|2|40/42|
|split_up_proj: cc_split_swin_16h_proj_512_chained_fp8|128|144|2|42/47|
|split_up_pool: cc_split_swin_16h_proj_pool_512_chained_fp8|162|0|3|0/0|

## 同轮正反配对结果

正值表示耗时下降；每项 50 warmup / 80 iter、正向 ABBA＋反向 BAAB。若首轮三档六方向全胜才进入 repeat；以两轮全胜为晋升门槛。

|轮次/候选|720p 降幅|900p 降幅|1080p 降幅|六方向全胜|
|---|---:|---:|---:|---|
|first/split|-0.022%|0.042%|-0.393%|False|
|first/split_up|0.384%|0.280%|0.079%|True|
|first/up|0.114%|0.217%|0.151%|False|
|caps/split_up_contract|-0.904%|0.208%|0.202%|False|
|caps/split_up_expand|-1.690%|-1.387%|-1.718%|False|
|caps/split_up_head|-0.083%|-0.384%|-0.246%|False|
|caps/split_up_pool|0.208%|-0.045%|0.609%|False|
|caps/split_up_proj|0.191%|0.059%|-0.207%|False|
|caps/split_up_publish|-0.017%|0.154%|0.305%|False|
|arithmetic/shift|0.203%|0.174%|-0.225%|False|
|arithmetic/split_up_shift|-0.180%|-0.434%|0.029%|False|
|repeat/split_up|0.191%|-0.161%|0.469%|False|

完整逐方向数字：[计时审计](timing-summary.md)、[原始 cap 运行](caps.json)、[算术运行](arithmetic.json)。均值为进程 GPU median 的均值；min、Wall 与 GPU timing 各自保留，不混拼或解释为 launch 气泡。

## 新 2×2 破坏性探针

重新构建 pack5 原点 P0（去 Pack）、P1（去 non-mapped Decode）、P2（双去除），三档正反顺序各两遍，共 48 次；4 个进程/版本/分辨率。只比较时长敏感度，不参与生产晋升，数值被破坏。

|宽度|Base ms|P0 ms|P1 ms|P2 ms|Base−P0|Base−P1|交互项|
|---|---:|---:|---:|---:|---:|---:|---:|
|1280|5.712000|5.566500|5.148500|5.366750|0.145500|0.563500|0.363750|
|1600|8.335500|8.233000|7.343500|7.774000|0.102500|0.992000|0.533000|
|1920|11.027250|10.860000|9.597750|10.294500|0.167250|1.429500|0.864000|

交互项严格按 355.md 的 `(Base−P0)+(Base−P1)−(Base−P2)`。独立重算历史 20:00 原始数据得到 +0.352/+0.182/+0.626ms；旧报告负号采用相反定义，不沿用成同一公式。[旧数据复核](probe-data-audit.json)、[本轮探针](probe-summary.json)。探针节省不是可全额兑现预算。

## 分支调度与交付

本轮不晋升 V3.2 DLL，继续封存 V3.1_pack5 为唯一 1.00×；分支 3 保持 Open，n=2/3，分支 4 保持 Open、n=0/3。

分支 1 Pruned 3/3；分支 2 原阶段标记 Closed 0/3，但新 P0 三档 12/12 正差值，必须交主脑复核是否重开，不能继续用旧变号证据说 Pack 已见底；分支 3 与 4 仍 Open。未开始分支 4 的代码改写。下一轮按新探针及剩余 Open 节点重新排优先级，不原样复跑本轮已否决候选。

- 13 项既有 Python 回归通过；UP/shift 各 33,554,432 对 GPU 原语，7 类别名 GPU 检验与全部整网末帧验证通过。
- 核心、生产五处及三 ZIP 的保护清单前后逐 SHA 核验一致：[前](protected-before.json)、[后](protected-after.json)。
- 清理临时 DLL、RGB、PTX、cubin、fatbin 缓存，仅保留文本证据及可能晋升的独立 DLL；清理清单见 cleanup.json。无部署、无 push，阶段独立 Git commit，无 Co-Authored-By。

本轮遥测共 6,062 点，温度 55～79°C，sw_thermal_slowdown 激活样本 0；高利用率样本 SM 中位 1530MHz。此统计覆盖构建、诊断和排除轮次，不作等频因果结论。清理 647 个临时文件、4,604,726,758 B，清理后再次核验九个受保护路径 SHA 全部不变。

日志入库统一 LF；构建失败 traceback 另清理行尾空白与多余空行，数值文本未改。转换前后 SHA 见 [log-encoding.json](log-encoding.json)。
