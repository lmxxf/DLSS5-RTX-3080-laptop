"""Independent F32 matrix attention on captured Q/K/V; diagnostic, not performance."""
from pathlib import Path
import numpy as np,json,hashlib
p=Path(__file__).resolve().parent

def decode(u):
 a=u&127
 return (np.where(u&128,-1.,1.)*np.where(a<8,a.astype(float)*2**-9,(1+(a&7).astype(float)/8)*np.exp2((a>>3).astype(float)-7))).astype(np.float32)
def encode(x):
 x=np.asarray(x,np.float32);b=x.view(np.uint32);s=(b>>24)&128;a=np.minimum(np.abs(x),np.float32(448)).astype(np.float32).view(np.uint32)
 sub=(a.view(np.float32)+np.float32(16384)).view(np.uint32)&255
 norm=((a+((a>>20)&1)+0x7ffff)>>20)-960
 return (s|np.where(a<0x3c800000,sub,norm)).astype(np.uint8)
rows={}
for k in ['phase12','f32']:
 a=p/f'artifacts/attention/{k}-legacy256';b=p/f'artifacts/attention/{k}-forced400';raw=np.fromfile(a/'qkv.bin',np.uint8);assert np.array_equal(raw,np.fromfile(b/'qkv.bin',np.uint8))
 n=240;q,kk,v=decode(raw).reshape(3,n,32,32).transpose(0,2,1,3)
 # CPU audit in F32 domain: FP8 inputs are exact, double accumulation -> one F32 rounding.
 score=np.matmul(q.astype(float),kk.astype(float).transpose(0,2,1)).astype(np.float32)
 scale=np.array([0x2dbb],np.uint16).view(np.float16)[0]
 af=np.clip((score.astype(float)*float(scale)+1.708984375).astype(np.float32),1.439453125,1.9775390625)
 hb=(af.view(np.uint32)>>13)-0x1c000;u=(((hb<<4)+0x4000)&65535).astype(np.uint16)
 prob=u.view(np.float16).astype(np.float32);prob8=decode(encode(prob))
 out=np.matmul(prob8.astype(float),v.astype(float));denom=prob.astype(float).sum(axis=2,keepdims=True)
 pred=decode(encode((out/denom).astype(np.float32))).transpose(1,0,2).reshape(n,1024)
 row={'input_qkv_sha256':hashlib.sha256(raw.tobytes()).hexdigest(),'cpu_attention_rms':float(np.sqrt(np.mean(pred.astype(float)**2))),'formula':'RNE(QK^T), source clamp/half-bit exp mapping, FP8(prob)*V / sum(half prob), E4M3 output','limitations':'F32 tensorcore partial order/rcp and F16 accumulation may differ near quantization boundaries; not requiring bit equality to CPU.'}
 for name,folder in [('legacy256',a),('forced400',b)]:
  got=decode(np.fromfile(folder/'av.bin',np.uint8)).reshape(n,1024);diff=pred.astype(float)-got;row[name]={'rmse':float(np.sqrt(np.mean(diff*diff))),'maxabs':float(np.max(abs(diff))),'got_rms':float(np.sqrt(np.mean(got.astype(float)**2))),'byte_equal_ratio':float(np.mean(encode(pred)==encode(got)))}
 rows[k]=row
(p/'attention-cpu-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
