from pathlib import Path
import sys,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE11_HALF_FEATURE_PACK=False
build.PHASE10_FP8=True
from transform import HALF_PACK_HELPER
original=build.phase10_optimize_fp8
build.phase10_optimize_fp8=original
# Helpers must precede the probe kernels.
orig_assemble=build.assemble_module_source
build.assemble_module_source=lambda *a,**k:orig_assemble(*a,**k).replace('using U=unsigned;',HALF_PACK_HELPER+'\nusing U=unsigned;')
compile_one_module=build.compile_one_module
out=root/'phase11/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='half_pack_probe',sources=['../phase11/probe_half_pack.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'half_pack_probe.hsaco').encode()))

n=65536
x=((np.arange(n,dtype=np.uint32)[:,None,None]+np.arange(256,dtype=np.uint32).reshape(1,32,8)*257)&65535).astype(np.uint16)
result=np.zeros((n,32,4),np.uint32)
def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
args=[alloc(x),alloc(result),U(n)];argv=(P*3)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'half_pack'));ok(d.cuLaunchKernel(fn,n,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[1],result.nbytes))
a=result[:,:,:2].copy().view(np.uint8);b=result[:,:,2:].copy().view(np.uint8);finite=(x&0x7c00)!=0x7c00
stats={'patterns_per_position':65536,'positions':256,'finite_bytes':int(np.count_nonzero(finite)),'finite_bitdiff':int(np.count_nonzero(a[finite]!=b[finite])),'all_bits_diagnostic_diff':int(np.count_nonzero(a!=b))};assert stats['finite_bitdiff']==0
print(stats);(root/'phase11/half-pack-primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n')

args=[alloc(x),alloc(result),U(n)];argv=(P*3)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'half_pack_rtz'));ok(d.cuLaunchKernel(fn,n,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[1],result.nbytes))
a=result[:,:,:2].copy().view(np.uint8);b=result[:,:,2:].copy().view(np.uint8)
rtz={'all_input_half_patterns_bitdiff':int(np.count_nonzero(a!=b))};print(rtz);assert rtz['all_input_half_patterns_bitdiff']==0
(root/'phase11/half-pack-rtz-primitive-results.json').write_text(json.dumps(rtz,indent=2)+'\n')
