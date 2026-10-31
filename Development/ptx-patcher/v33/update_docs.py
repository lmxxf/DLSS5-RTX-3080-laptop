from pathlib import Path
import json,re
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());selected=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;probe=json.loads((p/'probe-summary.json').read_text());timing=json.loads((p/'timing-summary.json').read_text())
verdict=(f'晋升{selected["variant"]}为独立V3.3 DLL，SHA256 {selected["sha256"]}，封存为下一轮唯一1.00×；不覆盖生产五处和v0.3.0 ZIP。' if selected else '本轮不晋升V3.3 DLL，继续以V3.1_pack5为唯一1.00×。')
branches='；'.join(f'分支{i} {v[f"branch{i}"]["state"]} n={v[f"branch{i}"]["n"]}/3' for i in [2,3,4]);shared='/'.join(f'{probe[str(w)]["base_minus_ms"]["probe_shared"]:.6f}' for w in [1280,1600,1920]);global_family='/'.join(f'{probe[str(w)]["base_minus_ms"]["probe_global_family"]:.6f}' for w in [1280,1600,1920]);global_pure='/'.join(f'{probe[str(w)]["base_minus_ms"]["probe_global"]:.6f}' for w in [1280,1600,1920]);interaction='/'.join(f'{probe[str(w)]["shared_global_family_interaction_ms"]:.6f}' for w in [1280,1600,1920])
record=f'''\n\n## 2026-10-31：PTX V3.3，Shared/Global拆分、Two-Pass分相半池、重解码与纯Quad（闇）

唯一输入基线V3.1_pack5 SHA1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86；全量15/15 O4原槽位重建同SHA。先完成所有构建、GPU原语、38核四张硬件表与官方Occupancy API，再开始计时；阶段及每个runner起止时序独立核验全部串行，无计时排除或删样本。

任务A重新CFG核对全部5848个静态run解码事件：Shared2320、纯Global3304、Global+本地量化144、Global+常量80；任务单Global3528为含224混合事件的Global家族，不冒称纯load。6个专项探针加Base共84次正反对照，Shared敏感度{shared}ms，Global家族{global_family}ms，纯Global{global_pure}ms；Shared×Global家族交互{interaction}ms，不能相加当可兑现预算。144项保留真实ld.global与fallback pack可达定义、CFG块/前驱及指令上下文；全体未找到经mov隐藏的纯本地pack叶源，不无条件拓宽mapped。分支4仍Open，未实施Shared跨线程半精度存储改写。

任务B按累加器C/D依赖层分相，保持每链phase0→phase1→下一K32顺序，decoded-half事件11696不增加；FB00..06虚拟池24/56/56/56/112/80/20→12/28/28/28/28/28/6，模型raw snapshot0。物理C512 ffwd174→144regs，部分Spill核STACK反增，虚拟池不代替资源/API裁决。Spill内联重解码池≤6，但O4的SASS/REG/STACK计数回到基线；另做设备函数强制重算控制，明确计入CALL与ABI STACK，不拿它独自否定所有重算。计时前按零STACK且REG不增固定26入口guarded子集，并测试其与FB23纯Quad组合。

任务C仅FB01/02/03或仅FB02/03开纯Quad，mask12不含UP bit1。FB23融合1232对；quad_fb23的FB01及其他非目标cubin字节保持基线；33,554,432对GPU原语0差。本轮纯quad_all的FB01两核STACK104/80→96/72B，全网STL107→106、LDL108不变，修正旧捆绑候选“Quad必然加Spill”的解释。

10个严格候选首轮{v['counts']['bench']}次，repeat{v['counts'].get('repeat',0)}次，三档快验{v['counts']['smoke']}次；另84次专项探针对照中含12次严格Base。全部{v['strict_successful_runs']}次严格版本成功运行末帧对同配置V3.1严格0bit/maxabs0/nonfinite0。3模式×7类别名GPU、4个依赖链用例、Quad原语及13项既有回归通过。NCU未安装，循环信息沿用V2.5语义插桩，未冒称新动态stall/issued计数。

{verdict} {branches}。K=3剪枝只结算该批机制，不是物理极限证明；剩余Open节点仍保留。核心/生产五处/三ZIP保护性SHA全部不变，不部署、不push。清理临时大二进制，保留文本证据及独立晋升DLL（若有），立即独立commit，无Co-Authored-By。

[完整回执](ptx-patcher/v33/README.md)、[逐方向计时](ptx-patcher/v33/timing-summary.md)、[探针汇总](ptx-patcher/v33/probe-summary.json)、[CFG反证](ptx-patcher/v33/forwarding-audit.json)、[验收](ptx-patcher/v33/validation.json)。
'''
f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-10-31：PTX V3.3' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.3' in s;lines=s.splitlines()
for j,line in enumerate(lines):
 for i in [2,3,4]:
  if f'| **分支 {i}** |' in line:
   q=v[f'branch{i}'];parts=line.split('|');parts[2]=f' **`[{q["state"]}]`** ';parts[3]=f' **`{q["n"]} / 3`** ';parts[-2]+=f'；V3.3已结算，见文末回执 ';lines[j]='|'.join(parts)
s='\n'.join(lines)+'\n'
if selected:
 s=s.replace('- **当前唯一 `1.00×` 对比基线**：','- **V3.3本轮输入 `1.00×` 基线（历史）**：',1)
 s=s.replace('### 候选分支调度表（`K = 3`）',f'**下一轮唯一封存 `1.00×`：PTX V3.3**，`{selected["path"]}`，SHA256 `{selected["sha256"]}`。下列V3.2/V3.3探针属于本轮旧V3.1输入参考，后续须在新基线上重测。\n\n### 候选分支调度表（`K = 3`）',1)
s+=f'''\n### V3.3 执行回执（2026-10-31，闇）

{verdict} {branches}。详细[回执](ptx-patcher/v33/README.md)、[逐方向计时](ptx-patcher/v33/timing-summary.md)、[验收](ptx-patcher/v33/validation.json)。

任务A：84次专项探针对照，Shared {shared}ms、Global家族 {global_family}ms、纯Global {global_pure}ms，交互 {interaction}ms。Global家族3528含224混合事件；不线性相加。144项load/fallback合流均留CFG/指令反证，未找到可无条件转发的纯本地pack隐藏源；分支4仍有后续Shared布局探索空间。

任务B：分相虚拟池12/28/28/28/28/28/6，解码次数不增，实际驻留/Spill逐核核验；重解码内联、两目标剥离、强制调用以及guarded/Quad组合均已测试。任务C：纯Quad全网/FB23单因素剥离UP，quad_fb23的FB23以外cubin与基线同字节；原语33554432对0差。正式首轮{v['counts']['bench']}次、repeat{v['counts'].get('repeat',0)}次，所有{v['strict_successful_runs']}次严格版本成功运行末帧0bit、maxabs0、nonfinite0，计时全程严格串行。

生产五处和三个v0.3.0 ZIP不覆盖；清理临时大产物，立即独立commit，不push，无Co-Authored-By。剩余Open分支按新数据调度，不将单枝剪枝写成全网收官。
''';f.write_text(s)
(p/'branches.json').write_text(json.dumps({'branch1':{'state':'Pruned','n':3},'branch2':v['branch2'],'branch3':v['branch3'],'branch4':v['branch4']},indent=2)+'\n');print(verdict,branches)
