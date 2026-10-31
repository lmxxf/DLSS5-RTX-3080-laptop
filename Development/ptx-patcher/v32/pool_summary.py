from pathlib import Path
import json
p=Path(__file__).resolve().parent;d=json.loads((p/'source-pools.json').read_text());active=json.loads((p/'resources.json').read_text())['baseline'];out={}
for mode,rows in d.items():
 out[mode]={n:{'temporary_b32_peak':max([r['temporary_b32_peak'] for r in rows if r['kernel']==n] or [0]),'runs':sum(r['kernel']==n for r in rows),'single_use_encoded_operands':sum(r['single_use_encoded_operands'] for r in rows if r['kernel']==n),'backup_moves':sum(r['backup_moves'] for r in rows if r['kernel']==n)} for n in active}
(p/'pool-summary.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# Half-step pool source audit','','38 launched FP8 kernels; zero means no MMA run (standalone UP). Peak is allocated virtual b32 pool per run, not physical registers.','','|Kernel|Old peak|Split peak|Runs|Single-use encoded operands|Backup moves|','|---|---:|---:|---:|---:|---:|']
for n in active:
 a,b=out['baseline'][n],out['split'][n];lines.append(f'|{n}|{a["temporary_b32_peak"]}|{b["temporary_b32_peak"]}|{b["runs"]}|{b["single_use_encoded_operands"]}|{b["backup_moves"]}|')
(p/'pool-summary.md').write_text('\n'.join(lines)+'\n')
for fb in range(7):
 names=[n for n,r in active.items() if r['FB']==fb];print('FB',fb,'peaks',*[max(out[m][n]['temporary_b32_peak'] for n in names) for m in out],'single_use',sum(out['baseline'][n]['single_use_encoded_operands'] for n in names))
