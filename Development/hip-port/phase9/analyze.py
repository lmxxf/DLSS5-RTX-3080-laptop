from pathlib import Path
import re,json,numpy as np
root=Path(__file__).resolve().parent
source=(root.parent/'phase6/analyze.py').read_text();ns={};exec(source[source.index('def read_log'):source.index("if __name__=='__main__':")],{'re':re,'np':np},ns)
read_log,load,accuracy=[ns[k] for k in ('read_log','load','accuracy')]
variants={}
names=['baseline','graph-only','v-bridge','v-graph','q63-lowreg','q63-graph','q63-peel','q63-peel-graph','q63-fast','q63-fast-graph','q31-lowreg','q31-graph','q63-policy','q63-policy-graph','baseline-final','selected','selected-graph']
for name in names:
 p=root/(name+'-bench.log')
 if not p.exists():continue
 text=p.read_text();cases=read_log(p)
 for w,c in cases.items():
  y=load(root/'artifacts/outputs'/name,w);base=load(root/'artifacts/outputs/baseline',w)
  c['accuracy_vs_baseline']=accuracy(base,y);c['accuracy_vs_phase8']=accuracy(load(root.parent/'phase8/artifacts/outputs/selected',w),y)
  vh=900 if w==1600 else 1080;c['accuracy_vs_f32_visible']=accuracy(load(root.parent/'phase1/artifacts/outputs/f32',w)[:vh],y[:vh])
  assert c['accuracy_vs_baseline']['bitdiff']==c['accuracy_vs_baseline']['invalid']==c['accuracy_vs_phase8']['bitdiff']==0
  part=next(part for part in text.split('Running Case: ')[1:] if str(w)+'x' in part.splitlines()[0])
  valid=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',part)
  assert valid and valid[1]==valid[2]=='0'
  c['first_last_bitdiff']=int(valid[2])
  mutable=re.search(r'GRAPH_MUTABLE_INPUT raw_bitdiff=(\d+) changed_values=(\d+) restored_bitdiff=(\d+)',part)
  c['mutable_input']=dict(zip(['raw_bitdiff','changed_values','restored_bitdiff'],map(int,mutable.groups()))) if mutable else None
  if mutable:assert mutable[1]==mutable[3]=='0' and int(mutable[2])>0
  if name=='selected-graph':assert mutable
  g=re.search(r'GRAPH_STATUS enabled=(\d+) builds=(\d+) replays=(\d+) small=(\d+) wave_owned=(\d+) final_direct=(\d+)',part)
  c['graph']=dict(zip(['enabled','builds','replays','small','wave_owned','final_direct'],map(int,g.groups()))) if g else None
  if name=='selected':assert all(k['lmem']==0 for k in c['kernels'].values()) and all(k['smem']==8192 and k['occw']==11 for n,k in c['kernels'].items() if n.startswith('c32_wave1_') and 'up' not in n)
  if c['graph'] and c['graph']['enabled']:assert c['graph']['small']==c['graph']['wave_owned']==c['graph']['final_direct']==1 and c['graph']['replays']>=130
  c['kernel_total']=sum(k['ms'] for k in c['kernels'].values()) if c['kernels'] else None
  c['launches']=sum(int(k['calls']) for k in c['kernels'].values()) if c['kernels'] else None
 variants[name]=cases
lines=['# Phase 9: Graph, V bridge, register-Q','', '50 warmup / 80 iter; padded processing 1600×1024 / 1920×1152. PROFILE_TOTAL is a separate instrumented frame, not the GPU median frame. Graph runs skip instrumentation; compare their GPU/Wall distributions directly.','', '| Variant | 900p GPU min / median | 900p Wall median | 1080p GPU min / median | 1080p Wall median | LMem kernels 900/1080 |','|---|---:|---:|---:|---:|---:|']
for name,c in variants.items():
 a,b=c[1600],c[1920]
 local='/'.join(str(sum(k['lmem']>0 for k in c[w]['kernels'].values())) if c[w]['kernels'] else 'not profiled' for w in (1600,1920))
 lines.append(f'| {name} | {a["gpu_min"]:.3f} / {a["gpu_median"]:.3f} | {a["wall_median"]:.3f} | {b["gpu_min"]:.3f} / {b["gpu_median"]:.3f} | {b["wall_median"]:.3f} | {local} |')
new=next((v for v in ['selected','q63-policy','q31-lowreg','q63-fast','q63-peel','q63-lowreg','v-bridge'] if v in variants),None)
if new:
 for w in (1600,1920):
  a,b=variants['baseline-final' if 'baseline-final' in variants else 'baseline'][w],variants[new][w]
  lines+=['',f'## {w}: '+('baseline-final' if 'baseline-final' in variants else 'baseline')+f' → {new} (Graph off)','', '| Kernel | Before ms | After ms | Regs | LMem B | SMem B | OccW |','|---|---:|---:|---:|---:|---:|---:|']
  for name,x in a['kernels'].items():
   y=b['kernels'][name];pairs=[f'{int(x[k])}→{int(y[k])}' for k in ['regs','lmem','smem','occw']]
   lines.append(f'| {name} | {x["ms"]:.6f} | {y["ms"]:.6f} | '+' | '.join(pairs)+' |')
  for name,c in variants.items():lines.append(f'\n{name}: kernel total `{c[w]["kernel_total"]}` ms, launches `{c[w]["launches"]}`, graph `{json.dumps(c[w]["graph"])}`, baseline bitdiff/invalid `{json.dumps(c[w]["accuracy_vs_baseline"])}`.')
(root/'results.json').write_text(json.dumps(variants,indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:18]))
