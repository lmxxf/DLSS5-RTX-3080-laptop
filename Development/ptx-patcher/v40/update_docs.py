from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None;n=v['branches']['5']['n'];verdict=f'晋升{sel["variant"]}为独立V4.0、下一轮唯一1.00×，SHA `{sel["sha256"]}`，不覆盖生产。' if sel else '本轮无晋升，保持V3.8为唯一1.00×。';c=json.loads((p/'cfg-clean-selection.json').read_text());record=f'''

## 2026-11-01：PTX V4.0，分支5第二轮零Spill隔离、全CFG UP拓宽与Pack4联合（闇）

{verdict} 分支5 Open {n}/3，其他六分支保持Pruned3/3，全表Open=1。

A：仅V3.9 clean中FB2345实际改写的16个零STACK/STL/LDL活跃入口，其余代码保持基线；静态非NOP净减1439（641+651+86+61），修正计划FB04 104/总1457硬账。另只增加FB01 inpview，使STACK64→56、STL/LDL11/15→10/14。没有把历史720p回退直接归因为FB00/01。

B：1031对/2062处cross_block UP全部通过唯一无守卫half定义、split支配use及所有CFG路径源32位无覆写证明，包含循环且守卫写入也视为覆写；没有用静态定义集合相等代替路径证明或放宽循环重置。6项基本安全测试、7项CFG测试和33554432个32位GPU模式逐位一致。按实际资源选{len(c['selected'])}个活跃入口构造cfg_clean，并分别与Pack4_FB2356联合；CFG-all只作资源诊断与质量冒烟，正式计时只含指定5候选。

计数{v['counts']}，精确（含基线）{v['exact_runs']}次末帧0bit，近似/实证{v['approximate_runs']}次保留预设质量门；正式计时50/80严格串行正反ABBA/BAAB，首轮六向全胜者全部repeat。十保护路径SHA不变，清理临时大二进制与帧，不留单次.log，三个小提交，无Co-Authored-By、不push。

[完整回执](ptx-patcher/v40/README.md)、[配对](ptx-patcher/v40/timing-summary.md)、[验收](ptx-patcher/v40/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V4.0' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V4.0' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| **分支 5** |'):
  a=line.split('|');a[2]=' **`[Open]`** ';a[3]=f' **`{n} / 3`** ';a[-2]=a[-2].rstrip()+'；V4.0结果见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n';s=s.replace('`104` 条 SASS','`86` 条 SASS').replace('`1,457` 条 SASS','`1,439` 条 SASS')
if sel:
 s=s.replace('   - 当前唯一 `1.00×` 对比基线为','   - 本轮历史输入 `1.00×` 对比基线为',1)
 old=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'));s=s.replace(old,f'- **当前唯一 `1.00×` 对比基线**：**PTX V4.0 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽O4，SHA `{sel["sha256"]}`（独立封存，未覆盖生产）。\n- **V4.0本轮历史输入参考**：V3.8，SHA `da27f34c5e10b884dd02b448eab424a4f44109ef08efc83e6a447100acd697c3`；本轮成绩以此为分母。',1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V4.0 执行回执（2026-11-01）\n\n{verdict} 分支5 Open {n}/3，其余六分支维持Pruned3/3，Open=1。1031对跨块UP全数通过严格全路径无覆写证明；零Spill子集净减1439，FB04小计86，已纠正计划硬账。全部首轮六向全胜者完成repeat，计数{v["counts"]}。[回执](ptx-patcher/v40/README.md)、[计时](ptx-patcher/v40/timing-summary.md)、[验收清理](ptx-patcher/v40/validation.json)。十保护路径不变，无.log碎文件，临时大二进制已清理，三个干净小提交，无Co-Authored-By、不push。\n';f.write_text(s);print(verdict,'branch5',n)
