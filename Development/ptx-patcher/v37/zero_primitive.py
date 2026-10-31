from pathlib import Path
import sys,ctypes as c,json,numpy as np,subprocess,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import v31.codegen as old;old.MODE='pack5'
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')])
body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];'+'\n'.join(old.declarations()+['.reg .b16 a,z;']+old.pack('%r0','a')+['mov.b16 z,0;','cvt.u32.u16 %r1,a;','cvt.u32.u16 %r2,z;'])+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
data=np.zeros(65536,dtype=np.uint32);out=execute(body,data,len(data)*2).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0
ptx='.version 8.0\n.target sm_86\n.address_size 64\n.visible .entry zero(.param .u64 dst){.reg .b64 ptr; .reg .b16 z; .reg .b32 w;ld.param.u64 ptr,[dst];mov.b16 z,0;mov.b32 w,{z,z};st.global.u32 [ptr],w;ret;}'
f=p/'artifacts/zero.ptx';f.write_text(ptx);tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/ptxas';r=subprocess.run([tool,'-arch=sm_86','-O4',str(f),'-o',str(f.with_suffix('.cubin'))],capture_output=True,text=True);assert r.returncode==0,r.stderr;sass=subprocess.check_output([tool.replace('ptxas','cuobjdump'),'-sass',str(f.with_suffix('.cubin'))],text=True);assert re.search(r'STG[^;]+RZ\s*;',sass)
(p/'zero-primitive.json').write_text(json.dumps({'mismatches':bad,'pairs':len(data),'domain':'both FP16 lanes positive zero only','constant_value':0,'arithmetic_instructions':0,'store_uses_RZ':True,'sass':sass,'compiler_output':r.stdout+r.stderr},indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx));print('PASS positive-zero primitive, STG RZ')
