from pathlib import Path
import json,re
p=Path(__file__).resolve().parent;x=json.loads((p/'sass-resources.json').read_text());lines=['# Static SASS / resources (all exports, not dynamic executed counts)','','| FB | old SHFL total | new SHFL total | old max STACK | new max STACK |','|---|---:|---:|---:|---:|'];pairs={}
for i in range(7):
 a=x['old'][f'fb{i:02d}-sm86'];b=x['new'][f'fatbin{i:02d}'];lines.append(f'| {i:02d} | {a["totals"]["SHFL"]} | {b["totals"]["SHFL"]} | {a["max_stack"]} | {b["max_stack"]} |')
 pairs[str(i)]=[]
 for n,v in a['kernels'].items():
  if n not in b['kernels']:continue
  z=b['kernels'][n];pairs[str(i)].append({'kernel':n,'old':v,'new':z})
lines+=['','Original reduction SHFLs remain. Zero-SHFL refers only to the replacement MMA operand preparation. STACK is compiler-reported stack; LOCAL may be0 while stack spill loads/stores exist. Includes unexecuted variants.','','## Representative matching FP8 exports','','| FB | Kernel | old/new SHFL | old/new REG | old/new STACK |','|---|---|---:|---:|---:|']
for i,rr in pairs.items():
 vals=[r for r in rr if '_fp8' in r['kernel'] and r['old'].get('resources')]
 for r in vals[:2]:
  a,b=r['old'],r['new'];ar,br=a['resources'],b['resources'];lines.append(f'| {i} | {r["kernel"]} | {a["SHFL"]}/{b["SHFL"]} | {ar["REG"]}/{br["REG"]} | {ar["STACK"]}/{br["STACK"]} |')
imma=[{'kernel':n,**r} for n,r in x['v7']['fb18-sm86']['kernels'].items() if r['IMMA']]
(p/'v7-imma-kernels.json').write_text(json.dumps(imma,indent=2)+'\n');(p/'matched-kernels.json').write_text(json.dumps(pairs,indent=2)+'\n');(p/'sass-summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines));print('V7 IMMA kernels:',[(r['kernel'],r['IMMA']) for r in imma])
# Small, reviewable instruction excerpts; raw megabytes of SASS are regenerable.
s=(p/'artifacts/v7/fb18-sm86-sass.txt').read_text();out=[]
for chunk in s.split('Function : ')[1:]:
 if 'IMMA.' not in chunk:continue
 out+=['Function : '+chunk.splitlines()[0]]
 ls=chunk.splitlines();idx=next(i for i,l in enumerate(ls) if 'IMMA.' in l);out+=ls[max(0,idx-12):idx+20]
(p/'v7-imma-snippets.txt').write_text('\n'.join(out)+'\n')
