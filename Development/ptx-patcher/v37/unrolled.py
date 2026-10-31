"""Fixed actual launch geometry, statically unrolled word refresh; no control loop."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from v26.codegen import decode
import json
from pathlib import Path
QKV='cc_split_swin_16h_qkv_512_chained_fp8'
def refresh_code(k,ordinal):
 profile=json.loads((Path(__file__).parent.parent/'v23/profile.json').read_text());blocks={tuple(x['block']) for r in profile.values() for x in r['calls'] if x['name']==QKV};assert len(blocks)==1;nx,ny,nz=next(iter(blocks));assert nx*ny*nz==128
 lines=['{','.reg .b32 cx,cy,cz,tid,off,addr,oldbase,newbase,w,lo,hi,dlssnr_fp8_scale;','mov.u32 cx,%tid.x;','mov.u32 cy,%tid.y;','mov.u32 cz,%tid.z;',f'mad.lo.u32 tid,cz,{ny},cy;',f'mad.lo.u32 tid,tid,{nx},cx;','shl.b32 off,tid,2;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']
 for si,(symbol,d) in enumerate(k['symbols'].items()):
  assert d['bytes']%(128*4)==0
  lines += [f'mov.u32 oldbase,{symbol};',f'mov.u32 newbase,v36_async_ext{si};']
  for offset in range(0,d['bytes'],128*4):
   lines += ['add.u32 addr,oldbase,off;',f'ld.shared.u32 w,[addr+{offset}];']+decode('w','lo','hi')+['shl.b32 addr,off,1;','add.u32 addr,newbase,addr;',f'st.shared.v2.u32 [addr+{2*offset}],{{lo,hi}};']
 return '\n'.join(lines+['bar.sync 0;','}'])
