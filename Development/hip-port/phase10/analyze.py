from pathlib import Path
import re,json,numpy as np
root=Path(__file__).resolve().parent
src=(root.parent/'phase6/analyze.py').read_text();ns={};exec(src[src.index('def read_log'):src.index("if __name__=='__main__':")],{'re':re,'np':np},ns)
read_log,load,accuracy=[ns[k] for k in ('read_log','load','accuracy')]
variants={}
for name in ['baseline','caps','optimized','lowreg-fix','baseline-final','selected']:
 p=root/(name+'-bench.log')
 if not p.exists():continue
 text=p.read_text();cases=read_log(p)
 for w,c in cases.items():
  y=load(root/'artifacts/outputs'/name,w);base=load(root/'artifacts/outputs/baseline',w)
  c['accuracy_vs_baseline']=accuracy(base,y);c['accuracy_vs_phase9']=accuracy(load(root.parent/'phase9/artifacts/outputs/selected',w),y)
  vh=900 if w==1600 else 1080;c['accuracy_vs_f32_visible']=accuracy(load(root.parent/'phase1/artifacts/outputs/f32',w)[:vh],y[:vh])
  assert c['accuracy_vs_baseline']['bitdiff']==c['accuracy_vs_baseline']['invalid']==c['accuracy_vs_phase9']['bitdiff']==0
  assert len(c['kernels'])==32
  c['kernel_total']=sum(r['ms'] for r in c['kernels'].values());c['lmem_kernel_kinds']=sum(r['lmem']>0 for r in c['kernels'].values())
  if name=='selected':assert c['lmem_kernel_kinds']==0
 variants[name]=cases
lines=['# Phase 10: register ceilings + finite FP8 saturation','', '50 warmup /80 iter; 1600×1024 /1920×1152 processing, Small31 Style1, Graph off, default DVFS. GPU excludes initialization/uploads/readback. Kernel totals are separate single instrumented frames.','', '| Variant | 900p GPU min /median | 900p Wall med | 900p kernel total | 1080p GPU min /median | 1080p Wall med | 1080p kernel total | LMem kinds 900/1080 |','|---|---:|---:|---:|---:|---:|---:|---:|']
for name,c in variants.items():
 a,b=c[1600],c[1920];lines.append(f'| {name} | {a["gpu_min"]:.3f} /{a["gpu_median"]:.3f} | {a["wall_median"]:.3f} | {a["kernel_total"]:.6f} | {b["gpu_min"]:.3f} /{b["gpu_median"]:.3f} | {b["wall_median"]:.3f} | {b["kernel_total"]:.6f} | {a["lmem_kernel_kinds"]}/{b["lmem_kernel_kinds"]} |')
base='baseline-final' if 'baseline-final' in variants else 'baseline';new=next(v for v in ['selected','lowreg-fix','optimized','caps'] if v in variants)
for w in [1600,1920]:
 a,b=variants[base][w],variants[new][w];lines+=['',f'## {w}: {base} → {new}','', '| Kernel | Before ms | After ms | Regs | LMem B | SMem B | OccW |','|---|---:|---:|---:|---:|---:|---:|']
 for name,x in a['kernels'].items():
  y=b['kernels'][name];lines.append(f'| {name} | {x["ms"]:.6f} | {y["ms"]:.6f} | '+' | '.join(f'{int(x[k])}→{int(y[k])}' for k in ['regs','lmem','smem','occw'])+' |')
 lines+=['',f'Accuracy `{json.dumps(b["accuracy_vs_baseline"])}`; F32 visible `{json.dumps(b["accuracy_vs_f32_visible"])}`.']
(root/'results.json').write_text(json.dumps(variants,indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:14]))
