from pathlib import Path
import re,json,numpy as np
root=Path(__file__).resolve().parent
source=(root.parent/'phase6/analyze.py').read_text();ns={};exec(source[source.index('def read_log'):source.index("if __name__=='__main__':")],{'re':re,'np':np},ns)
read_log,load,accuracy=[ns[k] for k in ('read_log','load','accuracy')]
variants={}
for name in ['baseline','c32-only','layout-only','full','lowreg','zero-local','baseline-final','selected']:
 p=root/(name+'-bench.log')
 if not p.exists():continue
 cases=read_log(p)
 for w,c in cases.items():
  y=load(root/'artifacts/outputs'/name,w);base=load(root/'artifacts/outputs'/('baseline' if (root/'baseline-bench.log').exists() else 'baseline-final'),w)
  c['accuracy_vs_baseline']=accuracy(base,y);c['accuracy_vs_archived_phase6']=accuracy(load(root.parent/'phase6/artifacts/outputs/selected',w),y)
  vh=900 if w==1600 else 1080
  c['accuracy_vs_f32_visible']=accuracy(load(root.parent/'phase1/artifacts/outputs/f32',w)[:vh],y[:vh])
  assert c['accuracy_vs_baseline']['bitdiff']==c['accuracy_vs_baseline']['invalid']==c['accuracy_vs_archived_phase6']['bitdiff']==0
  assert len(c['kernels'])==32
  if name=='selected':assert all(k['lmem']==0 for k in c['kernels'].values())
 variants[name]=cases
lines=['# Phase 8: direct Ampere D bytes to AB fragments','', '50 warmup / 80 iterations; separate instrumented frame. 900p/1080p process 1600×1024 / 1920×1152. GPU excludes initialization, weights, transfers/readback. Default DVFS, not clock-locked.','', '| Variant | 900p min / median ms | 1080p min / median ms | Bitdiff 900/1080 | Nonzero LMem kernel kinds 900/1080 |','|---|---:|---:|---:|---:|']
for name,c in variants.items():
 a,b=c[1600],c[1920]
 lines.append(f'| {name} | {a["gpu_min"]:.3f} / {a["gpu_median"]:.3f} | {b["gpu_min"]:.3f} / {b["gpu_median"]:.3f} | {a["accuracy_vs_baseline"]["bitdiff"]}/{b["accuracy_vs_baseline"]["bitdiff"]} | '+ '/'.join(str(sum(r['lmem']>0 for r in c[w]['kernels'].values())) for w in (1600,1920))+' |')
base_name='baseline-final' if 'baseline-final' in variants else 'baseline';new_name=next(v for v in ['selected','zero-local','full'] if v in variants)
for w in (1600,1920):
 a,b=[variants[v][w] for v in [base_name,new_name]]
 lines+=['',f'## {w}: {base_name} → {new_name}','', '| Kernel | Baseline ms | Selected ms | Regs | LMem B | SMem B | OccW |','|---|---:|---:|---:|---:|---:|---:|']
 for name,x in a['kernels'].items():
  y=b['kernels'][name];pairs=[f'{int(x[k])}→{int(y[k])}' for k in ['regs','lmem','smem','occw']]
  lines.append(f'| {name} | {x["ms"]:.6f} | {y["ms"]:.6f} | '+' | '.join(pairs)+' |')
 for name,c in variants.items():lines.append(f'\n{name}: instrumented kernel total {sum(k["ms"] for k in c[w]["kernels"].values()):.6f} ms. Baseline accuracy `{json.dumps(c[w]["accuracy_vs_baseline"])}`; F32 visible `{json.dumps(c[w]["accuracy_vs_f32_visible"])}`.')
(root/'results.json').write_text(json.dumps(variants,indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:17]))
