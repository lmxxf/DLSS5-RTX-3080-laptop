from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import codegen as gen
from v22.codegen import declarations,pack
src=(p.parent/'v2/check_primitives.py').read_text();src=src[:src.index('# All 65536 byte pairs')];exec(src)
results={}
for mode in ['exact','fast']:
 gen.MODE=mode;checks=[]
 for rotate in [False,True]:
  i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
  if rotate:x=(x<<16)|(x>>16)
  body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];\n'+'\n'.join(declarations()+gen.declarations()+['.reg .b16 old16,new16;']+pack('%r0','old16')+gen.pack('%r0','new16'))+'\ncvt.u32.u16 %r1,old16;cvt.u32.u16 %r2,new16;mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
  r=execute(body,x,2*len(x)).reshape(-1,2);bad=r[:,0]!=r[:,1];checks.append({'rotate':rotate,'pairs':len(x),'mismatch_pairs':int(bad.sum()),'examples':[{'input':hex(int(x[j])),'old':hex(int(r[j,0])),'new':hex(int(r[j,1]))} for j in np.flatnonzero(bad)[:10]]})
  assert mode!='exact' or not bad.any();print(mode,rotate,checks[-1],flush=True)
 results[mode]=checks;print(mode,checks,flush=True)
(p/'primitives.json').write_text(json.dumps(results,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
