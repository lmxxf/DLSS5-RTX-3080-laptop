from pathlib import Path
import ctypes as C,numpy as np,json,hashlib
from cuda_probe import CUDA
from reference import encode,decode,attention
r=Path(__file__).resolve().parents[1];p=r/'phase15';d=CUDA();rows=[];rng=np.random.default_rng(1401)
def invoke(m,name,raw,n,float_output=False):
 x=d.alloc(np.ascontiguousarray(raw));out=np.zeros((n,1024),np.float32 if float_output else np.uint8);y=d.alloc(out);d.run(m,name,[x,y,C.c_uint(n),C.c_uint64(0)],n//16*32);d.read(y,out);d.free(x,y);return out
cases=[]
for n in range(16,257,16):
 q=np.zeros((3,n,32,32),np.uint8)
 for h in range(32):q[0,n-1,h,h%32]=0x38;q[1,n-1,h,h%32]=0x40;q[2,n-1,h,h%32]=0x38;q[2,0,h,(h+17)%32]=0xb0
 cases.append((n,'head-coordinate-last-token',q.reshape(3,n,1024)))
 a=rng.normal(0,1,(3,n,32,32)).astype(np.float32);a[0]/=np.linalg.norm(a[0],axis=2,keepdims=True);a[0]*=5.65625;a[1]/=np.linalg.norm(a[1],axis=2,keepdims=True)
 cases.append((n,'random-normalized',encode(a).reshape(3,n,1024)))
 a=rng.choice(np.array([0,128,1,129,7,135,8,136],np.uint8),(3,n,1024));cases.append((n,'subnormal-signed-zero',a))
 a=rng.choice(np.array([0,128,0x7e,0xfe,0x38,0xb8],np.uint8),(3,n,1024));a[2]=rng.choice(np.array([0,128,0x38,0xb8],np.uint8),(n,1024));cases.append((n,'finite-boundary',a))
 # Reserved NaN codes are tested for unchanged ABI equivalence only. Packed MMA's
 # existing decoder interprets +/-0x7f as +/-480; this task does not redefine it.
 a=rng.choice(np.array([0,128,0x7f,0xff,0x38,0xb8],np.uint8),(3,n,1024));cases.append((n,'reserved-byte-ABI-only',a))
for src in ['phase12','f32']:
 cases.append((240,'actual-'+src,np.fromfile(p/f'artifacts/actual-qkv/{src}.bin',np.uint8).reshape(3,240,1024)))
for kind in ['fixed','f32-fixed']:
 m=d.load(p/f'artifacts/{kind}/probe/deep_fast-packed-fast.hsaco')
 for n,label,raw in cases:
  a=invoke(m,'vit_attention_fused_256_bytein_bout',raw,n);b=invoke(m,'vit_attention_fused_400_bytein_bout',raw,n);canonical=invoke(m,'p14_canonical',raw,n)
  row={'math':kind,'n':n,'case':label,'bytes':a.size,'fixed_vs400_byte_diff':int(np.count_nonzero(a!=b)),'fixed_vscanonical_byte_diff':int(np.count_nonzero(a!=canonical)),'input_sha256':hashlib.sha256(raw.tobytes()).hexdigest(),'output_sha256':hashlib.sha256(a.tobytes()).hexdigest()}
  rows.append(row)
  assert row['fixed_vscanonical_byte_diff']==0,row
  # Transposed-score and legacy are required to match in the supported finite domain.
  # Non-finite intermediate overflow is checked against the raw-layout reference.
  print(kind,n,label,row['fixed_vs400_byte_diff'],row['fixed_vscanonical_byte_diff'],flush=True)
 for n in [16,128,240,256]:
  a=rng.uniform(-1,1,(3,n,1024)).astype(np.float32);bits=a.view(np.uint32).reshape(-1)
  special=[0,0x80000000,0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7f800001,0xff800001]
  for i,bits_value in enumerate(special):bits[i::257]=bits_value
  x=d.alloc(a);q=np.zeros(a.size,np.uint8);y=d.alloc(q);d.run(m,'p14_float_pack',[x,y,C.c_uint(a.size)],(a.size+255)//256,256);d.read(y,q);d.free(x,y)
  direct=invoke(m,'vit_attention_fused_256',a,n,True);quantized=invoke(m,'vit_attention_fused_256_bytein',q,n,True)
  assert np.array_equal(direct.view(np.uint32),quantized.view(np.uint32)),(kind,n,'float conversion')
  converted=invoke(m,'vit_attention_fused_256_bytein_bout',q,n);canonical=invoke(m,'p14_canonical',q,n)
  assert np.array_equal(converted,canonical),(kind,n,'float special ABI')
  assert np.array_equal(encode(direct),converted),(kind,n,'float output encoding')
  alt=invoke(m,'vit_attention_fused_400_bytein_bout',q,n);assert np.array_equal(converted,alt),(kind,n,'float specials vs400')
  rows.append({'math':kind,'n':n,'case':'float-NaN-Inf-signed-zero-normalization','float_vs_quantized_bitdiff':0,'fixed_vscanonical_byte_diff':0,'quantized_reserved_nan_count':int(np.count_nonzero((q&127)==127)),'input_nonfinite_count':int(np.count_nonzero(~np.isfinite(a))),'first8_source_pack_bytes':q[:8].tolist()})
 d.ok(d.d.cuModuleUnload(m))
assert all(x.get('fixed_vs400_byte_diff',0)==0 for x in rows)
summary={'all_fixed_vs400_byte_diff':0,'rows':rows,'all_fixed_vscanonical_diff':0,'cases_per_math':len(cases),'token_domain':'16..256 in steps16, matching Host n%16 contract; n%64 tails included','NaN_policy':'Float NaN/Inf/+-0 tested through real source pack clamp. Raw7f/ff ABI-only: existing packed decoder finite shortcut is not IEEE NaN; no new claim.'}
(p/'coverage-results.json').write_text(json.dumps(summary,indent=2)+'\n');print('PASS',len(rows),'tests')
