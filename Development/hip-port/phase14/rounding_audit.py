from pathlib import Path
import sys,ctypes as C,json,numpy as np
from cuda_probe import CUDA
from reference import decode,encode,attention
r=Path(__file__).resolve().parents[1];p=r/'phase14';sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
out=p/'artifacts/rounding';out.mkdir(exist_ok=True);m=dict(name='rounding',sources=['../phase14/rounding_probe.hip'],defines=[],l23defines=[]);res=b.compile_one_module(m,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res[2]
d=CUDA();mod=d.load(out/'rounding.hsaco');rows=[]
for i in range(8):
 raw=np.fromfile(p/f'artifacts/gold-capture/{i}-qkv.bin',np.uint8);q,k,v=decode(raw).reshape(3,240,32,32).transpose(0,2,1,3)
 score=np.matmul(q.astype(float),k.astype(float).transpose(0,2,1)).astype(np.float32);scale=np.array([0x2dbb],np.uint16).view(np.float16)[0]
 af=np.clip((score.astype(float)*float(scale)+1.708984375).astype(np.float32),1.439453125,1.9775390625);hb=(af.view(np.uint32)>>13)-0x1c000;prob=((((hb<<4)+0x4000)&65535).astype(np.uint16)).view(np.float16).astype(np.float32)
 den=prob.astype(float).sum(axis=2).astype(np.float32);num=np.matmul(decode(encode(prob)).astype(float),v.astype(float)).astype(np.float32)
 x=d.alloc(den);inv=np.zeros_like(den);y=d.alloc(inv);d.run(mod,'p14_rcp',[x,y,C.c_uint(den.size)],(den.size+255)//256,256);d.read(y,inv);d.free(x,y)
 product=(num*inv[:,:,None]).astype(np.float32);pred=encode(product).transpose(1,0,2).reshape(240,1024);got=np.fromfile(p/f'artifacts/gold-capture/{i}-av.bin',np.uint8).reshape(240,1024);diff=int(np.count_nonzero(pred!=got));assert diff==0,(i,diff)
 row={'block':31+i,'bytes':pred.size,'CPU_with_isolated_rcp_byte_diff':diff}
 if i==1:
  z=np.argwhere(attention(raw)!=got);assert len(z)==1;tok,channel=map(int,z[0]);head,feature=divmod(channel,32);exact=(num[head,tok,feature].astype(float)/den[head,tok].astype(float)).astype(np.float32)
  row['quantization_boundary']={'token':tok,'head':head,'channel':feature,'numerator_f32':float(num[head,tok,feature]),'denominator_f32':float(den[head,tok]),'exact_division_rounded_f32':float(exact),'rcp_approx_f32':float(inv[head,tok]),'gpu_mul_rne_f32':float(product[head,tok,feature]),'exact_division_fp8':int(encode(np.array([exact]))[0]),'actual_fp8':int(got[tok,channel])}
 rows.append(row)
(p/'rounding-results.json').write_text(json.dumps({'rows':rows,'total_bytes':8*240*1024,'CPU_with_primitive_rcp_byte_diff':0,'scope':'Independent CPU QK/prob/PV/denominator; only CUDA ISA rcp.approx primitive used to match explicit source inverse semantics. No attention output fed into reference.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
