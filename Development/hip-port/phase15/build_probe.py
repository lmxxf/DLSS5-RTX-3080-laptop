from pathlib import Path
import sys,importlib.util,hashlib,json,re
r=Path(__file__).resolve().parents[1];p=r/'phase15';sys.path.insert(0,str(r/'hip'));sys.dont_write_bytecode=True
from phase14_transform import fix_legacy_attention_abi
from phase2_transform import masked,end_at
for kind in ['fixed','f32-fixed']:
 if kind=='fixed':
  import build_sm86_modules as b
  compat=r/'hip/sm86_compat.h'
 else:
  frozen=r/'phase1/artifacts/f32-source';spec=importlib.util.spec_from_file_location('p14_probe_f32',frozen/'build_sm86_modules.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);compat=frozen/'sm86_compat.h'
  old=b.transform_hip_to_sm86_cu;b.transform_hip_to_sm86_cu=lambda *a:fix_legacy_attention_abi(old(*a))
 original=b.assemble_module_source
 def assemble(*args):
  s=original(*args);ma=masked(s);m=re.search(r'\bvoid vit_attention_fused_body\(',ma);a=ma.index('{',end_at(ma,m.end()-1));z=end_at(ma,a,'{','}');func=s[m.start():z+1]
  func=func.replace('vit_attention_fused_body','p14_canonical_body').replace('q[0]=sm86_preshuffle_fp8(q[0]);q[1]=sm86_preshuffle_fp8(q[1]);','').replace('xb=sm86_preshuffle_fp8(xb);','')
  func=func.replace('sm86_wmma_fp8_preshuffled_a(q[k/16],y,a)','__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(q[k/16],y,a)').replace('sm86_wmma_fp8_preshuffled_a(xb,y,acc[c])','__builtin_amdgcn_wmma_f32_16x16x16_fp8_fp8_w32_gfx12(xb,y,acc[c])')
  return s+'\ntemplate<uint MAXT,bool ByteInput=false,bool ByteOut=false> __attribute__((device,always_inline)) '+func+'''
extern "C" __attribute__((global)) __attribute__((launch_bounds(32))) void p14_canonical(const float*in,float*out,uint n,const uint*gate){p14_canonical_body<256,true,true>(in,out,n);}
extern "C" __attribute__((global)) void p14_float_pack(const float*in,unsigned char*out,uint n){uint i=__builtin_amdgcn_workgroup_id_x()*256+__builtin_amdgcn_workitem_id_x();if(i<n){i2 a{};pack(a,0,in[i]);out[i]=(unsigned char)(a[0]&255);}}
'''
 b.assemble_module_source=assemble
 m=next(m for m in b.parse_ps1_modules(r/'hip/build-modules.ps1') if m['name']=='deep_fast-packed-fast');m['defines']+=['P14_PROBE_HASH 0x'+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:8]]
 out=p/'artifacts'/kind/'probe';out.mkdir(exist_ok=True);res=b.compile_one_module(m,str(r/'hip'),str(out),str(compat),str(r/'hip/ptx2cubin'));print(kind,res[0:3],flush=True);assert res[1],res[2]
