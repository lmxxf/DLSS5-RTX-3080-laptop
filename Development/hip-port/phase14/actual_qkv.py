from pathlib import Path
import numpy as np,ctypes as C,json
from cuda_probe import CUDA
from reference import attention,decode
r=Path(__file__).resolve().parents[1];p=r/'phase14';d=CUDA();rows=[]
for kind in ['fixed','f32-fixed']:
 m=d.load(p/f'artifacts/{kind}/modules/deep_fast-packed-fast.hsaco')
 for src in ['phase12','f32']:
  raw=np.fromfile(r/f'phase13/artifacts/attention/{src}-legacy256/qkv.bin',np.uint8);n=240;x=d.alloc(raw);got={}
  for cap in [256,400]:
   a=np.zeros((n,1024),np.uint8);y=d.alloc(a);d.run(m,f'vit_attention_fused_{cap}_bytein_bout',[x,y,C.c_uint(n),C.c_uint64(0)],n//16*32);d.read(y,a);got[cap]=a;d.free(y)
  cpu=attention(raw);a=decode(got[256]).astype(float);b=decode(cpu).astype(float);row={'math':kind,'actual_source':src,'bytes':n*1024,'256_vs400_byte_diff':int(np.count_nonzero(got[256]!=got[400])),'256_vsCPU_byte_diff':int(np.count_nonzero(got[256]!=cpu)),'256_vsCPU_RMSE':float(np.sqrt(np.mean((a-b)**2))),'256_vsCPU_maxabs':float(np.max(abs(a-b)))};rows.append(row);print(row,flush=True);d.free(x)
 d.ok(d.d.cuModuleUnload(m))
(p/'actual-qkv-results.json').write_text(json.dumps(rows,indent=2)+'\n')
