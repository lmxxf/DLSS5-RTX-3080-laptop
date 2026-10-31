from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;state=v['branches']['5'];verdict=f'晋升{sel["variant"]}为独立V4.3、下一轮唯一1.00×，SHA `{sel["sha256"]}`，不覆盖生产。' if sel else '本轮无晋升，保留V4.0为唯一1.00×；分支5正式Pruned3/3，七个预设分支全部Pruned3/3，Open=0。';c=json.loads((p/'clean-selection.json').read_text());q=json.loads((p/'quad-coverage.json').read_text());record=f'''

## 2026-11-01：PTX V4.3，剔除FB00的末轮联合与七分支K=3结算（闇）

{verdict} 分支5 {state['state']} {state['n']}/3，其他六分支保持Pruned3/3，全表Open={v['open_branch_count']}。

唯一参考V4.0 SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`，重建同SHA。候选1仅FB01四入口Pack4+FB02/03 Quad，非NOP144131、净减1330、PRMT净减847、STL/LDL98/98；FB00及其他排除模块逐字节一致。候选2保留指定upsample/ds_wait/inpview三个入口，当前参考实际仅upsample减少Spill，其他两个保持原值，未用旧基线差值记功。

候选3先查询FB01 Pack4+Quad诊断（活跃融合{q['fb123_quad_diagnostic']['FB01_active_fused']}组），按STACK/STL/LDL不增及官方CTA不降选择{len(c['FB01_selected'])}入口；outview因STL/LDL增长被剔除，再与FB23 Quad联合。14项结构/绑定/守卫/回边测试和33554432对GPU原语通过，独立O4确认7核心SASS；新增FB01去夹断保持实证/近似标签。

计数{v['counts']}，基线检查{v['exact_runs']}次末帧0bit，新增Pack4/联合{v['approximate_runs']}次按预设质量门。50/80严格串行正反ABBA/BAAB，首轮六向全胜全部repeat。十一保护路径不变，清理临时大二进制及帧，无单次.log；三个干净小提交，无Co-Authored-By、不push。结算按已执行七分支K=3预算，不将有限候选失败写成物理性能下限。

[完整回执](ptx-patcher/v43/README.md)、[配对](ptx-patcher/v43/timing-summary.md)、[验收](ptx-patcher/v43/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V4.3' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V4.3' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| **分支 5** |'):
  a=line.split('|');a[2]=f' **`[{state["state"]}]`** ';a[3]=f' **`{state["n"]} / 3`** ';a[-2]=a[-2].rstrip()+'；V4.3结算见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n'
if sel:
 s=s.replace('   - 当前唯一 `1.00×` 对比基线为','   - 本轮历史输入 `1.00×` 对比基线为',1);old=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'));s=s.replace(old,f'- **当前唯一 `1.00×` 对比基线**：**PTX V4.3 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽O4，SHA `{sel["sha256"]}`（独立封存，未覆盖生产）。\n- **V4.3本轮历史输入参考**：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`，本轮数据以此为分母。',1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V4.3 执行结算（2026-11-01）\n\n{verdict} 分支5 {state["state"]} {state["n"]}/3，其余六分支维持Pruned3/3，全表Open={v["open_branch_count"]}。三个候选均保持FB00模块字节不变，FB01 Quad按实际资源选择{len(c["FB01_selected"])}入口，剔除outview；命名spill3实际仅upsample在当前V4.0上减少Spill，已在回执澄清。所有首轮六向全胜均完成repeat，计数{v["counts"]}。[完整回执](ptx-patcher/v43/README.md)、[配对](ptx-patcher/v43/timing-summary.md)、[验收清理](ptx-patcher/v43/validation.json)。十一保护路径不变，临时大二进制清理，无.log碎文件，三个独立小提交，无Co-Authored-By、不push。\n';f.write_text(s);print(verdict)
