from pathlib import Path
import sys,json,ctypes as c,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from v26.codegen import decode
import v31.codegen as pack;pack.MODE='pack5'
src=(p.parent/'v2/check_primitives.py').read_text();exec(src[:src.index('# All 65536 byte pairs')])
i=np.arange(65536,dtype=np.uint32);poison=np.arange(256,dtype=np.uint32)*257;x=(i[:,None]|(poison[None,:]<<16)).reshape(-1);records=[]
load='mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;ld.global.u32 %r0,[%sp];'
for rotate in [False,True]:
 data=(x<<16)|(x>>16) if rotate else x
 # Pair alignment / arbitrary-byte exact decode and encode roundtrip.
 body=load+'\n'.join(['.reg .b32 l,h,dlssnr_fp8_scale;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']+decode('%r0','l','h')+pack.declarations()+['.reg .b16 a,z;']+pack.pack('l','a')+pack.pack('h','z')+['mov.b32 %r1,{a,z};'])+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r0,%r1};'
 out=execute(body,data,len(data)*2).reshape(-1,2);valid=np.ones(len(data),bool)
 for shift in [0,8,16,24]:valid &= ((data>>shift)&127)!=127
 bad=int(np.count_nonzero(out[valid,0]!=out[valid,1]));assert bad==0;records.append({'test':'finite FP8 word decode/repack identity','rotate':rotate,'words':len(data),'valid_words':int(valid.sum()),'mismatches':bad})
 # fast clipped companion re-encodes exactly to the original pack5 output.
 body=load+'\n'.join(pack.declarations()+['.reg .b16 a,z;','.reg .b32 clipped,limit;']+pack.pack('%r0','a')+['abs.f16x2 clipped,%r0;','mov.b32 limit,0x5f005f00;','min.f16x2 clipped,clipped,limit;','lop3.b32 clipped,%r0,clipped,0x7fff7fff,0xd8;']+pack.pack('clipped','z')+['cvt.u32.u16 %r1,a;','cvt.u32.u16 %r2,z;'])+'mul.wide.u32 %off,%idx,8;add.u64 %dp,%dp,%off;st.global.v2.u32 [%dp],{%r1,%r2};'
 out=execute(body,data,len(data)*2).reshape(-1,2);bad=int(np.count_nonzero(out[:,0]!=out[:,1]));assert bad==0;valid_codes=all(np.all(((out[:,0]>>sh)&127)!=127) for sh in [0,8]);assert valid_codes;records.append({'test':'clamp companion pack5 identity including all half bit patterns','rotate':rotate,'pairs':len(data),'mismatches':bad,'pack5_emits_no_reserved_7f_ff':valid_codes})
 print(records[-2:],flush=True)
# Real Shared exchange: reverse lanes within a warp, write-decode/read-native.
data=np.random.default_rng(3500).integers(0,2**32,65536,dtype=np.uint32)
body=load+'.shared .align 16 .b8 raw[128];.shared .align 16 .b8 expanded[256];.reg .b32 lane,peer,ra,ea,rf,ef,l,h,a,z,dlssnr_fp8_scale;mov.u32 lane,%tid.x;xor.b32 peer,lane,31;mov.u32 ra,raw;mov.u32 ea,expanded;shl.b32 rf,lane,2;add.u32 rf,rf,ra;st.shared.u32 [rf],%r0;mov.b32 dlssnr_fp8_scale,0x5c005c00;'+'\n'.join(decode('%r0','l','h'))+'shl.b32 ef,lane,3;add.u32 ef,ef,ea;st.shared.v2.u32 [ef],{l,h};bar.sync 0;shl.b32 rf,peer,2;add.u32 rf,rf,ra;ld.shared.u32 %r1,[rf];'+'\n'.join(decode('%r1','a','z'))+'shl.b32 ef,peer,3;add.u32 ef,ef,ea;ld.shared.v2.u32 {l,h},[ef];mul.wide.u32 %off,%idx,16;add.u64 %dp,%dp,%off;st.global.v4.u32 [%dp],{a,z,l,h};'
out=execute(body,data,len(data)*4).reshape(-1,4);bad=int(np.count_nonzero(out[:,:2]!=out[:,2:]));assert bad==0;records.append({'test':'Shared byte x2 cross-lane mirror, arbitrary u32 including reserved FP8 bytes','threads':len(data),'mismatches':bad})
# Same byte isomorphism across two warps; no warp-local identity assumption.
fragment=src[src.index('def execute'):src.index('# All 65536 byte pairs')]
fragment=fragment.replace('mad.lo.u32 %idx,%a,32,%t;', 'mov.u32 %r9,%tid.y;mad.lo.u32 %t,%r9,32,%t;mad.lo.u32 %idx,%a,64,%t;').replace('(threads or len(inp))//32,1,1,32,1,1','(threads or len(inp))//64,1,1,32,2,1')
exec(fragment)
body64=body.replace('raw[128]','raw[256]').replace('expanded[256]','expanded[512]').replace('mov.u32 lane,%tid.x;xor.b32 peer,lane,31;', 'mov.u32 lane,%tid.x;mov.u32 peer,%tid.y;mad.lo.u32 lane,peer,32,lane;xor.b32 peer,lane,63;')
out=execute(body64,data,len(data)*4).reshape(-1,4);bad=int(np.count_nonzero(out[:,:2]!=out[:,2:]));assert bad==0;records.append({'test':'Shared byte x2 cross-warp mirror','threads':len(data),'block':[32,2,1],'mismatches':bad})
(p/'primitive-tests.json').write_text(json.dumps(records,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
