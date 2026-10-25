from pathlib import Path
import sys,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE10_FP8=True
compile_one_module=build.compile_one_module
out=root/'phase10/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='finite_probe',sources=['../phase10/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'finite_probe.hsaco').encode()))

rng=np.random.default_rng(10)
x=rng.integers(0,2**32,2**22,dtype=np.uint32);x=x[(x&0x7f800000)!=0x7f800000]
h=np.arange(65536,dtype=np.uint16).view(np.float16).astype(np.float32);h=h[np.isfinite(h)].view(np.uint32)
grid=np.array([((b&7)/512 if b<8 else (1+(b&7)/8)*2.**((b>>3)-7)) for b in range(127)],np.float32)
mid=((grid[:-1]+grid[1:])/2).view(np.uint32)
bounds=np.concatenate([(mid.astype(np.int64)+d).astype(np.uint32) for d in [-2,-1,0,1,2]])
corner=np.array([0,0x80000000,1,0x80000001,0x7f7fffff,0xff7fffff,0x3c800000,0xbc800000,0x43e00000,0xc3e00000],np.uint32)
special=np.array([0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7f800001,0xff800001],np.uint32)
x=np.concatenate([x,h,bounds,bounds|0x80000000,corner,special]);finite=(x&0x7f800000)!=0x7f800000;n=x.size;result=np.zeros((n,8),np.uint32)
def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
args=[alloc(x),alloc(result),U(n)];argv=(P*3)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'compare'));ok(d.cuLaunchKernel(fn,(n+31)//32,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[1],result.nbytes))
stats={'finite_samples':int(np.count_nonzero(finite)),'outer_clamp_preserve_zero_bitdiff':int(np.count_nonzero(result[finite,0]!=result[finite,1])),'outer_clamp_add_zero_bitdiff':int(np.count_nonzero(result[finite,2]!=result[finite,3])),'lowreg_vs_fast_bitdiff':int(np.count_nonzero(result[finite,1]!=result[finite,5])),'negative_zero_old_preserved':int(result[np.where(x==0x80000000)[0][0],0]),'negative_zero_add0':int(result[np.where(x==0x80000000)[0][0],3])}
stats['nonfinite_diagnostic']=[{'bits':hex(int(x[i])),'old_clamped':int(result[i,0]),'new_saturating':int(result[i,1]),'old_raw':int(result[i,4])} for i in np.flatnonzero(~finite)]
print(stats);(root/'phase10/primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n');assert stats['outer_clamp_preserve_zero_bitdiff']==stats['outer_clamp_add_zero_bitdiff']==stats['lowreg_vs_fast_bitdiff']==0
