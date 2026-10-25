from pathlib import Path
import sys,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
from build_sm86_modules import compile_one_module
out=root/'phase7/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='primitive_probe',sources=['../phase7/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'primitive_probe.hsaco').encode()))

rng=np.random.default_rng(7)
# Random all-bit-domain values, every half, and FP8 rounding boundaries +/- nearby float ULPs.
h=np.arange(65536,dtype=np.uint16).view(np.float16).astype(np.float32).view(np.uint32)
bound=np.concatenate([(np.arange(0x3b000000,0x44000000,0x80000,dtype=np.int64)+d).astype(np.uint32) for d in [-2,-1,0,1,2]])
x=np.concatenate([rng.integers(0,2**32,2**22,dtype=np.uint32),h,bound,bound|0x80000000]);n=x.size
result=np.zeros((n,8),np.uint32)
def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
args=[alloc(x),alloc(result),U(n)];argv=(P*3)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'primitives'));ok(d.cuLaunchKernel(fn,(n+31)//32,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[1],result.nbytes))
stats={'samples':n,'fp8_bitdiff':int(np.count_nonzero(result[:,0]!=result[:,1])),'clamp4_bitdiff':int(np.count_nonzero(result[:,2]!=result[:,3])),'clamp448_bitdiff':int(np.count_nonzero(result[:,4]!=result[:,5])),'half_bits_bitdiff':int(np.count_nonzero(result[:,6]!=result[:,7]))}
print(stats);(root/'phase7/primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n');assert all(stats[k]==0 for k in stats if k!='samples')
