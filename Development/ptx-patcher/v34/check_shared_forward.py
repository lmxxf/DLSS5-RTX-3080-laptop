from pathlib import Path
import ctypes as c,json,numpy as np
from shared_forward import apply
p=Path(__file__).resolve().parent;cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(n):assert n==0,n
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev))
ptx='''.version 8.0
.target sm_86
.address_size 64
.visible .entry demo(.param .u64 src,.param .u64 dst)
.maxntid 32,2,1
{
.reg .b32 %r<16>;
.reg .b64 %rd<6>;
.shared .align 16 .b8 storage[1024];
ld.param.u64 %rd0,[src];ld.param.u64 %rd1,[dst];
mov.u32 %r9,%tid.x;mov.u32 %r10,%tid.y;mov.u32 %r11,%ntid.x;
mad.lo.u32 %r12,%r10,%r11,%r9;mul.wide.u32 %rd2,%r12,16;
add.u64 %rd3,%rd0,%rd2;ld.global.v4.u32 {%r0,%r1,%r2,%r3},[%rd3];
mov.u32 %r13,storage;shl.b32 %r14,%r12,4;add.u32 %r8,%r13,%r14;
st.shared.v4.u32 [%r8],{%r0,%r1,%r2,%r3};bar.sync 0;
ld.shared.v4.u32 {%r4,%r5,%r6,%r7},[%r8];
add.u64 %rd4,%rd1,%rd2;st.global.v4.u32 [%rd4],{%r4,%r5,%r6,%r7};ret;
}
'''
plan={'demo':[{'shape':[32,2,1],'destinations':[f'%r{i}' for i in range(4,8)],'sources':[f'%r{i}' for i in range(4)],'address':'[%r8]'}]};new,n=apply(ptx,0,plan);assert n==1;rows=[]
for text,version in [(ptx,'baseline'),(new,'forwarded')]:
 mod=c.c_void_p();ck(cu.cuModuleLoadData(c.byref(mod),c.c_char_p(text.encode())));fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,b'demo'))
 for bx,by in [(32,2),(32,1),(16,2)]:
  inp=np.random.default_rng(3400).integers(0,2**32,bx*by*4,dtype=np.uint32);out=np.zeros_like(inp);src=c.c_uint64();dst=c.c_uint64();ck(cu.cuMemAlloc_v2(c.byref(src),c.c_size_t(inp.nbytes)));ck(cu.cuMemAlloc_v2(c.byref(dst),c.c_size_t(out.nbytes)));ck(cu.cuMemcpyHtoD_v2(src,c.c_void_p(inp.ctypes.data),c.c_size_t(inp.nbytes)));args=(c.c_void_p*2)(c.cast(c.byref(src),c.c_void_p),c.cast(c.byref(dst),c.c_void_p));ck(cu.cuLaunchKernel(fn,1,1,1,bx,by,1,0,None,args,None));ck(cu.cuCtxSynchronize());ck(cu.cuMemcpyDtoH_v2(c.c_void_p(out.ctypes.data),dst,c.c_size_t(out.nbytes)));assert np.array_equal(inp,out);rows.append({'version':version,'block':[bx,by,1],'runtime_fast_path':version=='forwarded' and (bx,by)==(32,2),'word_bitdiff':int(np.count_nonzero(inp!=out))});ck(cu.cuMemFree_v2(src));ck(cu.cuMemFree_v2(dst))
 ck(cu.cuModuleUnload(mod))
ck(cu.cuCtxDestroy_v2(ctx));(p/'shared-forward-gpu-tests.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
