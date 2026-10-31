from pathlib import Path
import sys,json,ctypes as c,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from v26.codegen import decode
src=(p.parent/'v2/check_primitives.py').read_text();snippet=src[:src.index('# All 65536 byte pairs')].replace('mad.lo.u32 %idx,%a,32,%t;', 'mov.u32 %r9,%tid.y;mad.lo.u32 %t,%r9,32,%t;mad.lo.u32 %idx,%a,64,%t;').replace('(threads or len(inp))//32,1,1,32,1,1','(threads or len(inp))//64,1,1,32,2,1');exec(snippet)
threads=65536;data=np.random.default_rng(3607).integers(0,2**32,threads*4,dtype=np.uint32)
body='.shared .align 16 .b8 raw[1024];.shared .align 16 .b8 ext[2048];.reg .b32 tid,peer,sa,se,ra,ea,t0,t1,t2,t3,dlssnr_fp8_scale,'+','.join([f'a{i}' for i in range(8)]+[f'b{i}' for i in range(8)])+';mov.u32 tid,%t;mov.u32 ra,raw;mov.u32 ea,ext;shl.b32 sa,tid,4;add.u32 sa,sa,ra;mul.wide.u32 %off,%idx,16;add.u64 %sp,%sp,%off;cp.async.cg.shared.global [sa],[%sp],16;cp.async.commit_group;cp.async.wait_group 0;bar.sync 0;ld.shared.v4.u32 {t0,t1,t2,t3},[sa];mov.b32 dlssnr_fp8_scale,0x5c005c00;'
for i in range(4):body+='\n'.join(decode(f't{i}',f'a{2*i}',f'a{2*i+1}'))
body+='shl.b32 se,tid,5;add.u32 se,se,ea;st.shared.v4.u32 [se],{a0,a1,a2,a3};st.shared.v4.u32 [se+16],{a4,a5,a6,a7};bar.sync 0;xor.b32 peer,tid,63;shl.b32 sa,peer,4;add.u32 sa,sa,ra;ld.shared.v4.u32 {t0,t1,t2,t3},[sa];'
for i in range(4):body+='\n'.join(decode(f't{i}',f'b{2*i}',f'b{2*i+1}'))
body+='shl.b32 se,peer,5;add.u32 se,se,ea;ld.shared.v4.u32 {a0,a1,a2,a3},[se];ld.shared.v4.u32 {a4,a5,a6,a7},[se+16];mul.wide.u32 %off,%idx,64;add.u64 %dp,%dp,%off;'
for off,regs in [(0,'b0,b1,b2,b3'),(16,'b4,b5,b6,b7'),(32,'a0,a1,a2,a3'),(48,'a4,a5,a6,a7')]:body+=f'st.global.v4.u32 [%dp+{off}],{{{regs}}};'
out=execute(body,data,threads*16,threads).reshape(-1,16);bad=int(np.count_nonzero(out[:,:8]!=out[:,8:]));assert bad==0;(p/'async-primitive.json').write_text(json.dumps({'threads':threads,'block':[32,2,1],'arbitrary_u32_input_words':len(data),'word_mismatches':bad,'old_copy':'real cp.async.cg.shared.global 16B, commit/wait + CTA barrier','extra_per_thread_16B_chunk':{'LDS_v4':1,'decode_PTX':32,'STS_v4':2},'additional_BAR_per_CTA':1,'scope':'constructive real-copy cross-warp correctness, not end-to-end latency prediction'},indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx));print('async primitive PASS')
