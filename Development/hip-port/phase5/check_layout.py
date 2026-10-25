#!/usr/bin/env python3
"""Compare packed Benes to the retained scalar reference on the actual GPU."""
from pathlib import Path
import sys,subprocess,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
from build_sm86_modules import compile_one_module
out=root/'phase5/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='layout_probe',sources=['../phase5/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'layout_probe.hsaco').encode()))
n=65536;rng=np.random.default_rng(55)
c=rng.integers(0,2**32,(n,32,8),dtype=np.uint32)
# Every half bit pattern appears at every one of the 256 lane/element positions.
h=((np.arange(n,dtype=np.uint32)[:,None,None]+np.arange(256,dtype=np.uint32).reshape(1,32,8)*257)&65535).astype(np.uint16)
b=h.view(np.uint32);result=np.zeros((n,32,24),np.uint32)
def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
args=[alloc(c),alloc(b),alloc(result),U(n)];argv=(P*4)(*[C.cast(C.pointer(a),P) for a in args]);fn=P();ok(d.cuModuleGetFunction(C.byref(fn),module,b'compare_layouts'));ok(d.cuLaunchKernel(fn,n,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,args[2],result.nbytes))
stats={'warps':n,'c_f32_random_values':int(c.size),'d_half_patterns_per_position':65536,'d_positions':256,'c_packed_u32_bitdiff':int(np.count_nonzero(result[:,:,:4]!=result[:,:,4:8])),'d_f32_bitdiff':int(np.count_nonzero(result[:,:,8:16]!=result[:,:,16:24]))}
assert stats['c_packed_u32_bitdiff']==0 and stats['d_f32_bitdiff']==0,stats
# Required independent single/multi-MMA validation, using the new header.
m=dict(name='wmma_probe',sources=['../Development/HIP/wmma_probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
subprocess.run(['g++','-O2',str(root/'hip/wmma_validate_cuda.cpp'),'-L/usr/lib/wsl/lib','-lcuda','-o',str(out/'wmma_validate_cuda')],check=True)
v=subprocess.run([str(out/'wmma_validate_cuda'),str(out/'wmma_probe.hsaco'),'--fp16-acc'],check=True,capture_output=True,text=True)
print(json.dumps(stats,indent=2));print(v.stdout)
(root/'phase5/layout-validation.json').write_text(json.dumps(stats,indent=2)+'\n');(root/'phase5/wmma-validation.log').write_text(v.stdout)
