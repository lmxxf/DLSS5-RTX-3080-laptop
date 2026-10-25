#!/usr/bin/env python3
"""Compare the deterministic Small-model benchmark dumps and kernel census."""
import argparse
import json
import re
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('baseline',type=Path,help='dump prefix (also PREFIX-bench.log)')
p.add_argument('candidate',type=Path)
p.add_argument('output',type=Path)
p.add_argument('--f32',type=Path,default=Path(__file__).resolve().parents[1]/'phase1/artifacts/outputs/f32')
a=p.parse_args()
def read(prefix):
    text=Path(str(prefix)+'-bench.log').read_text()
    results={}
    for part in text.split('Running Case: ')[1:]:
        w=1920 if '1080p' in part.splitlines()[0] else 1600
        gpu=re.search(r'GPU  \(ms\): mean=([\d.]+) median=([\d.]+).*?min=([\d.]+)',part)
        rows={}
        for line in part.splitlines():
            cols=line.split()
            if len(cols)==10 and cols[0] not in ('Kernel',) and cols[1].isdigit():
                rows[cols[0]]=dict(zip(('calls','ms','us','grid','block','regs','lmem','smem','occw'),map(float,cols[1:])))
        results[w]={'gpu_median':float(gpu[2]),'gpu_min':float(gpu[3]),'kernels':rows}
    return results
base,new=read(a.baseline),read(a.candidate)
report=['# Phase 2: static weights / exact ones / packed partition sums','', 'GPU timings exclude initialization/readback; kernel census is a separate instrumented frame.','']
for w,h,validh in [(1920,1152,1080),(1600,1024,900)]:
    x=np.fromfile(str(a.baseline)+f'-{w}.rgb32',dtype=np.float32).reshape(h,w,3)
    y=np.fromfile(str(a.candidate)+f'-{w}.rgb32',dtype=np.float32).reshape(h,w,3)
    metrics={}
    for name,xx,yy in [('padded',x,y),('visible',x[:validh],y[:validh])]:
        delta=yy.astype(np.float64)-xx
        mse=float(np.mean(delta**2))
        metrics[name]={'invalid':int(np.count_nonzero(~np.isfinite(yy))),'psnr_peak1_db':float(-10*np.log10(mse)) if mse else 999.,'maxabs':float(np.max(np.abs(delta))),'rmse':float(np.sqrt(mse))}
    new[w]['accuracy_vs_phase1']=metrics
    original=np.fromfile(str(a.f32)+f'-{w}.rgb32',dtype=np.float32).reshape(h,w,3)
    f32metrics={}
    for name,xx,yy in [('padded',original,y),('visible',original[:validh],y[:validh])]:
        delta=yy.astype(np.float64)-xx;mse=float(np.mean(delta**2))
        f32metrics[name]={'invalid':int(np.count_nonzero(~np.isfinite(yy))),'psnr_peak1_db':float(-10*np.log10(mse)) if mse else 999.,'maxabs':float(np.max(np.abs(delta))),'rmse':float(np.sqrt(mse))}
    new[w]['accuracy_vs_f32']=f32metrics
    report += [f'## {w}x{validh} (processing {w}x{h})','',f'Phase 1 median/min {base[w]["gpu_median"]}/{base[w]["gpu_min"]} ms; Phase 2 {new[w]["gpu_median"]}/{new[w]["gpu_min"]} ms; speedup {base[w]["gpu_median"]/new[w]["gpu_median"]:.3f}x.', '',f'Accuracy vs Phase 1: `{json.dumps(metrics)}`', '',f'Accuracy vs F32: `{json.dumps(f32metrics)}`','', '| Kernel | Calls | Phase 1 ms | Phase 2 ms | Regs P1→P2 | LMem P1→P2 | OccW P1→P2 |','|---|---:|---:|---:|---:|---:|---:|']
    for name,row in base[w]['kernels'].items():
        other=new[w]['kernels'][name]
        report.append(f'| {name} | {row["calls"]:.0f} | {row["ms"]:.4f} | {other["ms"]:.4f} | {row["regs"]:.0f}→{other["regs"]:.0f} | {row["lmem"]:.0f}→{other["lmem"]:.0f} | {row["occw"]:.0f}→{other["occw"]:.0f} |')
    report+=['']
a.output.mkdir(parents=True,exist_ok=True)
(a.output/'results.json').write_text(json.dumps({'baseline':base,'candidate':new},indent=2)+'\n')
(a.output/'results.md').write_text('\n'.join(report)+'\n')
print('\n'.join(report[:10]))
