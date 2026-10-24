from pathlib import Path
import subprocess,json
import numpy as np
from PIL import Image
root=Path('/mnt/c/DLSS5-5090-dll');dest=Path(__file__).parent
core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
summary={}
for v in ['strict_nq','multidef_nq']:
 summary[v]={}
 for w,h,scene in [(1280,720,'sky'),(1600,900,'scene'),(1920,1080,'scene')]:
  args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,rf'C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_{v}.dll',str(w),str(h),'2','5','20',rf'C:\DLSS5-5090-dll\{v}_{w}_{h}.rgb32']
  if scene=='sky':args.append('sky')
  log=dest/f'{v}-{w}x{h}.log'
  with log.open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
  text=log.read_text().split('SUMMARY')[-1].strip();print(v,text,flush=True);summary[v][f'{w}x{h}']=text
  if scene=='sky':
   a=np.fromfile(root/f'{v}_{w}_{h}.rgb32',np.float32).reshape(h,w,3)
   d=(a[:,:,0]-a[:,:,1]).mean(1);hf=d[1:-1]-(d[:-2]+d[2:])*.5
   stats={'sign_changes':int(np.count_nonzero(np.diff(np.sign(d)))),'hf_rms':float(np.sqrt(np.mean(hf**2))),'nonfinite':int(np.count_nonzero(~np.isfinite(a)))}
   summary[v]['sky']=stats;print(v,'SKY',stats,flush=True)
   Image.fromarray((np.clip(a,0,1)*255).astype('uint8')).save(dest/f'{v}-output.png')
(dest/'nq-controls-results.json').write_text(json.dumps(summary,indent=2))
