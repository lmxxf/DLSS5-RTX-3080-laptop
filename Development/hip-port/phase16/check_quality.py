from pathlib import Path
import re,json,hashlib,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;rows={}
for f in p.glob('*-run.json'):
 m=json.loads(f.read_text());v=m['variant'];w=m['width'];s=(p/f'{v}-{w}.log').read_text();kernels={}
 for line in s.splitlines():
  a=line.split()
  if len(a)==10 and a[1].isdigit():kernels[a[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,a[1:])))
 if v in ['quick','corrected-quick']:continue
 a=np.fromfile(r/f'phase14/artifacts/outputs/default400-{w}.rgb32',np.uint32);b=np.fromfile(p/f'artifacts/outputs/{v}-{w}.rgb32',np.uint32)
 bitdiff=int(np.count_nonzero(a!=b));assert bitdiff==0,(v,w,bitdiff)
 assert len(kernels)==32 and all(x['lmem']==0 for x in kernels.values()),(v,w)
 val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);assert val[1]==val[2]=='0'
 g=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s)
 rows.setdefault(v,{})[w]={'gpu_min':float(g[2]),'gpu_median':float(g[1]),'wall_median':float(wall[1]),'profile_total':float(re.search(r'PROFILE_TOTAL ([\d.]+)',s)[1]),'bitdiff':bitdiff,'invalid':0,'first_last':0,'kernels':kernels,'output_sha256':hashlib.sha256(b.tobytes()).hexdigest()}
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
lines=['# Phase16 formal results','','Small31 Style1, Graph off; 50 warmup / 80 iterations. ABBA per tier, default DVFS. PROFILE_TOTAL is an independent instrumented frame.','', '| Run | Width | GPU min / median ms | Wall median | PROFILE_TOTAL |','|---|---:|---:|---:|---:|']
for v,cases in rows.items():
 for w,x in cases.items():
  if not ('abba' in v):continue
  lines.append(f'| {v} | {w} | {x["gpu_min"]:.3f} / {x["gpu_median"]:.3f} | {x["wall_median"]:.3f} | {x["profile_total"]:.6f} |')
for w in [1280,1600,1920]:
 lines+=['',f'## {w} kernel profiles','','| Run | Kernel | ms | Regs | LOCAL | Shared | OccW |','|---|---|---:|---:|---:|---:|---:|']
 for v,cases in rows.items():
  if 'abba' not in v or w not in cases:continue
  for n,x in cases[w]['kernels'].items():lines.append(f'| {v} | {n} | {x["ms"]:.6f} | {int(x["regs"])} | {int(x["lmem"])} | {int(x["smem"])} | {int(x["occw"])} |')
(p/'results.md').write_text('\n'.join(lines)+'\n');print('PASS all accepted runs: Phase14 0bit, invalid0, first-last0,32/32 LOCAL0')
