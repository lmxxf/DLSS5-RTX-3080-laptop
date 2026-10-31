from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;n=v['branches']['5']['n'];verdict=f'晋升{sel["variant"]}为独立V3.9、下一轮唯一1.00×，SHA `{sel["sha256"]}`，不覆盖生产。' if sel else '本轮无晋升，保持V3.8为唯一1.00×。';u=json.loads((p/'up-pair-summary.json').read_text());c=json.loads((p/'up-clean-selection.json').read_text())
record=f'''

## 2026-11-01：PTX V3.9，在V3.8基线上扩展零常量/Pack4与UP-Pair（闇）

{verdict} 分支5 Open {n}/3，分支1～4、6、7保持Pruned3/3，全表Open=1。

所有参考均为V3.8 SHA `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`，未以V3.1成绩抵充本轮收益。540/540/676处正零扩展候选分别启用FB1456、FB3456、全网排除FB00 upsample，no_fb0up无活跃入口REG/STACK增长；Pack4分别叠加FB36/FB2356，保留V3.8原500处零折叠。

UP审计确认4744处来自2372个拆半字，但只有{u['eligible_UPs']}处满足同基本块稳定源条件，删除{u['removed_splits']}个无其他用户的拆分；跨块位点保留旧解码。GPU原语33554432个32位模式、两个half2输出均零差异，含保留码；6项防覆写/别名/守卫/跨块/其他用户测试通过。按实际REG/STACK/STL/LDL及官方驻留选择{len(c['selected'])}个活跃入口构建clean并复核，未把纯语法来源等同全2372对均可安全直解。

运行计数{v['counts']}，精确（含基线）{v['exact_runs']}次末帧0bit，近似/实证{v['approximate_runs']}次保留预设质量门。正式计时50/80串行正反ABBA/BAAB，首轮六向全胜全部repeat。十保护路径SHA不变，清理临时二进制与帧，无单次.log，三个干净小提交，无Co-Authored-By、不push。

[实验回执](ptx-patcher/v39/README.md)、[计时](ptx-patcher/v39/timing-summary.md)、[验收](ptx-patcher/v39/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.9' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.9' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| **分支 5** |'):
  a=line.split('|');a[2]=' **`[Open]`** ';a[3]=f' **`{n} / 3`** ';a[-2]=a[-2].rstrip()+'；V3.9结果见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n'
s=s.replace('`PRMT = 19,549`（净减 `312` 条）','`PRMT = 19,525`（净减 `336` 条）')
s=s.replace('`FB00 (36)`、`FB01 (64)`','`FB00 (60)`、`FB01 (40)`').replace('`FB01`（64 处','`FB01`（40 处').replace('（`564` 处正零折叠）','（`540` 处正零折叠）').replace('（`664` 处正零折叠，','（`676` 处正零折叠，')
if sel:
 old=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'));s=s.replace(old,f'- **当前唯一 `1.00×` 对比基线**：**PTX V3.9 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽O4，SHA `{sel["sha256"]}`（独立封存，未覆盖生产）。\n- **V3.9本轮输入历史参考**：V3.8，SHA `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`，本轮数据仍以此为分母。',1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V3.9 执行回执（2026-11-01）\n\n{verdict} 分支5 Open {n}/3；其他六个分支保持Pruned3/3，全表Open=1。计划硬账已纠正：FB00/01为60/40，排除FB00 upsample为4处，三个候选总覆盖540/540/676；UP全2372对语法来源已确认，实际满足同基本块条件并移除拆分{u["removed_splits"]}对，其余保留旧路径。所有首轮六向全胜均补repeat，计数{v["counts"]}。[完整回执](ptx-patcher/v39/README.md)、[相对V3.8的配对](ptx-patcher/v39/timing-summary.md)、[验收清理](ptx-patcher/v39/validation.json)。十保护路径不变，三个小提交，无Co-Authored-By、不push。\n';f.write_text(s);print(verdict,'branch5',n)
