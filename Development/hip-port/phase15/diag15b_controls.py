from diag15b_paths import ROOT
from pathlib import Path
import json,numpy as np,hashlib,os,subprocess
p=Path(__file__).resolve().parent;root=ROOT;base=next(x for x in json.loads((p/'diag15b-inputs.json').read_text()) if x['case']=='ramp1024');a=np.fromfile(base['input_file'],np.float32).reshape(1024,1024,4);rows=[]
for shift in [1,8]:
 idx=abs(np.arange(1024)-shift);b=a[:,idx].copy();file=root/'inputs'/f'ramp1024-shift{shift}.rgba32';b.tofile(file);outcomes={}
 for mode in ['native','f32']:
  out=root/'controls'/f'shift{shift}'/mode;out.mkdir(parents=True,exist_ok=True);assert not (out/'0.rgb32').exists()
  env={k:v for k,v in os.environ.items() if not k.startswith(('DLSS5_','NR_'))};env.update(DLSS5_AMPERE_WEIGHTS='1' if mode=='native' else '0',DLSS5_LAB_COMPACT_ALL='1' if mode=='native' else '0',DLSS5_LAB_C256_SPLIT='1' if mode=='f32' else '0')
  mods=p/'artifacts/selected/modules' if mode=='native' else root/'reference';log=p/f'diag15b-shift{shift}-{mode}.log'
  with log.open('w') as f:ret=subprocess.run([str(p/'artifacts/host/frame_runner'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(mods),'1024','1024',str(out),str(file)],env=env,stdout=f,stderr=subprocess.STDOUT)
  assert ret.returncode==0;outcomes[mode]=np.fromfile(out/'0.rgb32',np.float32).reshape(1024,1024,3)
 delta=outcomes['native'].astype(float)-outcomes['f32'].astype(float);rows.append({'shift_pixels':shift,'tokens':256,'input_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'PSNR_peak1':float(-10*np.log10(np.mean(delta*delta))),'maxabs':float(np.max(abs(delta))),'scope':'whole-image reflected horizontal translation, sameN256; no equivariance/gold claim'})
(p/'diag15b-controls.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
