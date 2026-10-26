from pathlib import Path
import sys,ctypes as C,json
import numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE12_C32_AV=False
build.PHASE11_HALF_FEATURE_PACK=False
build.PHASE10_FP8=True
from phase18_transform import helpers
compat=(root/"hip/sm86_compat.h").read_text();HELPERS=helpers(compat+"\nusing f8=sm86_f8;")[len(compat):].split("using f8=")[0]
original=build.phase10_optimize_fp8
build.phase10_optimize_fp8=original
# Helpers must precede the probe kernels.
orig_assemble=build.assemble_module_source
build.assemble_module_source=lambda *a,**k:orig_assemble(*a,**k).replace('using U=unsigned;',HELPERS+'\nusing U=unsigned;')
compile_one_module=build.compile_one_module
out=root/'phase18/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
m=dict(name='producer_probe',sources=['../phase18/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));assert r[1],r[2]
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types
d.cuMemFree_v2.argtypes=[Q]
def ok(r):assert r==0,r
ok(d.cuInit(0));dev=C.c_int();ok(d.cuDeviceGet(C.byref(dev),0));ctx=P();ok(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();ok(d.cuModuleLoad(C.byref(module),str(out/'producer_probe.hsaco').encode()))


def alloc(a):
 p=Q();ok(d.cuMemAlloc_v2(C.byref(p),a.nbytes));ok(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
n=65536+256
h=((np.arange(n,dtype=np.uint32)[:,None,None]+np.arange(256,dtype=np.uint32).reshape(1,32,8)*257)&65535).astype(np.uint16)
h[65536:]=0
for k in range(256):h[65536+k].reshape(-1)[k]=0x3c00
x=alloc(h.view(np.uint32));result=np.zeros((n,32,4),np.uint32)
# Use explicit output pointers for copy, independent of argument count.
def run(name,inputs,result,mode,steps=None):
 dst=alloc(result);warps=result.shape[0];args=inputs+[dst,U(warps),U(mode)]+([] if steps is None else [U(steps)])
 f=P();ok(d.cuModuleGetFunction(C.byref(f),module,name.encode()));argv=(P*len(args))(*[C.cast(C.pointer(a),P) for a in args]);ok(d.cuLaunchKernel(f,warps,1,1,32,1,1,0,None,argv,None));ok(d.cuCtxSynchronize());ok(d.cuMemcpyDtoH_v2(result.ctypes.data,dst,result.nbytes));a=result[:,:,:2].copy().view(np.uint8);b=result[:,:,2:].copy().view(np.uint8);diff=int(np.count_nonzero(a!=b));ok(d.cuMemFree_v2(dst));return diff
stats={}
for mode,name in enumerate(['contract','result','v','av','byteout','c32-prefix','c32-v']):
 diff=run('producer',[x],result,mode);stats[name]={'all_half_patterns_and_onehot_byte_diff':diff,'half_patterns_per_position':65536,'positions':256,'onehot_layout_cases':256};print(name,stats[name],flush=True)
assert all(v['all_half_patterns_and_onehot_byte_diff']==0 for v in stats.values()),stats
rng=np.random.default_rng(12);n=2048
# Prepared-fragment operands: random finite values, zeros, infinities and varied NaN payload/signs.
a=rng.uniform(-4,4,(n,32,8)).astype(np.float16).view(np.uint16);b=rng.uniform(-4,4,a.shape).astype(np.float16).view(np.uint16);c=np.zeros_like(a)
patterns=[0,0x8000,0x7c00,0xfc00,0x7c01,0xfc01,0x7fff,0xffff,1,0x8001,0x7bff,0xfbff]
for k,p in enumerate(patterns):a[k*8:(k+1)*8]=p;b[k*8:(k+1)*8]=0x3c00;c[(k+12)*8:(k+13)*8]=p
inputs=[alloc(v.view(np.uint32)) for v in [a,b,c]]
for mode,name in enumerate(['contract','result','v','av','byteout','c32-prefix','c32-v']):
 stats[name]['mma_steps']={}
 for steps in {'contract':[8],'result':[4,8,16],'v':[4,8,16],'av':[4],'byteout':[7,11,19],'c32-prefix':[1,2],'c32-v':[2]}[name]:
  diff=run('mma_producer',inputs,np.zeros((n,32,4),np.uint32),mode,steps);stats[name]['mma_steps'][steps]=diff;assert diff==0
print(stats);(root/'phase18/primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n')
