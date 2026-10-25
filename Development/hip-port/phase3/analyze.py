#!/usr/bin/env python3
"""Summarize controlled Phase-3 runs; preserve added/removed kernel families."""
from pathlib import Path
import re,json,argparse
import numpy as np
parser=argparse.ArgumentParser();parser.add_argument('--warmup',type=int,default=50);parser.add_argument('--iterations',type=int,default=80);args=parser.parse_args()
root=Path(__file__).resolve().parent
out=root/'artifacts/outputs'
def read(path):
    cases={}
    for part in path.read_text().split('Running Case: ')[1:]:
        w=1920 if '1080p' in part.splitlines()[0] else 1600
        gpu=re.search(r'GPU  \(ms\): mean=([\d.]+) median=([\d.]+).*?min=([\d.]+)',part)
        wall=re.search(r'Wall \(ms\): mean=([\d.]+) median=([\d.]+)',part)
        rows={}
        for line in part.splitlines():
            c=line.split()
            if len(c)==10 and c[1].isdigit():rows[c[0]]=dict(zip(('calls','ms','us','grid','block','regs','lmem','smem','occw'),map(float,c[1:])))
        cases[w]={'gpu_min':float(gpu[3]),'gpu_median':float(gpu[2]),'wall_median':float(wall[2]),'kernels':rows}
    return cases

def pixels(prefix,w):
    h=1152 if w==1920 else 1024
    return np.fromfile(prefix.parent/(prefix.name+f'-{w}.rgb32'),np.float32).reshape(h,w,3)
def accuracy(x,y):
    d=y.astype(np.float64)-x;mse=float(np.mean(d*d))
    return {'psnr_peak1_db':float(-10*np.log10(mse)) if mse else 999.,'maxabs':float(np.max(np.abs(d))),'invalid':int(np.sum(~np.isfinite(y))),'bitdiff':int(np.count_nonzero(x.view(np.uint32)!=y.view(np.uint32)))}
base=read(root/'phase2-bench.log');new=read(root/'phase3-bench.log');control=read(root/'shared-q-bench.log')
lines=['# Phase 3: deferred unpack, 900p gates, and register-local Q','', f'{args.warmup} warmup / {args.iterations} measured frames. Kernel census is an extra instrumented frame. GPU times exclude initialization/transfers/readback.','', '| Size | Phase 2 min / median ms | Full Phase 3 min / median ms | Shared-Q control min / median ms | Full / control PSNR vs F32 |','|---|---:|---:|---:|---:|']
for w,vh in [(1920,1080),(1600,900)]:
    y=pixels(out/'phase3',w);x=pixels(out/'phase2',w);c=pixels(out/'shared_q',w)
    f=pixels(root.parent/'phase1/artifacts/outputs/f32',w)
    new[w]['accuracy_vs_f32']={name:accuracy(f[:h],y[:h]) for name,h in [('padded',len(f)),('visible',vh)]}
    new[w]['accuracy_vs_phase2']=accuracy(x,y)
    new[w]['local_q_vs_shared_q']=accuracy(c,y)
    assert new[w]['local_q_vs_shared_q']['bitdiff']==0
    a,b,z=base[w],new[w],control[w]
    lines.append(f'| {w}×{vh} | {a["gpu_min"]:.3f} / {a["gpu_median"]:.3f} | {b["gpu_min"]:.3f} / {b["gpu_median"]:.3f} | {z["gpu_min"]:.3f} / {z["gpu_median"]:.3f} | {b["accuracy_vs_f32"]["visible"]["psnr_peak1_db"]:.4f} dB |')
for w,vh in [(1920,1080),(1600,900)]:
    lines+=['',f'## {w}×{vh} (processing {w}×{1152 if w==1920 else 1024})','',f'Accuracy: `{json.dumps(new[w]["accuracy_vs_f32"])}`',f'Q relocation vs shared-Q control: `{json.dumps(new[w]["local_q_vs_shared_q"])}`','', '| Kernel | Calls P2→P3 | P2 ms | P3 ms | Regs | LMem | SMem | OccW |','|---|---:|---:|---:|---:|---:|---:|---:|']
    a,b=base[w]['kernels'],new[w]['kernels']
    for name in list(a)+[n for n in b if n not in a]:
        aa,bb=a.get(name),b.get(name)
        def val(row,k):return '—' if row is None else f'{row[k]:.0f}'
        def pair(k):return val(aa,k)+'→'+val(bb,k)
        lines.append('| '+name+' | '+pair('calls')+' | '+('—' if aa is None else f'{aa["ms"]:.6f}')+' | '+('—' if bb is None else f'{bb["ms"]:.6f}')+' | '+' | '.join(pair(k) for k in ('regs','lmem','smem','occw'))+' |')
    lines+=['',f'Profile totals: {sum(v["ms"] for v in a.values()):.6f} → {sum(v["ms"] for v in b.values()):.6f} ms; {len(a)} → {len(b)} active kernels.']
gates={name:read(root/path) for name,path in [('compact_only','900-compact-only.log'),('compact_c256','900-compact-c256.log')]}
for name in gates:
    gates[name][1600]['accuracy_vs_f32']=accuracy(pixels(root.parent/'phase1/artifacts/outputs/f32',1600)[:900],pixels(out/name,1600)[:900])
assert accuracy(pixels(out/'compact_only',1600),pixels(out/'compact_c256',1600))['bitdiff']==0
(root/'results.json').write_text(json.dumps({'warmup':args.warmup,'iterations':args.iterations,'baseline':base,'candidate':new,'shared_q_control':control,'gate_controls_20warmup_40iterations':gates},indent=2)+'\n')
(root/'results.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:9]))
