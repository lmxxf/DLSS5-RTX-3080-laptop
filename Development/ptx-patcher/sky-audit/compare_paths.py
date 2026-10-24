from pathlib import Path
import numpy as np
from PIL import Image
root=Path('/mnt/c/DLSS5-5090-dll'); out=Path(__file__).parent
for name in ['fast','stock','nomapped','independent']:
 p=root/f'sky_{name}.rgb32'
 if not p.exists():continue
 a=np.fromfile(p,np.float32).reshape(-1,1280,3)[:720]
 d=(a[:,:,0]-a[:,:,1]).mean(1)
 # Remove broad luminance trend to measure the spatial alternating component.
 hf=d[1:-1]-(d[:-2]+d[2:])*.5
 print(name,'R-G min/max',float(d.min()),float(d.max()),'sign changes',np.count_nonzero(np.diff(np.sign(d))), 'highpass RMS',float(np.sqrt(np.mean(hf**2))),'clipped>=1',float(np.mean(a>=1)))
 Image.fromarray((np.clip(a,0,1)*255).astype('uint8')).save(out/f'{name}-output.png')
 if name=='fast':ref=a
 else:print(' vs fast: maxabs',float(abs(a-ref).max()),'RMSE',float(np.sqrt(np.mean((a-ref)**2))))
