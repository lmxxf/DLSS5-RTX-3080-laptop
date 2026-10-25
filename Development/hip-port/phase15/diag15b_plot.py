from diag15b_paths import ROOT
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;root=ROOT;cases=json.loads((p/'diag15b-inputs.json').read_text());fig,ax=plt.subplots(4,3,figsize=(13,13))
for j,c in enumerate(cases):
 w,h=c['processing'];n=np.fromfile(root/'traces'/c['case']/'native/0.rgb32',np.float32).reshape(h,w,3);f=np.fromfile(root/'traces'/c['case']/'f32/0.rgb32',np.float32).reshape(h,w,3);src=np.fromfile(c['input_file'],np.float32).reshape(h,w,4);err=np.sqrt(np.mean((n.astype(float)-f)**2,axis=2));tile=err.reshape(h//64,64,w//64,64).mean(axis=(1,3))
 ax[j,0].imshow(src[:,:,:3]);ax[j,0].set_title(c['case']+' working input');im=ax[j,1].imshow(err,vmin=0,vmax=.02,cmap='magma');ax[j,1].set_title('RGB RMS error (shared0..0.02)');ax[j,2].imshow(tile,vmin=0,vmax=.008,cmap='magma');ax[j,2].set_title('64x64 region mean error (shared0..0.008)')
 for a in ax[j]:a.set_xticks([]);a.set_yticks([])
fig.suptitle('Phase15B: encoded working RGB, no image-wise error rescaling');fig.tight_layout();fig.savefig(root/'spatial.png',dpi=120);plt.close(fig)
