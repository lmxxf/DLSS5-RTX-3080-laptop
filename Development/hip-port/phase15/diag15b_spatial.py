from diag15b_paths import ROOT
from pathlib import Path
import numpy as np,json,hashlib
p=Path(__file__).resolve().parent;root=ROOT;cases=json.loads((p/'diag15b-inputs.json').read_text());rows={}
for c in cases:
 paths=[root/'traces'/c['case']/m/'0.rgb32' for m in ['native','f32']]
 if not all(x.exists() for x in paths):continue
 w,h=c['processing'];vw,vh=c['visible'];n,f=[np.fromfile(x,np.float32).reshape(h,w,3) for x in paths];src=np.fromfile(c['input_file'],np.float32).reshape(h,w,4)[:,:,:3];d=n.astype(float)-f.astype(float);sq=d*d;pix=sq.sum(2);total=sq.sum();visible=sq[:vh,:vw]
 def masks(mask):
  if mask.ndim==2:s=pix;den=total
  else:s=sq;den=total
  return {'area_fraction':float(mask.mean()),'SSE_fraction':float(s[mask].sum()/den),'mean_squared_error':float(s[mask].mean()) if mask.any() else None}
 row={'visible_psnr_peak1':float(-10*np.log10(visible.mean())),'full_psnr_peak1':float(-10*np.log10(sq.mean())),'maxabs':float(abs(d[:vh,:vw]).max()),'channel_MSE':sq[:vh,:vw].mean(axis=(0,1)).tolist(),'channel_SSE_fraction':(sq.sum(axis=(0,1))/total).tolist(),'channel_bias':d[:vh,:vw].mean(axis=(0,1)).tolist(),'absolute_error_quantiles':np.quantile(abs(d[:vh,:vw]),[.5,.9,.99,.999,1]).tolist(),'output_reference_clipped':masks((f<=0)|(f>=1)),'output_reference_near_clip':masks((f<=.01)|(f>=.99))}
 row['either_output_clipped']=masks((f<=0)|(f>=1)|(n<=0)|(n>=1));row['either_output_near_clip']=masks((f<=.01)|(f>=.99)|(n<=.01)|(n>=.99))
 luma=src@np.array([.2126,.7152,.0722]);row['working_input_luma_groups']={f'{a}-{b}':masks((luma>=a)&(luma<b)) for a,b in [(0,.01),(.01,.1),(.1,.5),(.5,.9),(.9,1.00001)]}
 flat=np.sort(pix.reshape(-1))[::-1];row['largest_pixel_error_SSE_fraction']={str(q):float(flat[:max(1,int(q*flat.size))].sum()/total) for q in [.001,.01,.05,.1]}
 yy,xx=np.mgrid[:h,:w];row['window_boundaries']={}
 for q in [8,16,32,64]:
  for origin in [0,4]:
   mask=((xx+origin)%q==0)|((xx+origin)%q==q-1)|((yy+origin)%q==0)|((yy+origin)%q==q-1);b=masks(mask);b['boundary_vs_interior_MSE']=float(pix[mask].mean()/pix[~mask].mean());row['window_boundaries'][f'{q}@{origin}']=b
 row['spatial_regions']={name:masks(mask) for name,mask in [('first64rows',yy<64),('last64rows',yy>=h-64),('first64cols',xx<64),('last64cols',xx>=w-64),('interior', (yy>=64)&(yy<h-64)&(xx>=64)&(xx<w-64))]}
 worst=np.argsort(pix.reshape(-1))[-12:][::-1];row['worst_pixels']=[{'x':int(i%w),'y':int(i//w),'input':src[i//w,i%w].tolist(),'native':n[i//w,i%w].tolist(),'F32':f[i//w,i%w].tolist(),'error':d[i//w,i%w].tolist()} for i in worst]
 row['token64_error_map']=pix.reshape(h//64,64,w//64,64).mean(axis=(1,3)).tolist();rows[c['case']]=row
(p/'diag15b-spatial.json').write_text(json.dumps(rows,indent=2)+'\n');print({k:(x['visible_psnr_peak1'],x['channel_SSE_fraction'],x['largest_pixel_error_SSE_fraction']['0.01']) for k,x in rows.items()})
