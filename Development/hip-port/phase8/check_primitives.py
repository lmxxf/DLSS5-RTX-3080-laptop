from pathlib import Path
import sys,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
from build_sm86_modules import compile_one_module
out=root/'phase8/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='direct_probe',sources=['../phase8/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'direct_probe.hsaco').encode()))

rng=np.random.default_rng(8);n=16385
h=rng.integers(0,65536,(n,32,8),dtype=np.uint16)
h[0]=np.arange(256,dtype=np.float16).view(np.uint16).reshape(32,8)
# All half patterns at each position across the random sample plus structured tags.
x=h.view(np.uint32);result=np.zeros((n,32,4),np.uint32)
def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
args=[alloc(x),alloc(result),U(n)];argv=(P*3)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'direct'));ok(d.cuLaunchKernel(fn,n,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[1],result.nbytes))
a=result[:,:,:2].copy().view(np.uint8);b=result[:,:,2:].copy().view(np.uint8)
stats={'unique_tag_positions':256,'tag_byte_differences':int(np.count_nonzero(a[0]!=b[0])),'random_half_values':int(h[1:].size),'quantized_byte_differences':int(np.count_nonzero(a[1:]!=b[1:]))};assert len(np.unique(a[0]))==256
print(stats);(root/'phase8/primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n');assert stats['tag_byte_differences']==stats['quantized_byte_differences']==0
