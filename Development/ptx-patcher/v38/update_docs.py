from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None
verdict=f'晋升{sel["variant"]}为独立V3.8，SHA `{sel["sha256"]}`，下一轮唯一1.00×，不覆盖生产。' if sel else '本轮无晋升，保持V3.1_pack5为唯一1.00×；七大预设分支全部Pruned3/3，Open=0。';states='；'.join(f'分支{b} {r["state"]} {r["n"]}/3' for b,r in v['branches'].items());joint=json.loads((p/'joint-selection.json').read_text())['joint'];record=f'''

## 2026-11-01：PTX V3.8，七分支K=3末轮精准冲击与结算（闇）

{verdict} {states}，分支1～4维持Pruned3/3。

A：仅FB02..06/FB04..06正零折叠、纯FB03+06 Pack4、fb26正零+Pack4；位点独立mov/cvt正零证明，排除FB00/01及其他指定模块的PTX/cubin/bin逐字节一致。B：仅FB03 inpview+upsample双入口exact/fast，其余36活跃入口相同。C：pool单核异步half视图，其余37入口相同。8个A×B+pool联合版本预先构造与冒烟，按预注册最弱方向收益优先规则，从本轮7个单因素数据选出`{joint}`再独立计时，无计时中编译或查询。

运行计数{v['counts']}，精确（含基线）{v['exact_runs']}次0bit，近似/实证{v['approximate_runs']}次按预设质量门验收。全部正式计时50/80串行、正反ABBA/BAAB，首轮六向全胜全部repeat；逐次输出嵌入JSON，无单次.log。九保护路径不变，临时大二进制与帧清理，三个独立提交，无Co-Authored-By、不push。结算基于有限七分支K=3预算，不把静态资源削减或有限负样本当作数学物理下限。

[回执](ptx-patcher/v38/README.md)、[跑分](ptx-patcher/v38/timing-summary.md)、[验收](ptx-patcher/v38/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.8' not in s;f.write_text(s+record)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.8' in s;lines=s.splitlines()
for i,line in enumerate(lines):
 for b,r in v['branches'].items():
  if line.startswith(f'| **分支 {b}** |'):
   a=line.split('|');a[2]=f' **`[{r["state"]}]`** ';a[3]=f' **`{r["n"]} / 3`** ';a[-2]=a[-2].rstrip()+'；V3.8结算见文末 ';lines[i]='|'.join(a)
s='\n'.join(lines)+'\n'
if sel:
 oldline=next(x for x in s.splitlines() if x.startswith('- **当前唯一 `1.00×` 对比基线**：'))
 current=f'- **当前唯一 `1.00×` 对比基线**：**PTX V3.8 / {sel["variant"]}**，`{sel["path"]}`，266,414,592 B，15/15原槽位O4，SHA256 `{sel["sha256"]}`（独立封存，未覆盖生产部署）。'
 historical='- **V3.8本轮历史输入参考**：V3.1_pack5，SHA256 `1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86`；本轮全部成绩以此为分母，后续实验以新V3.8为1.00×。'
 s=s.replace(oldline,current+'\n'+historical,1).replace('## 2. 本轮派单任务','## 2. 已执行的历史派单任务',1)
s+=f'\n### V3.8 执行结算（2026-11-01）\n\n{verdict} {states}。Open={v["open_branch_count"]}。所有首轮六向全胜者均完成repeat；计数{v["counts"]}。联合候选为`{joint}`，选择规则与全量数据已保留。[完整回执](ptx-patcher/v38/README.md)、[配对结果](ptx-patcher/v38/timing-summary.md)、[验收与清理](ptx-patcher/v38/validation.json)。九保护路径不变，无.log碎文件，清理临时大二进制，三个独立小提交，无Co-Authored-By，不push。\n';f.write_text(s);print(verdict,states)
