from pathlib import Path
import subprocess,numpy as np
from PIL import Image
root=Path('/mnt/c/DLSS5-5090-dll');dest=Path(__file__).parent
core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
for w,h,scene in [(1280,720,'sky'),(1600,900,'scene'),(1920,1080,'scene')]:
 for variant in ['fast','safe']:
  out=rf'C:\DLSS5-5090-dll\{variant}_{w}_{h}.rgb32'
  args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,rf'C:\DLSS5-5090-dll\nvngx_dlssnr_sm86_{variant}.dll',str(w),str(h),'2','5','20',out]
  if scene=='sky':args.append('sky')
  log=dest/f'{variant}-{w}x{h}.log'
  with log.open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
  print(log.name,log.read_text().split('SUMMARY')[-1].strip(),flush=True)
a=np.fromfile(root/'safe_1280_720.rgb32',np.float32).reshape(720,1280,3)
n=np.fromfile(root/'sky_nomapped.rgb32',np.float32).reshape(a.shape)
d=(a[:,:,0]-a[:,:,1]).mean(1);hf=d[1:-1]-(d[:-2]+d[2:])*.5
print('safe sky sign changes',np.count_nonzero(np.diff(np.sign(d))),'HF RMS',np.sqrt(np.mean(hf**2)),'vs nomapped maxabs',abs(a-n).max(),'RMSE',np.sqrt(np.mean((a-n)**2)),flush=True)
Image.fromarray((np.clip(a,0,1)*255).astype('uint8')).save(dest/'safe-output.png')
