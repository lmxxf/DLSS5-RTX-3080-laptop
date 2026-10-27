from pathlib import Path
import sys,ctypes as c,json,numpy as np
p=Path(__file__).resolve().parent;(p/'artifacts').mkdir(exist_ok=True);sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import pack,declarations
cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(x):assert x==0,x
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev))
# Every half pattern in both positions, each paired with all 256 distinct
# adversarial values (sign/exponent/mantissa), including cross-lane carries.
i=np.arange(65536,dtype=np.uint32);other=(np.arange(256,dtype=np.uint32)*257)
x=(i[:,None]|(other[None,:]<<16)).reshape(-1);x=np.concatenate([x,(x<<16)|(x>>16)])
ptx='''.version 8.0
.target sm_86
.address_size 64
.visible .entry test(.param .u64 src,.param .u64 dst){
.reg .b64 sp,dp,off;
.reg .b32 idx,t,a,x,old,new;
.reg .b16 old16,new16;
ld.param.u64 sp,[src];ld.param.u64 dp,[dst];mov.u32 a,%ctaid.x;mov.u32 t,%tid.x;mad.lo.u32 idx,a,256,t;
mul.wide.u32 off,idx,4;add.u64 sp,sp,off;ld.global.u32 x,[sp];
'''+ '\n'.join(b.fast_half_conversion_declarations()+declarations()+b.fast_half_pair_to_fp8_lines('x','old16')+pack('x','new16'))+'''
cvt.u32.u16 old,old16;cvt.u32.u16 new,new16;shl.b32 new,new,16;or.b32 old,old,new;
add.u64 dp,dp,off;st.global.u32 [dp],old;ret;}
'''
(p/'artifacts/pack.ptx').write_text(ptx);mod=c.c_void_p();log=c.create_string_buffer(16384);opts=(c.c_int*2)(5,6);vals=(c.c_void_p*2)(c.cast(log,c.c_void_p),c.c_void_p(16384));ret=cu.cuModuleLoadDataEx(c.byref(mod),c.c_char_p(ptx.encode()),2,opts,vals);print(log.value.decode());ck(ret);fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,b'test'))
src=c.c_uint64();dst=c.c_uint64();out=np.zeros_like(x)
ck(cu.cuMemAlloc_v2(c.byref(src),c.c_size_t(x.nbytes)));ck(cu.cuMemAlloc_v2(c.byref(dst),c.c_size_t(out.nbytes)));ck(cu.cuMemcpyHtoD_v2(src,c.c_void_p(x.ctypes.data),c.c_size_t(x.nbytes)))
args=(c.c_void_p*2)(c.cast(c.byref(src),c.c_void_p),c.cast(c.byref(dst),c.c_void_p));ck(cu.cuLaunchKernel(fn,len(x)//256,1,1,256,1,1,0,None,args,None));ck(cu.cuCtxSynchronize());ck(cu.cuMemcpyDtoH_v2(c.c_void_p(out.ctypes.data),dst,c.c_size_t(out.nbytes)))
a=out&65535;z=out>>16;finite=((x&0x7c00)!=0x7c00)&((x&0x7c000000)!=0x7c000000);bad=(a!=z)
r={'packed_pairs':len(x),'finite_half_patterns':63488,'finite_pair_mismatches':int((bad&finite).sum()),'all_pair_mismatches':int(bad.sum()),'examples':[{'input':hex(int(x[j])),'old':hex(int(a[j])),'new':hex(int(z[j]))} for j in np.flatnonzero(bad&finite)[:8]],'ptx_lines':len(pack('x','new16'))}
(p/'pack-test.json').write_text(json.dumps(r,indent=2)+'\n');print(r);assert r['finite_pair_mismatches']==0
ck(cu.cuCtxDestroy_v2(ctx))
