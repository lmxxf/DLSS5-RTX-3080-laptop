import numpy as np
from pathlib import Path
base=Path('/mnt/c/DLSS5-5090-dll')
a=np.fromfile(base/'sky_fast.rgb32',np.float32).reshape(720,1280,3)
b=np.fromfile(base/'sky_stock.rgb32',np.float32).reshape(a.shape)
print('fast/stock differing components',np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)),'maxabs',np.max(abs(a-b)))
for name,v in [('fast',a),('stock',b)]:
 rg=(v[:,:,0]-v[:,:,1]).mean(axis=1)
 print(name,'R-G row range',rg.min(),rg.max(),'row sign changes',np.count_nonzero(np.diff(np.sign(rg))),'max row step',abs(np.diff(rg)).max())
# Identity-model control: encode/decode a perfectly neutral HDR ramp.
# Quantize RGB to the normalized mantissas of R11G11B10_FLOAT vs FP16.
y=np.linspace(.65,1.5,65536); orig=np.repeat(y[:,None],3,axis=1)
rolled=np.where(y>.75,.75+.25*(1-np.exp(-(y-.75)/.25)),y)
p=orig*(rolled/y)[:,None]
s=1.055*p**(1/2.4)-.055
for name,bits in [('R11G11B10',[6,6,5]),('FP16',[10,10,10])]:
 e=np.floor(np.log2(s)); step=2.**(e-np.array(bits)); q=np.rint(s/step)*step
 dec=((q+.055)/1.055)**2.4
 err=dec-p
 print(name,'identity roundtrip maxabs',abs(err).max(),'max |R-B|',abs(dec[:,0]-dec[:,2]).max(),'R-G',abs(dec[:,0]-dec[:,1]).max())
