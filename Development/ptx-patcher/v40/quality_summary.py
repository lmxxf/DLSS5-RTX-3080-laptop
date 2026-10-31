from pathlib import Path
import json
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());rows=[]
for f in ['smoke.json','bench.json','repeat.json']:
 if (p/f).exists():rows+=json.loads((p/f).read_text())
lines=['# V4.0 输出质量汇总','','三档固定输入、末帧对V3.8；经验Pack4仍按实证候选标记，不推断未测中间激活范围。','','|候选|类型|次数|最大bit-diff|最大绝对误差|最小非无限PSNR dB|最大非有限数|质量全过|','|---|---|---:|---:|---:|---:|---:|---|']
for n,c in cs.items():
 r=[x for x in rows if x['variant']==n];ps=[x['quality']['PSNR_db'] for x in r if x['quality']['PSNR_db'] is not None];lines.append(f'|{n}|'+('近似/实证' if c['approximate'] else '精确')+f'|{len(r)}|{max(x["quality"]["bitdiff"] for x in r)}|{max(x["quality"]["maxabs"] for x in r)}|{min(ps) if ps else "∞"}|{max(x["quality"]["nonfinite"] for x in r)}|{all(x["quality"]["quality_pass"] for x in r)}|')
(p/'quality-summary.md').write_text('\n'.join(lines)+'\n');print('quality summary',len(rows),'runs')
