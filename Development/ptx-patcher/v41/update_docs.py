from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;n=v['branches']['5']['n'];j=json.loads((p/'joint-selection.json').read_text())['joint'];verdict=f'晋升{sel["variant"]}为独立V4.1与下一轮唯一1.00×，SHA `{sel["sha256"]}`，不覆盖生产。' if sel else '本轮无晋升，保留V4.0为唯一1.00×。';record=f'''

## 2026-11-01：PTX V4.1，在V4.0上补全驻留不变UP、正零与FB04 Pack4（闇）

{verdict} 分支5 Open {n}/3，其余六分支维持Pruned3/3，全表Open=1。

唯一参考V4.0 SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`，重建配方同SHA。三个UP增量分别加入pool/FB06/两者，均复核STACK/STL/LDL不增加及官方CTA不降；pool REG180→181/SASS6001→5841，FB06在完整V4.0配方下REG203→206/SASS3855→3533，二者0 Spill且2/4 CTA不变，总非NOP144979，纠正计划混用未叠加Pack4诊断数据的数字。

FB02/03增加80处正零，总580；FB04八个baseline零Spill活跃入口新增经验Pack4，保留近似标签。三个联合备选全部在计时前构造、查询与冒烟；单因素完成后按预注册最弱方向优先规则选`{j}`独立计时，未选联合仅保留资源/质量记录。13项安全/CFG测试与33554432个32位GPU模式原语通过，排除模块及入口一致性核验通过。

计数{v['counts']}，严格增量（含基线）{v['exact_runs']}次末帧0bit，新增Pack4/联合{v['approximate_runs']}次按预设质量门。50/80严格串行正反ABBA/BAAB，首轮六向全胜全部repeat。十一个保护路径SHA不变，无单次.log，清理临时大二进制与帧；三个干净小提交，无Co-Authored-By、不push。

[回执](ptx-patcher/v41/README.md)、[配对](ptx-patcher/v41/timing-summary.md)、[验收](ptx-patcher/v41/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V4.1' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V4.1' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| **分支 5** |'):
  a=line.split('|');a[2]=' **`[Open]`** ';a[3]=f' **`{n} / 3`** ';a[-2]=a[-2].rstrip()+'；V4.1结果见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n';s=s.replace('`198 → 200`','`203 → 206`').replace('`3,988 → 3,670`','`3,855 → 3,533`').replace('`318`','`322`').replace('`-318`','`-322`').replace('`144,983`','`144,979`').replace('`PRMT` 净减 `80` 条','`PRMT` 净减 `32` 条').replace('`PRMT` 净减 `96` 条','`PRMT` 净减 `64` 条')
if sel:
 old=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'));s=s.replace(old,f'- **当前唯一 `1.00×` 对比基线**：**PTX V4.1 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽O4，SHA `{sel["sha256"]}`（独立封存，未覆盖生产）。\n- **V4.1本轮历史输入参考**：V4.0，SHA `749daadb43f11b2fc0bf39d92a67809978f27b9e96150b631d50fc8d1ec9e3ca`，本轮数据以此为分母。',1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V4.1 执行回执（2026-11-01）\n\n{verdict} 分支5 Open {n}/3，其他六分支保持Pruned3/3，Open=1。实际完整配方新增UP的FB06为203→206 REG、3855→3533 SASS，保持0 Spill/4 CTA，pool保持0 Spill/2 CTA，两核合计总SASS144979；已按实际数据修正原计划。联合选择`{j}`，所有首轮六向全胜均repeat，计数{v["counts"]}。[完整回执](ptx-patcher/v41/README.md)、[配对结果](ptx-patcher/v41/timing-summary.md)、[验收清理](ptx-patcher/v41/validation.json)。十一保护路径不变，无.log碎文件，临时大二进制清理，三个小提交，无Co-Authored-By、不push。\n';f.write_text(s);print(verdict,'branch5',n)
