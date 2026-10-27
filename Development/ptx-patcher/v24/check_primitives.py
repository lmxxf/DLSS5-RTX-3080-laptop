from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import up,bias_pack,quad
from v22.codegen import declarations,pack
src=(p.parent/'v2/check_primitives.py').read_text();src=src[:src.index('# All 65536 byte pairs')];exec(src)
i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257
# Entire u16 decode domain, plus every u16 half pattern in both half lanes.
x=(i[:,None]|(poison[None,:]<<16)).reshape(-1)
load='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];'
body=load+'\n'+ '\n'.join(b.fast_fp8_conversion_declarations()+['.reg .b32 old,new;']+b.fast_fp8_pair_to_half_lines('%r0','old')+up('%r0','new'))+'\nmul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{old,new};'
r=execute(body,x,2*len(x)).reshape(-1,2);upbad=int(np.count_nonzero(r[:,0]!=r[:,1]));assert upbad==0
results={'up_pairs':len(x),'up_bitdiff':upbad,'bias':[],'quad':[]}
for rotate in [False,True]:
 inp=(x<<16)|(x>>16) if rotate else x
 body=load+'\n'+ '\n'.join(declarations()+['.reg .b16 old16,new16;']+pack('%r0','old16')+bias_pack('%r0','new16'))+'\ncvt.u32.u16 %r1,old16;cvt.u32.u16 %r2,new16;mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
 r=execute(body,inp,2*len(inp)).reshape(-1,2);bad=int(np.count_nonzero(r[:,0]!=r[:,1]));assert bad==0;results['bias'].append({'patterns':len(inp),'rotate':rotate,'all_bitdiff':bad})
 # Two independently packed pairs, including opposite signs/subnormals/NaNs.
 body=load+'xor.b32 %r3,%r0,0xa55a5aa5;\n'+'\n'.join(declarations()+['.reg .b16 old0,old1;']+pack('%r0','old0')+pack('%r3','old1'))+'\nmov.b32 %r1,{old0,old1};\n'+'\n'.join(quad('%r0','%r3','%r2',True))+'\nmul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
 r=execute(body,inp,2*len(inp)).reshape(-1,2);bad=int(np.count_nonzero(r[:,0]!=r[:,1]));assert bad==0;results['quad'].append({'patterns':len(inp),'rotate':rotate,'all_bitdiff':bad})
(p/'primitives.json').write_text(json.dumps(results,indent=2)+'\n');print(results);ck(cu.cuCtxDestroy_v2(ctx))
