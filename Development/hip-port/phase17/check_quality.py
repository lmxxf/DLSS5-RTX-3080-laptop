from pathlib import Path
import re,json,numpy as np,hashlib
p=Path(__file__).resolve().parent;r=p.parent;rows={}
for f in sorted(p.glob('*-run.json')):
 m=json.loads(f.read_text());v=m['variant'];w=m['width'];s=(p/f'{v}-{w}.log').read_text();kernels={}
 for line in s.splitlines():
  a=line.split()
  if len(a)==10 and a[1].isdigit():kernels[a[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,a[1:])))
 a=np.fromfile(p/f'artifacts/outputs/{v}-{w}.rgb32',np.uint32);b=np.fromfile(r/f'phase16/artifacts/outputs/final-quick-{w}.rgb32',np.uint32);assert len(a)==len(b) and np.array_equal(a,b),(v,w)
 assert len(kernels)==32 and all(x['lmem']==0 for x in kernels.values()),(v,w,'spill')
 val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);assert val[1]==val[2]=='0'
 c32={n:x for n,x in kernels.items() if n.startswith('c32_wave1_')};assert len(c32)==6
 for n,x in c32.items():
  assert x['smem']==(10240 if '_up_' in n else 8192),(n,x)
  assert x['occw']==(9 if '_up_' in n else 11),(n,x)
 g=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s)
 rows.setdefault(v,{})[w]={'gpu_min':float(g[2]),'gpu_median':float(g[1]),'wall_median':float(wall[1]),'profile_total':float(re.search(r'PROFILE_TOTAL ([\d.]+)',s)[1]),'bitdiff':0,'invalid':0,'first_last':0,'kernels':kernels,'output_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'warmup':m['warmup'],'iterations':m['iterations']}
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');lines=['# Phase17 paired controls','','Small31/Style1,Graph off,defaultDVFS;50warmup/80iter for ABBA. PROFILE_TOTAL is an independent instrumented frame.','', '| Run | Width | GPU min /median ms | Wall median | PROFILE_TOTAL |','|---|---:|---:|---:|---:|']
for v,cases in rows.items():
 for w,x in cases.items():lines.append(f'| {v} | {w} | {x["gpu_min"]:.3f} /{x["gpu_median"]:.3f} | {x["wall_median"]:.3f} | {x["profile_total"]:.6f} |')
for w in [1280,1600,1920]:
 lines+=['',f'## {w} C32 profiles','','| Run | Kernel | Total ms | Regs | LMem | Shared | OccW |','|---|---|---:|---:|---:|---:|---:|']
 for v,cases in rows.items():
  if w not in cases:continue
  for n,x in cases[w]['kernels'].items():
   if n.startswith('c32_wave1_'):lines.append(f'| {v} | {n} | {x["ms"]:.6f} | {int(x["regs"])} | {int(x["lmem"])} | {int(x["smem"])} | {int(x["occw"])} |')
(p/'results.md').write_text('\n'.join(lines)+'\n');print('PASS:all runs Phase16/14 exact outputs,invalid0,32/32 LMem0,C32 8KB/nonUp preserved')
