from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from decode import decode
from v23.decode import decode as reference
b.even_odd_decode_lines=reference
# Reuse only the CUDA launch helper, not the old test's executed cases.
s=(p.parent/'v2/check_primitives.py').read_text();s=s[:s.index('# All 65536 byte pairs')];s=s.replace("p=Path(__file__).resolve().parent", "p=Path(__file__).resolve().parent");exec(s)
i=np.arange(65536,dtype=np.uint32);other=np.arange(256,dtype=np.uint32)
# Exhaust both requested byte pairs, with every possible byte value poisoning
# the unused pair; repeat inverted poison to exercise asymmetry.
lo=(i&255)[:,None];hi=(i>>8)[:,None];q=other[None,:]
x=(lo|(hi<<16)|(q<<8)|((255-q)<<24)).reshape(-1)
body='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];\n'+'\n'.join(b.fast_fp8_conversion_declarations())+'\n.reg .b32 old0,old1,new0,new1;mov.b32 dlssnr_fp8_scale,0x5c005c00;\n'+'\n'.join(b.even_odd_decode_lines('%r0','old0','old1')+decode('%r0','new0','new1'))+'\nmul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{old0,old1,new0,new1};'
bad=0
for rotate in [False,True]:
 inp=((x<<8)|(x>>24)) if rotate else x
 r=execute(body,inp,len(inp)*4).reshape(-1,4);bad+=int(np.count_nonzero(r[:,:2]!=r[:,2:]))
stats={'pairs':2*len(x),'FP8_patterns_per_byte':256,'all_bitdiff':bad,'old_PTX_lines':8,'new_PTX_lines':8,'including_nonfinite':True};(p/'decode-test.json').write_text(json.dumps(stats,indent=2)+'\n');print(stats);assert bad==0
ck(cu.cuCtxDestroy_v2(ctx))
