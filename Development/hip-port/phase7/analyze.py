#!/usr/bin/env python3
from pathlib import Path
import re,json
import numpy as np
root=Path(__file__).resolve().parent
# Same parsing and accuracy denominators as Phase 6, without running its CLI.
source=(root.parent/'phase6/analyze.py').read_text();ns={};exec(source[source.index('def read_log'):source.index("if __name__=='__main__':")],{'re':re,'np':np},ns)
read_log,load,accuracy=[ns[k] for k in ('read_log','load','accuracy')]
variants={}
for name in ('baseline','step12','hoist','step12-repeat','baseline-repeat','selected'):
 p=root/(name+'-bench.log')
 if not p.exists():continue
 cases=read_log(p)
 for w,c in cases.items():
  y=load(root/'artifacts/outputs'/name,w);base=load(root/'artifacts/outputs/baseline',w)
  c['accuracy_vs_baseline']=accuracy(base,y)
  c['accuracy_vs_archived_phase6']=accuracy(load(root.parent/'phase6/artifacts/outputs/selected',w),y)
  assert c['accuracy_vs_baseline']['bitdiff']==0 and c['accuracy_vs_baseline']['invalid']==0
  assert c['accuracy_vs_archived_phase6']['bitdiff']==0
  assert len(c['kernels'])==32 and all(k['lmem']==0 for k in c['kernels'].values())
  original=load(root.parent/'phase1/artifacts/outputs/f32',w);vh=900 if w==1600 else 1080
  c['accuracy_vs_f32_visible']=accuracy(original[:vh],y[:vh])
 variants[name]=cases
lines=['# Phase 7: branchless FP8 / constant clamps / invariant input decode','', '50 warmup / 80 iterations, separate instrumented frame. 900p/1080p process 1600×1024 / 1920×1152. Initialization, weights, uploads/readback excluded. Default DVFS; no clock lock.','', '| Variant | 900p min / median ms | 1080p min / median ms | Bitdiff 900/1080 | Active local-memory kernels 900/1080 |','|---|---:|---:|---:|---:|']
for name,c in variants.items():
 a,b=c[1600],c[1920]
 lines.append(f'| {name} | {a["gpu_min"]:.3f} / {a["gpu_median"]:.3f} | {b["gpu_min"]:.3f} / {b["gpu_median"]:.3f} | {a["accuracy_vs_baseline"]["bitdiff"]}/{b["accuracy_vs_baseline"]["bitdiff"]} | '+ '/'.join(str(sum(r['lmem']>0 for r in c[w]['kernels'].values())) for w in (1600,1920))+' |')
for w in (1600,1920):
 lines+=['',f'## {w} kernel breakdown','', '| Kernel | Baseline ms | 1+2 ms | Hoist ms | Regs baseline→1+2→hoist | LMem B | OccW |','|---|---:|---:|---:|---|---|---|']
 names=list(variants['baseline'][w]['kernels'])
 for name in names:
  rows=[variants[v][w]['kernels'].get(name) for v in ('baseline','step12','hoist') if v in variants]
  ms=['—' if r is None else f'{r["ms"]:.6f}' for r in rows]
  fields=['→'.join('—' if r is None else str(int(r[k])) for r in rows) for k in ('regs','lmem','occw')]
  lines.append('| '+name+' | '+' | '.join(ms+fields)+' |')
 for name,c in variants.items():lines.append(f'\n{name}: kernel total {sum(r["ms"] for r in c[w]["kernels"].values()):.6f} ms; accuracy `{json.dumps(c[w]["accuracy_vs_baseline"])}`; F32 visible `{json.dumps(c[w]["accuracy_vs_f32_visible"])}`.')
(root/'results.json').write_text(json.dumps(variants,indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:13]))
