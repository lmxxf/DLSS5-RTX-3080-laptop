from pathlib import Path
import json,re
p=Path(__file__).resolve().parent;dev=p.parent.parent
v=json.loads((p/'validation.json').read_text());probe=json.loads((p/'probe-summary.json').read_text());n=v['branch3_n_after'];formal=264+v['counts'].get('repeat',0);selected=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None
outcome=f'晋升独立V3.2候选{selected["variant"]}（SHA {selected["sha256"]}），分支3重置n=0/3，封存为下一轮1.00×。' if selected else '11个计时单因素/组合均未通过三档两轮正反全胜门槛，不晋升V3.2 DLL，保留V3.1_pack5；分支3保持Open、n=2/3，分支4保持Open、n=0/3。'
decode='/'.join(f'{probe[str(w)]["base_minus_p1_ms"]:.6f}' for w in [1280,1600,1920]);pack='/'.join(f'{probe[str(w)]["base_minus_p0_ms"]:.6f}' for w in [1280,1600,1920])
record=f'''\n\n## 2026-10-31：PTX V3.2，半步Decode池、独立UP、等价算术与G2临界核控制（闇）

严格以V3.1_pack5 SHA1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86为唯一1.00×基线，重建15/15 O4原槽位SHA完全一致。先核38活跃核SASS/REG/STACK、官方CUDA Occupancy API及真实Grid表、原始ABBA、2×2与分支表，再生成文字报告。四表与全部机器数据归档v32；NCU未安装，循环信息明确沿用V2.5语义插桩，等待距离仅词法计数，未冒充硬件stall或动态occupancy。

Phase-Split将encoded解码/释放细化至2*i+phase，并在原源被当前或更早MMA写坏前提前解码second；保留mapped隐式源备份和MMA顺序。7类128warp独立upfront-snapshot GPU别名测试全0bit。38核368个run、5848个encoded事件中240个单次使用；FB00..06池峰值24/56/56/56/112/80/20→24/56/56/56/112/80/18，部分C512 run72→70，但目标G2物理REG没有自然跨阶。

独立UP仅mask8→9、不绑quad，4744处转换GPU33554432对全位0差；38核非NOP152076→150179，HMMA13188不变，STL/LDL107/108→108/110。解码直接packed立即数乘法被驱动JIT/ptxas拒绝，保留失败证据、不计时；另测严格等价先移位后掩码及其split+UP组合，33554432对GPU原语0差，SASS计数/资源未减但35核机器码字节变化，完整配对实测。

在split+UP上另做publish/contract/expand/head/proj/pool六个单核cap控制，API均跨阶。publish/contract分别16/8B STACK，expand/head/proj分别152/136/144B；pool实际162regs、零STACK、3CTA/SM，但三档方向未全稳。每项均对同轮V3.1_pack5正反ABBA，不用静态池削减或理论驻留提升充整帧收益。

原首轮72次因与驱动编译/资源查询重叠，全部保留为筛查且排除计时；串行补齐12次repair+60次clean。有效首轮72、cap144、算术48次，加条件repeat，共{formal}次正式配对；所有严格候选连同筛查/3快验共{v['strict_successful_runs']}次成功运行末帧均对同配置基线0bit、maxabs0、nonfinite0，13项既有回归通过。{'首轮全胜候选按固定门槛补repeat，完整结果见回执。' if v['repeat_eligible'] else '无首轮三档六方向全胜候选，未为失败项反复重测挑样本。'}

新建并串行重跑48次2×2破坏性探针：Base−P1三档均值{decode}ms、12/12正；Base−P0为{pack}ms，也12/12正。旧20:00的Pack变号不能继续当见底依据，分支2保留阶段Closed历史状态但标记需主脑复核重开，未越权启动Pack新实现。交互项按355公式(Base−P0)+(Base−P1)−(Base−P2)，旧记录负号为相反定义；探针敏感度不当成可兑现预算。

{outcome}不将本批次负结果当作全网收官，不提前剪枝。生产五处、原DLL和三个v0.3.0 ZIP保护性SHA全部不变；不部署、不push。清理本轮临时DLL/RGB/PTX/cubin/fatbin缓存，仅保留文本证据与可能晋升的独立候选；完成后立即独立commit，无Co-Authored-By。

[完整回执](ptx-patcher/v32/README.md)、[逐方向计时](ptx-patcher/v32/timing-summary.md)、[四表](ptx-patcher/v32/hardware-baseline.md)、[验收](ptx-patcher/v32/validation.json)、[新探针](ptx-patcher/v32/probe-summary.json)。
'''
f=dev/'DevHistory.md';text=f.read_text();assert '## 2026-10-31：PTX V3.2' not in text;f.write_text(text+record)
f=dev/'WorkingPlan.md';text=f.read_text();lines=text.splitlines()
for i,line in enumerate(lines):
 if '| **分支 3** |' in line:
  lines[i]=line.replace('**`1 / 3`**',f'**`{n} / 3`**').replace('此前仅 `V3.0` 全 run 重排未晋升 (`n=1`)',f'`V3.0` 及本轮 `V3.2` 均未晋升 (`n={n}`)' if n else '本轮 V3.2 已晋升，n=0')
 if '| **分支 2** |' in line:lines[i]=line.replace('阶段收官','阶段收官；V3.2新P0三档12/12正，需主脑复核是否重开')
text='\n'.join(lines)+'\n'
if selected:
 text=text.replace('- **当前唯一 `1.00×` 对比基线**：', '- **V3.2 本轮输入 `1.00×` 基线（历史）**：',1)
 text=text.replace('### 候选分支调度表（`K = 3`）',f'**下一轮唯一封存 `1.00×` 基线：PTX V3.2**，`{selected["path"]}`，SHA256 `{selected["sha256"]}`。下列2000/V3.2探针属于旧V3.1参考，下一轮须在新基线上重测。\n\n### 候选分支调度表（`K = 3`）',1)
assert '### V3.2 执行回执（2026-10-31，闇）' not in text
text+=f'''\n### V3.2 执行回执（2026-10-31，闇）

{outcome}完整证据见[回执](ptx-patcher/v32/README.md)、[计时](ptx-patcher/v32/timing-summary.md)、[四表](ptx-patcher/v32/hardware-baseline.md)、[验收](ptx-patcher/v32/validation.json)。

完成Phase-Split、UP单因素、split+UP、等价shift及组合，以及六个单核cap控制。pool162regs/零STACK/3CTA确实跨阶；其他核跨阶引入8～152B STACK，均按真实整帧ABBA裁决。有效正式配对{formal}次，初轮并发72次全部排除并串行补齐；成功严格运行合计{v['strict_successful_runs']}次末帧0bit/maxabs0/nonfinite0，7类别名GPU、UP/shift各33554432对原语、13项回归通过。{'repeat结果详见回执。' if v['repeat_eligible'] else '无首轮全档双向胜出项，未进入repeat。'}

新2×2另48次：去Decode为{decode}ms，去Pack为{pack}ms，二者均12/12正。**新事实：Pack重新呈全档正敏感度，分支2的Closed是阶段状态，不是见底证明；交主脑复核重开/排期。** 分支4仍Open，本轮未实现，分支3未达K=3仍Open。保护性SHA前后不变；清理临时大产物，立即独立commit，不部署、不push，无Co-Authored-By。
'''
f.write_text(text)
branches=[{'branch':1,'state':'Pruned','n':3},{'branch':2,'state':'Closed','n':0,'needs_reassessment':True,'evidence':'new P0 12/12 positive; principal planner to reassess reopening'},{'branch':3,'state':'Open','n':n,'K':3},{'branch':4,'state':'Open','n':0,'K':3}]
(p/'branches.json').write_text(json.dumps(branches,indent=2)+'\n');print(outcome)
