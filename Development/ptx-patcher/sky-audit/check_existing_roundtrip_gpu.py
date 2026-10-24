from pathlib import Path
import ctypes as c,sys,numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import build_quantmapped as b
import check_quantmapped as ref
text='\n mma.sync.aligned.m16n8k32.row.col.f16.e4m3.e4m3.f16 {%r10, %r11}, {%r1, %r2, %r3, %r4}, {%r5, %r6}, {%r10, %r11};'
match=list(b.m.dp.FP8_MMA_PATTERN.finditer(text))
body='\n'.join(['.reg .b16 enc;', '.reg .b32 enc32, qm_q0;']+b.m.fast_half_conversion_declarations()+b.m.fast_fp8_conversion_declarations()+b.m.fast_half_pair_to_fp8_lines('%r99','enc')+['cvt.u32.u16 enc32, enc;']+b.m.fast_fp8_pair_to_half_lines('enc32','qm_q0'))

ptx='''.version 8.0
.target sm_86
.address_size 64
.visible .entry test(.param .u64 src, .param .u64 dst) {
.reg .b32 %r99, %idx, %a, %t;
.reg .b64 %sp, %dp, %off;
ld.param.u64 %sp,[src];ld.param.u64 %dp,[dst];
mov.u32 %a,%ctaid.x;mov.u32 %t,%tid.x;mad.lo.u32 %idx,%a,256,%t;
mul.wide.u32 %off,%idx,4;add.u64 %sp,%sp,%off;add.u64 %dp,%dp,%off;
ld.global.u32 %r99,[%sp];
'''+body+'\nst.global.u32 [%dp],qm_q0; ret; }'
Path('/tmp/dlss-sky-audit/quant-test.ptx').write_text(ptx)
cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(r):
 assert r==0,r
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev))
module=c.c_void_p();ck(cu.cuModuleLoadData(c.byref(module),c.c_char_p(ptx.encode())))
fun=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fun),module,b'test'))
h=np.arange(65536,dtype=np.uint32);inp=h | ((65535-h)<<16);out=np.zeros_like(inp)
src=c.c_uint64();dst=c.c_uint64();ck(cu.cuMemAlloc_v2(c.byref(src),c.c_size_t(inp.nbytes)));ck(cu.cuMemAlloc_v2(c.byref(dst),c.c_size_t(inp.nbytes)))
ck(cu.cuMemcpyHtoD_v2(src,c.c_void_p(inp.ctypes.data),c.c_size_t(inp.nbytes)))
args=(c.c_void_p*2)(c.cast(c.byref(src),c.c_void_p),c.cast(c.byref(dst),c.c_void_p))
ck(cu.cuLaunchKernel(fun,256,1,1,256,1,1,0,None,args,None));ck(cu.cuCtxSynchronize())
ck(cu.cuMemcpyDtoH_v2(c.c_void_p(out.ctypes.data),dst,c.c_size_t(out.nbytes)))
for shift in [0,16]:
 index=(inp>>shift)&65535;expected=ref.ref[index];valid=np.isfinite(index.astype(np.uint16).view(np.float16))
 actual=((out>>shift)&65535).astype(np.uint16);n=np.count_nonzero(actual[valid]!=expected[valid]);print('GPU finite mismatches lane',shift//16,n,'/',valid.sum())
ck(cu.cuCtxDestroy_v2(ctx))
