from diag15b_paths import ROOT
from pathlib import Path
import numpy as np,ctypes as C,json
from reference import encode,decode
from cuda_probe import CUDA
p=Path(__file__).resolve().parent;root=ROOT;d=CUDA();mod=d.load(p/'artifacts/rounding/rounding.hsaco');rows=[]
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 name=case['case'];n=case['processing'][0]//64*(case['processing'][1]//64)
 for i in range(8):
  raw=np.fromfile(root/'traces'/name/'f32'/f'attention-{i}-in.bin',np.uint8);q,k,v=decode(raw).reshape(3,n,32,32).transpose(0,2,1,3)
  score=np.matmul(q.astype(float),k.astype(float).transpose(0,2,1)).astype(np.float32);scale=np.array([0x2dbb],np.uint16).view(np.float16)[0]
  af=np.clip((score.astype(float)*float(scale)+1.708984375).astype(np.float32),1.439453125,1.9775390625);hb=(af.view(np.uint32)>>13)-0x1c000;prob=((((hb<<4)+0x4000)&65535).astype(np.uint16)).view(np.float16).astype(np.float32)
  denominator=prob.astype(float).sum(axis=2).astype(np.float32);numerator=np.matmul(decode(encode(prob)).astype(float),v.astype(float)).astype(np.float32);xp=d.alloc(denominator);inv=np.zeros_like(denominator);yp=d.alloc(inv);d.run(mod,'p14_rcp',[xp,yp,C.c_uint(denominator.size)],(denominator.size+255)//256,256);d.read(yp,inv);d.free(xp,yp)
  pred=encode(numerator*inv[:,:,None]).transpose(1,0,2).reshape(n,1024);got=np.fromfile(root/'traces'/name/'f32'/f'attention-{i}-out.bin',np.uint8).reshape(n,1024);diff=int(np.count_nonzero(pred!=got));delta=decode(pred).astype(float)-decode(got)
  row={'case':name,'block':31+i,'tokens':n,'bytes':got.size,'CPU_with_rcp_byte_diff':diff,'maxabs':float(np.max(abs(delta))),'RMS_error':float(np.sqrt(np.mean(delta*delta))),'reserved_nan_inputs':int(np.count_nonzero((raw&127)==127))};rows.append(row);print(row,flush=True)
(p/'diag15b-attention-cpu.json').write_text(json.dumps({'rows':rows,'scope':'Actual frozen input, taps armed afterPrepare; independent CPU QK/prob/denominator/PV, isolated existing rcp.approx; no gold or default changes'},indent=2)+'\n')
