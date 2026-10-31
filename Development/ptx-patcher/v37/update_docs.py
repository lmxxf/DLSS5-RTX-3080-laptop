from pathlib import Path
import json
p=Path(__file__).resolve().parent;dev=p.parent.parent;v=json.loads((p/'validation.json').read_text());assert v['passed'] and v['cleanup_complete'];sel=json.loads((p/'selected.json').read_text()) if (p/'selected.json').exists() else None
verdict=f'晋升{sel["variant"]}为独立V3.7 SHA `{sel["sha256"]}`，下一轮唯一1.00×，不覆盖生产。' if sel else '本轮无晋升，保持V3.1_pack5为唯一1.00×。';states='；'.join(f'分支{b} {r["state"]} n={r["n"]}/3' for b,r in v['branches'].items());rec=f'''

## 2026-11-01：PTX V3.7，QKV单核、680正零与FB03逐入口剥离（闇）

{verdict} {states}。分支1～4仍为Pruned3/3。

分支7：循环版与128线程固定偏移展开版均只改QKV512；其余37入口PTX/SASS逐项相同。分支5：680处正零由独立mov/cvt定义链复核，直接mov.b16 0，GPU原语与STG RZ核验；再叠加FB2356/36经验Pack4。分支6：FB03四入口单列，预先选择REG下降两核、排除inpview三核，以及各自联合QKV展开+正零的候选，未按结果倒推子集。

运行计数{v['counts']}，精确（含基线）{v['exact_runs']}次0bit，近似/实证{v['approximate_runs']}次保留质量门结果。计时严格串行50/80、正反ABBA/BAAB，首轮六方向全胜全部repeat；资源静态削减不冒充动态净收益。九个保护路径SHA不变，清理临时大二进制及帧，无单次.log，三个职责提交，无Co-Authored-By、不push。

[实验回执](ptx-patcher/v37/README.md)、[配对数据](ptx-patcher/v37/timing-summary.md)、[验收](ptx-patcher/v37/validation.json)。
''';f=dev/'DevHistory.md';s=f.read_text();assert '## 2026-11-01：PTX V3.7' not in s;f.write_text(s+rec)
f=dev/'WorkingPlan.md';s=f.read_text();assert 'WorkingPlan — PTX V3.7' in s;lines=s.splitlines()
for j,line in enumerate(lines):
 for b,r in v['branches'].items():
  if line.startswith(f'| **分支 {b}** |'):
   a=line.split('|');a[2]=f' **`[{r["state"]}]`** ';a[3]=f' **`{r["n"]} / 3`** ';a[-2]=a[-2].rstrip()+'；V3.7结果见文末回执 ';lines[j]='|'.join(a)
s='\n'.join(lines)+'\n'
if sel:
 s=s.replace('- **当前唯一 `1.00×` 对比基线**：','- **V3.7输入历史 `1.00×` 基线**：',1);s+=f'\n**下一轮唯一1.00×：V3.7**，`{sel["path"]}`，SHA `{sel["sha256"]}`。\n'
s+=f'\n### V3.7 执行回执（2026-11-01）\n\n{verdict} {states}。所有首轮六方向全胜候选已repeat，计数{v["counts"]}。完整[回执](ptx-patcher/v37/README.md)、[正反配对](ptx-patcher/v37/timing-summary.md)、[验收与清理](ptx-patcher/v37/validation.json)。九个保护路径不变，三小提交，不加Co-Authored-By，不push；保留剩余Open分支，未以本轮结果宣布全局收敛。\n';f.write_text(s);print(verdict,states)
