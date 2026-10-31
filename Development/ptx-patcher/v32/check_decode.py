from pathlib import Path
import sys,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b
import v26.codegen as old
import v32.codegen as new
from v24.codegen import up
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')])
i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1);rows=[]
for mode in ['up','shift']:
 new.IMMEDIATE=False;new.SHIFT_MASK=(mode=='shift')
 for rotate in [False,True]:
  inp=(x<<16)|(x>>16) if rotate else x
  reference=old.decode('%r0','a','b') if mode=='shift' else b.fast_fp8_pair_to_half_lines('%r0','a')
  candidate=new.decode('%r0','c','d') if mode=='shift' else up('%r0','c')
  body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];'+ '\n'.join(b.fast_fp8_conversion_declarations()+['.reg .b32 a,b,c,d;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']+reference+candidate)+'mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{a,b,c,d};'
  out=execute(body,inp,len(inp)*4).reshape(-1,4)
  bad=int(np.count_nonzero(out[:,0]!=out[:,2]))
  if mode=='shift':bad+=int(np.count_nonzero(out[:,1]!=out[:,3]))
  assert bad==0,(mode,rotate,bad);rows.append(dict(mode=mode,rotate=rotate,pairs=len(inp),bitdiff=bad));print(rows[-1],flush=True)
(p/'shift-tests.json').write_text(json.dumps(rows,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
