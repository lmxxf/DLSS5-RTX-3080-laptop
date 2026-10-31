from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;n=v['branches']['5']['n'];j=json.loads((p/'joint-selection.json').read_text())['joint'];verdict=f'晋升{sel["variant"]}为独立V4.2与下一轮唯一1.00×，SHA `{sel["sha256"]}`，不覆盖生产。' if sel else '本轮无晋升，保留V4.0为唯一1.00×。';record=f'''

## 2026-11-01：PTX V4.2，分支5第二轮FB00隔离、FB01降Spill和7-SASS Quad（闇）

{verdict} 分支5 Open {n}/3，其他六分支保持Pruned3/3，Open=1。

A仅FB00五活跃入口新增Pack4、排除pre_block，当前配方非NOP净减168，所有FB00入口STACK/STL/LDL不增；不把旧新增Spill来源直接当作整帧唯一因果。B先构造FB01四入口诊断，按实际STACK/STL/LDL不增加全部入选clean，净减488，全网STL/LDL99/100→98/98，不额外卡REG。

C独立O4切片验证旧两次Pack4+拼接9核心SASS、Quad7核心（2 HMUL2+2 LEA+2 LOP3+1 PRMT），33554432对GPU原语零差异，包含Inf/NaN/负零；相对既有Pack4语义。声明绑定、同块源稳定、半字无中途读取和全CFG死后证明通过14项结构/作用域/守卫/回边测试。全导出融合1232组，活跃入口424组，实际PRMT净减847（修正预估848）、非NOP净减842。clean八活跃入口均满足无Spill增长。两个联合备选全部预构造/查询/冒烟，按预注册最弱方向优先规则选`{j}`独立计时。

计数{v['counts']}，严格增量（含基线）{v['exact_runs']}次末帧0bit，新增Pack4/联合{v['approximate_runs']}次按预设质量门。全部50/80串行正反ABBA/BAAB，首轮六向全胜全部repeat。十一保护路径SHA不变，清理临时大二进制和帧，无单次.log；三个独立小提交，无Co-Authored-By、不push。

[完整回执](ptx-patcher/v42/README.md)、[配对](ptx-patcher/v42/timing-summary.md)、[验收](ptx-patcher/v42/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V4.2' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V4.2' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| **分支 5** |'):
  a=line.split('|');a[2]=' **`[Open]`** ';a[3]=f' **`{n} / 3`** ';a[-2]=a[-2].rstrip()+'；V4.2结果见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n';s=s.replace('直接再砍 `848` 条 `PRMT`','本轮实际净减 `847` 条 `PRMT`')
if sel:
 s=s.replace('   - 当前唯一 `1.00×` 对比基线为','   - 本轮历史输入 `1.00×` 对比基线为',1);old=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'));s=s.replace(old,f'- **当前唯一 `1.00×` 对比基线**：**PTX V4.2 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽O4，SHA `{sel["sha256"]}`（独立封存，未覆盖生产）。\n- **V4.2本轮历史输入参考**：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`，本轮数据以此为分母。',1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V4.2 执行回执（2026-11-01）\n\n{verdict} 分支5 Open {n}/3，其余六分支保持Pruned3/3，Open=1。独立O4确认7核心Quad，33554432对GPU零差异与14项结构测试通过；活跃入口424组融合，PRMT实际净减847、非NOP净减842。A/B/Quad clean均满足STACK/STL/LDL不增加，联合选择`{j}`。所有首轮六向全胜均repeat，计数{v["counts"]}。[回执](ptx-patcher/v42/README.md)、[计时](ptx-patcher/v42/timing-summary.md)、[验收清理](ptx-patcher/v42/validation.json)。十一保护路径不变，临时大二进制已清理，无.log碎文件，三个小提交，无Co-Authored-By、不push。\n';f.write_text(s);print(verdict,'branch5',n)
