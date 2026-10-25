from pathlib import Path
import json,re,numpy as np,datetime,csv
root=Path(__file__).resolve().parent
DIM={1280:(768,720),1600:(1024,900),1920:(1152,1080)}
def image(prefix,w):return np.fromfile(root/'artifacts/outputs'/f'{prefix}-{w}.rgb32',np.float32).reshape(DIM[w][0],w,3)
def accuracy(a,b):
 d=a.astype(np.float64)-b.astype(np.float64);mse=float(np.mean(d*d));return {'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'invalid':int(np.count_nonzero(~np.isfinite(b))),'maxabs':float(np.max(np.abs(d))),'psnr_peak1':float(-10*np.log10(mse)) if mse else 999.}
tele=[]
for tf in sorted(root.glob('telemetry*.csv')):tele.extend(csv.reader(tf.open()))
data={}
for p in sorted(root.glob('*-run.json')):
 run=json.loads(p.read_text());v=run['variant'];w=run['processing_width'];log=root/(v+f'-{w}.log')
 if not log.exists() or run['returncode']:continue
 s=log.read_text();gpu=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s);val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s);rows={}
 for line in s.splitlines():
  c=line.split()
  if len(c)==10 and c[1].isdigit():rows[c[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,c[1:])))
 a,b=[datetime.datetime.fromisoformat(run[k]) for k in ['begin','end']]
 sample=[x for x in tele if len(x)==6 and a<=datetime.datetime.strptime(x[0],'%Y/%m/%d %H:%M:%S.%f')<=b and float(x[5])>=95]
 c={'gpu_min':float(gpu[2]),'gpu_median':float(gpu[1]),'wall_median':float(wall[1]),'kernel_total':sum(x['ms'] for x in rows.values()),'kernels':rows,'invalid':int(val[1]),'first_last_bitdiff':int(val[2]),'telemetry':{'samples_util95':len(sample),**{k:float(np.median([float(x[i]) for x in sample])) if sample else None for k,i in [('sm_mhz',1),('mem_mhz',2),('power_w',3),('temp_c',4)]}}}
 ref='baseline-a'
 if not (root/'artifacts/outputs'/f'{ref}-{w}.rgb32').exists():ref=next(x.name[:-len(f'-{w}-run.json')] for x in root.glob(f'baseline*-{w}-run.json') if (root/'artifacts/outputs'/f'{x.name[:-len(f"-{w}-run.json")]}-{w}.rgb32').exists())
 c['vs_phase10']=accuracy(image(ref,w),image(v,w));assert c['vs_phase10']['bitdiff']==c['vs_phase10']['invalid']==c['first_last_bitdiff']==0
 gold=root.parent/'phase1/artifacts/outputs'/f'f32-{w}.rgb32'
 if w==1280:gold=root/'artifacts/outputs/f32-1280.rgb32'
 if gold.exists():
  a32=np.fromfile(gold,np.float32).reshape(DIM[w][0],w,3);c['f32_visible']=accuracy(a32[:DIM[w][1]],image(v,w)[:DIM[w][1]])
 if w==1280:c['f32_reference_status']='No accepted matching 720p absolute F32 gold; bit equality to Phase10 guarantees unchanged PSNR against any common fixed reference.'
 data.setdefault(v,{})[w]=c
lines=['# Phase11 controls','', '50 warmup/80 iterations, Graph off; separate instrumented frame. Default DVFS, not clock locked.','', '| Variant | Width | GPU min /median | Wall median | Kernel total | LMem kinds | SM MHz med | Power W med |','|---|---:|---:|---:|---:|---:|---:|---:|']
for v,cases in data.items():
 for w,c in cases.items():lines.append(f'| {v} | {w} | {c["gpu_min"]:.3f} /{c["gpu_median"]:.3f} | {c["wall_median"]:.3f} | {c["kernel_total"]:.6f} | {sum(x["lmem"]>0 for x in c["kernels"].values())} | {c["telemetry"]["sm_mhz"]} | {c["telemetry"]["power_w"]} |')
if 'selected' in data and 'baseline-final' in data:
 for w in [1280,1600,1920]:
  a,b=data['baseline-final'][w],data['selected'][w]
  lines+=['',f'## {w}: Phase10 baseline-final → Phase11 selected','', '| Kernel | Baseline ms | Selected ms | Regs | LMem B | SMem B | OccW |','|---|---:|---:|---:|---:|---:|---:|']
  for name,x in a['kernels'].items():
   y=b['kernels'][name];lines.append(f'| {name} | {x["ms"]:.6f} | {y["ms"]:.6f} | '+' | '.join(f'{int(x[k])}→{int(y[k])}' for k in ['regs','lmem','smem','occw'])+' |')
  lines+=['',f'Baseline vs selected output: `{json.dumps(b["vs_phase10"])}`. Trusted F32 visible: `{json.dumps(b.get("f32_visible"))}`.']
(root/'results.json').write_text(json.dumps(data,indent=2)+'\n');(root/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
