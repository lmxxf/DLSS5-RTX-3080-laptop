#!/usr/bin/env python3
from pathlib import Path
import re,json,argparse
import numpy as np
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--warmup',type=int,default=50);p.add_argument('--iterations',type=int,default=80);args=p.parse_args()
def read_log(path):
 cases={}
 for part in path.read_text().split('Running Case: ')[1:]:
  w=1920 if '1080p' in part.splitlines()[0] else 1600
  g=re.search(r'GPU  \(ms\): mean=([\d.]+) median=([\d.]+) p90=([\d.]+).*?min=([\d.]+)',part)
  wall=re.search(r'Wall \(ms\): mean=([\d.]+) median=([\d.]+)',part);rows={}
  for line in part.splitlines():
   c=line.split()
   if len(c)==10 and c[1].isdigit():rows[c[0]]=dict(zip(('calls','ms','us','grid','block','regs','lmem','smem','occw'),map(float,c[1:])))
  cases[w]={'gpu_min':float(g[4]),'gpu_median':float(g[2]),'gpu_p90':float(g[3]),'wall_median':float(wall[2]),'kernels':rows}
 return cases

def load(prefix,w):
 h=1152 if w==1920 else 1024
 return np.fromfile(prefix.parent/(prefix.name+f'-{w}.rgb32'),np.float32).reshape(h,w,3)
def accuracy(a,b):
 d=b.astype(np.float64)-a;mse=float(np.mean(d*d))
 return {'invalid':int(np.count_nonzero(~np.isfinite(b))),'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'psnr_peak1_db':float(-10*np.log10(mse)) if mse else 999.,'maxabs':float(np.max(np.abs(d)))}
if __name__=='__main__':
 variants={}
 for name in ['baseline','vector','vector-bound9','register-q','register-q-uninit','register-q-bound9','register-q-capped','selected']:
  path=root/(name+'-bench.log')
  if not path.exists():continue
  cases=read_log(path)
  for w,c in cases.items():
   y=load(root/'artifacts/outputs'/name,w);base=load(root/'artifacts/outputs/baseline',w);original=load(root.parent/'phase1/artifacts/outputs/f32',w);vh=1080 if w==1920 else 900
   c['accuracy_vs_baseline']=accuracy(base,y)
   c['accuracy_vs_f32']={'visible':accuracy(original[:vh],y[:vh]),'padded':accuracy(original,y)}
   assert c['accuracy_vs_baseline']['bitdiff']==0, name
   assert name!='selected' or all(r['lmem']==0 for r in c['kernels'].values()), name
  variants[name]=cases
 base,new=variants['baseline'],variants['selected']
 lines=['# Phase 5: packed C/D Benes and register-Q controls','',f'Final comparisons: {args.warmup} warmup / {args.iterations} iterations; GPU events exclude initialization/transfers/readback. Separate instrumented frame for the kernel census.','', '| Resolution | Baseline min / median ms | Selected min / median ms | Speedup | PSNR vs F32 | Maxabs |','|---|---:|---:|---:|---:|---:|']
 for w,vh in [(1920,1080),(1600,900)]:
  a,b=base[w],new[w];m=b['accuracy_vs_f32']['visible'];lines.append(f'| {w}×{vh} | {a["gpu_min"]:.3f} / {a["gpu_median"]:.3f} | {b["gpu_min"]:.3f} / {b["gpu_median"]:.3f} | {a["gpu_median"]/b["gpu_median"]:.4f}× | {m["psnr_peak1_db"]:.4f} dB | {m["maxabs"]:.8f} |')
 lines+=['','## Stage summary','', 'baseline/vector/vector-bound9/register-q-capped are final 50/80 runs; other Q variants are 10/40 pilots. Selected aliases the chosen run, not an independent repetition.','', '| Stage | 900p median ms | 1080p median ms |','|---|---:|---:|']
 for name,c in variants.items():lines.append(f'| {name} | {c[1600]["gpu_median"]:.3f} | {c[1920]["gpu_median"]:.3f} |')
 for w,vh in [(1920,1080),(1600,900)]:
  a,b=base[w]['kernels'],new[w]['kernels'];lines+=['',f'## {w}×{vh} (processing {w}×{1152 if w==1920 else 1024})','',f'Bitdiff vs chosen Phase-3 baseline: {new[w]["accuracy_vs_baseline"]["bitdiff"]}; invalid=0; F32 metrics: `{json.dumps(new[w]["accuracy_vs_f32"])}`','', '| Kernel | Calls before→after | Before ms | After ms | Regs | LMem | SMem | OccW |','|---|---:|---:|---:|---:|---:|---:|---:|']
  for name in list(a)+[n for n in b if n not in a]:
   x,y=a.get(name),b.get(name)
   def val(row,k):return '—' if row is None else f'{row[k]:.0f}'
   def pair(k):return val(x,k)+'→'+val(y,k)
   lines.append('| '+name+' | '+pair('calls')+' | '+('—' if x is None else f'{x["ms"]:.6f}')+' | '+('—' if y is None else f'{y["ms"]:.6f}')+' | '+' | '.join(pair(k) for k in ('regs','lmem','smem','occw'))+' |')
  lines+=['',f'Instrumented kernel total: {sum(v["ms"] for v in a.values()):.6f} → {sum(v["ms"] for v in b.values()):.6f} ms; active kernel kinds {len(a)}→{len(b)}.']
 (root/'results.json').write_text(json.dumps({'warmup':args.warmup,'iterations':args.iterations,'variants':variants},indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:9]))
