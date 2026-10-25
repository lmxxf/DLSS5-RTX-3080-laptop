from pathlib import Path
import numpy as np,json,re,csv,datetime
p=Path(__file__).resolve().parent;r=p.parent;dims={1280:(768,720),1600:(1024,900),1920:(1152,1080)}
tele=[]
for f in p.glob('telemetry*.csv'):tele+=list(csv.reader(f.open()))
def metrics(a,b):
 delta=a.astype(float)-b.astype(float);mse=float(np.mean(delta*delta))
 return {'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'maxabs':float(np.max(abs(delta))),'psnr_peak1':float(-10*np.log10(mse)) if mse else 999.,'invalid':int(np.count_nonzero(~np.isfinite(b)))}
def image(path,w):return np.fromfile(path,np.float32).reshape(dims[w][0],w,3)
rows={}
for f in sorted(p.glob('*-run.json')):
 m=json.loads(f.read_text())
 if m['warmup']!=50 or m['iterations']!=80 or m['f32']:continue
 v=m['variant'];w=m['width'];s=(p/f'{v}-{w}.log').read_text();assert m['returncode']==0
 g=re.search(r'GPU  \(ms\):.*?median=([\d.]+).*?min=([\d.]+)',s);wall=re.search(r'Wall \(ms\):.*?median=([\d.]+)',s);val=re.search(r'Validity : invalid=(\d+).*?bit_diff_first_last=(\d+)',s)
 kernels={}
 for line in s.splitlines():
  a=line.split()
  if len(a)==10 and a[1].isdigit():kernels[a[0]]=dict(zip(['calls','ms','us','grid','block','regs','lmem','smem','occw'],map(float,a[1:])))
 assert len(kernels)==32 and all(a['lmem']==0 for a in kernels.values()),v
 assert int(val[1])==int(val[2])==0
 a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);samples=[x for x in tele if len(x)==6 and a<=datetime.datetime.strptime(x[0],'%Y/%m/%d %H:%M:%S.%f')<=b and float(x[5])>=95]
 data={'cap_request':m['cap'],'gpu_min':float(g[2]),'gpu_median':float(g[1]),'wall_median':float(wall[1]),'profile_total':float(re.search(r'PROFILE_TOTAL ([\d.]+)',s)[1]),'kernels':kernels,'invalid':0,'first_last_bitdiff':0,'telemetry':{'util95_samples':len(samples),**{k:float(np.median([float(x[i]) for x in samples])) if samples else None for k,i in [('sm_mhz',1),('mem_mhz',2),('power_w',3),('temp_c',4)]}}}
 out=image(p/f'artifacts/outputs/{v}-{w}.rgb32',w);expected=image(p/f'artifacts/outputs/fixed-quick-{w}.rgb32',w);data['vs_corrected_output']=metrics(expected,out);assert data['vs_corrected_output']['bitdiff']==0
 old=image(r/f'phase12/artifacts/outputs/selected-{w}.rgb32',w);data['vs_phase12_old']=metrics(old,out)
 if w!=1280:assert data['vs_phase12_old']['bitdiff']==0
 else:assert data['vs_phase12_old']['bitdiff']==2947224
 gold=image(p/'artifacts/gold/f32-720p-1280x768.rgb32' if w==1280 else r/f'phase1/artifacts/outputs/f32-{w}.rgb32',w)
 data['visible_vs_trusted_F32']=metrics(gold[:dims[w][1]],out[:dims[w][1]])
 attention=[k for k in kernels if k.startswith('vit_attention_fused_')];assert len(attention)==1;data['attention_entry']=attention[0]
 if w==1280:assert attention[0].startswith(f'vit_attention_fused_{m["cap"]}_')
 rows.setdefault(v,{})[w]=data
lines=['# Phase14 formal controls','','Small31/Style1, Graph off, defaultDVFS140W cap,50warmup/80iter. PROFILE_TOTAL is a separate instrumented frame. Both720 paths are corrected; wrong Phase12720 output is not used for quality.','', '| Variant | Width | GPU min / median | Wall med | PROFILE_TOTAL | Attention entry | SM MHz med | Power W med | Temp C med |','|---|---:|---:|---:|---:|---|---:|---:|---:|']
for v,cases in rows.items():
 for w,x in cases.items():
  t=x['telemetry'];lines.append(f'| {v} | {w} | {x["gpu_min"]:.3f} / {x["gpu_median"]:.3f} | {x["wall_median"]:.3f} | {x["profile_total"]:.6f} | {x["attention_entry"]} | {t["sm_mhz"]} | {t["power_w"]} | {t["temp_c"]} |')
for w in [1280,1600,1920]:
 if w not in rows.get('default400',{}):continue
 x=rows['default400'][w];lines+=['',f'## Final default400 {w} kernel profile','', '| Kernel | Calls | Total ms | Regs | LOCAL B | Shared B | OccW |','|---|---:|---:|---:|---:|---:|---:|']
 for n,a in x['kernels'].items():lines.append(f'| {n} | {int(a["calls"])} | {a["ms"]:.6f} | {int(a["regs"])} | {int(a["lmem"])} | {int(a["smem"])} | {int(a["occw"])} |')
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:24]))
