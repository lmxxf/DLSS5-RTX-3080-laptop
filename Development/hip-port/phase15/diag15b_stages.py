from diag15b_paths import ROOT
from pathlib import Path
import numpy as np,json,hashlib
p=Path(__file__).resolve().parent;root=ROOT
formats={'pre-down':'fp8','block0':'fp8','block4':'fp8','block4-down':'fp8','block5':'fp8','block8':'half','block9':'fp8','block14':'half','block15':'fp8','block22':'float','block23':'fp8','block30':'float','head':'auto',**{f'block{x}':'auto' for x in range(31,39)},'block39':'fp8','block40':'fp8','block47':'fp8','block48':'fp8','block55':'fp8','block56':'fp8','block61':'fp8','block62':'fp8','block65':'float','block69':'fp8','block70':'float'}
def decode(path,fmt,n):
 raw=path.read_bytes()
 if fmt=='auto':fmt='fp8' if len(raw)==n*1024 else 'float'
 if fmt=='fp8':
  u=np.frombuffer(raw,np.uint8);a=u&127;v=np.where(u&128,-1.,1.)*np.where(a<8,a.astype(float)/512,(1.+(a&7).astype(float)/8)*np.exp2((a>>3).astype(float)-7))
 else:v=np.frombuffer(raw,np.float16 if fmt=='half' else np.float32).astype(float)
 return v,fmt
rows={};lines=['# Phase15B actual-input stage diagnosis','','Taps armed AFTER zero preparation. Prefix consumed-input SHA equals the frozen fixture. No observer/dump_dir graph changes; frozen final outputs remain0bit. Latent NRMSE is not image PSNR.','', '| Case | Stage | Types N/F32 | NRMSE | RMSE | Maxabs | Native /F32 RMS |','|---|---|---|---:|---:|---:|---|']
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 name=case['case'];w,h=case['processing'];n=(w//64)*(h//64);rr={}
 for stage,fmt in formats.items():
  f=root/'traces'/name/'native'/(stage+'.bin');g=root/'traces'/name/'f32'/(stage+'.bin')
  if not f.exists() or not g.exists():continue
  a,fa=decode(f,fmt,n);b,fb=decode(g,fmt,n);assert a.shape==b.shape,(name,stage,a.shape,b.shape);d=a-b;rms=float(np.sqrt(np.mean(d*d)));brms=float(np.sqrt(np.mean(b*b)))
  v={'types':[fa,fb],'elements':a.size,'NRMSE':rms/max(brms,1e-30),'RMSE':rms,'maxabs':float(np.max(abs(d))),'native_RMS':float(np.sqrt(np.mean(a*a))),'F32_RMS':brms,'native_maxabs':float(np.max(abs(a))),'F32_maxabs':float(np.max(abs(b))),'invalid':int(np.count_nonzero(~np.isfinite(a))+np.count_nonzero(~np.isfinite(b))),'sha256':[hashlib.sha256(f.read_bytes()).hexdigest(),hashlib.sha256(g.read_bytes()).hexdigest()]};rr[stage]=v
  lines.append(f'| {name} | {stage} | {fa}/{fb} | {v["NRMSE"]:.6f} | {rms:.6g} | {v["maxabs"]:.6g} | {v["native_RMS"]:.6g}/{brms:.6g} |')
 for category,cols in [('expand',4096),('contract',1024),('qkv',3072),('attention',1024)]:
  for i in range(8):
   f=root/'traces'/name/'native'/f'{category}-{i}-out.bin';g=root/'traces'/name/'f32'/f'{category}-{i}-out.bin'
   if not f.exists() or not g.exists():continue
   a,fa=decode(f,'fp8',n);b,fb=decode(g,'fp8',n);d=a-b;rms=float(np.sqrt(np.mean(d*d)));brms=float(np.sqrt(np.mean(b*b)));rr[f'vit{31+i}-{category}']={'RMSE':rms,'NRMSE':rms/max(brms,1e-30),'maxabs':float(np.max(abs(d))),'native_RMS':float(np.sqrt(np.mean(a*a))),'F32_RMS':brms}
 rows[name]=rr
(p/'diag15b-stages.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'diag15b-stages.md').write_text('\n'.join(lines)+'\n')
for name,rr in rows.items():print(name,[(k,round(v['NRMSE'],4)) for k,v in rr.items() if k in ['pre-down','block4','block8','block14','block22','head','block31','block38','block39','block65','block69','block70']])
