from pathlib import Path
import ctypes as C,numpy as np,json
from cuda_probe import CUDA
r=Path(__file__).resolve().parents[1];p=r/'phase13';d=CUDA();rows=[]
for kind in ['phase12','f32']:
 m=d.load(r/('phase12/artifacts/selected/modules' if kind=='phase12' else 'phase1/artifacts/f32-modules')/'deep_fast-packed-fast.hsaco')
 for n in [16,240,256]:
  a=np.zeros((3,n,1024),np.uint8);a[2]=0x38;x=d.alloc(a)
  for cap in [256,400]:
   out=np.zeros((n,1024),np.uint8);y=d.alloc(out);d.run(m,f'vit_attention_fused_{cap}_bytein_bout',[x,y,C.c_uint(n),C.c_uint64(0)],n//16*32);d.read(y,out)
   rows.append({'kind':kind,'tokens':n,'cap':cap,'uniform_QK0_V1_expected_byte':0x38,'got_unique':np.unique(out).tolist(),'wrong_values':int(np.count_nonzero(out!=0x38))});d.free(y)
  d.free(x)
 d.ok(d.d.cuModuleUnload(m))
(p/'attention-uniform-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
