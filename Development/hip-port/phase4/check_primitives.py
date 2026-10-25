#!/usr/bin/env python3
import ctypes as C
import subprocess,sys,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'phase4/artifacts/probe';out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(root/'hip'))
from build_sm86_modules import compile_one_module
mod=dict(name='phase4_probe',sources=['../phase4/probe.hip'],defines=[],l23defines=[])
r=compile_one_module(mod,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'))
assert r[1],r[2]
cpp=out/'host.cpp';cpp.write_text(r'''#include "packed_weights.h"
#include <fstream>
#include <random>
#include <array>
int main(int argc,char**argv){std::ofstream a(std::string(argv[1])+"/original.bin",std::ios::binary),b(std::string(argv[1])+"/packed.bin",std::ios::binary);std::mt19937 g(42);for(unsigned n=0;n<64;n++){std::array<uint8_t,256> x;for(unsigned j=0;j<256;j++)x[j]=n?uint8_t(g()):uint8_t(j);a.write((char*)x.data(),256);auto y=x;hip_reference::AmperePreshuffleTile256(y.data());b.write((char*)y.data(),256);auto z=x;for(auto&v:z)v^=0x5a;auto w=z;hip_reference::AmperePreshuffleTile256(w.data());uint8_t wide[512];for(unsigned l=0;l<32;l++)for(unsigned h=0;h<2;h++)std::memcpy(wide+l*16+h*8,(h?z:x).data()+l*8,8);hip_reference::AmperePreshuffleTile512W16(wide);for(unsigned l=0;l<32;l++)for(unsigned h=0;h<2;h++)if(std::memcmp(wide+l*16+h*8,(h?w:y).data()+l*8,8))return 1;}return 0;}
''')
subprocess.run(['g++','-std=c++17','-O2','-I'+str(root/'Development/HIP'),str(cpp),'-o',str(out/'host')],check=True)
subprocess.run([str(out/'host'),str(out)],check=True)
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for name,types in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}.items():getattr(d,name).argtypes=types

def check(r):assert r==0,r
check(d.cuInit(0));dev=C.c_int();check(d.cuDeviceGet(C.byref(dev),0));ctx=P();check(d.cuCtxCreate_v2(C.byref(ctx),0,dev));module=P();check(d.cuModuleLoad(C.byref(module),str(out/'phase4_probe.hsaco').encode()))
def alloc(a):
 p=Q();check(d.cuMemAlloc_v2(C.byref(p),a.nbytes));check(d.cuMemcpyHtoD_v2(p,a.ctypes.data,a.nbytes));return p
def run(name,arrays,result,nb):
 args=[alloc(a) for a in arrays];p=alloc(result);args+=[p,U(nb)];argv=(P*len(args))(*[C.cast(C.pointer(x),P) for x in args]);f=P();check(d.cuModuleGetFunction(C.byref(f),module,name.encode()));check(d.cuLaunchKernel(f,nb,1,1,32,1,1,0,None,argv,None));check(d.cuCtxSynchronize());check(d.cuMemcpyDtoH_v2(result.ctypes.data,p,result.nbytes));return result
orig=np.fromfile(out/'original.bin',np.uint8);packed=np.fromfile(out/'packed.bin',np.uint8);r=run('permute',[orig,packed],np.zeros((64,32,10),np.uint32),64)
perm_diff=int(np.count_nonzero(r[:,:,:4]!=r[:,:,4:8]));assert perm_diff==0;assert np.array_equal(r[:,:,8:].copy().view(np.uint8).reshape(-1),packed)
rng=np.random.default_rng(42);x=rng.uniform(-4,4,(128,32,8)).astype(np.float16);x[:16]=rng.integers(-4,5,(16,32,8));x[64:]=np.abs(x[64:]);c=rng.uniform(-2,2,x.shape).astype(np.float32);c[:16]=rng.integers(-2,3,(16,32,8))
r=run('ones',[x,c],np.zeros((128,4,4,32,8),np.float32),128)
np.savez(out/'ones-data.npz',x=x,c=c,r=r)
stats={'tile256_prep_bitdiff':perm_diff,'tile512w16': 'pass'}
for name,ix in [('ones_a',0),('ones_b',2)]:
 a,b=r[:,:,ix],r[:,:,ix+1];delta=np.abs(a-b);ulp=np.abs(np.spacing(a.astype(np.float16)).astype(np.float32));stats[name]={'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'maxabs':float(delta.max()),'max_half_ulp':float(np.max(delta/np.maximum(ulp,2**-24))),'integer_bitdiff':int(np.count_nonzero(a[:16].view(np.uint32)!=b[:16].view(np.uint32))),'invalid':int(np.count_nonzero(~np.isfinite(b)))}
 assert stats[name]['integer_bitdiff']==0 and stats[name]['invalid']==0
 # The changed reduction order is measured, never silently treated as bit-exact.
aa=rng.uniform(-100,100,(128,32,8)).astype(np.float16).view(np.uint32);bb=rng.uniform(-100,100,(128,32,8)).astype(np.float16).view(np.uint32)
add=run('packed_add',[aa,bb],np.zeros((128,32,8),np.uint32),128)
stats['packed_add_bitdiff']=int(np.count_nonzero(add[:,:,:4]!=add[:,:,4:]))
assert stats['packed_add_bitdiff']==0
assert stats['ones_a']['bitdiff']==0 and stats['ones_b']['bitdiff']==0
counter=run('seeded_partition_counterexample',[],np.zeros((32,16),np.float32),1)
assert np.all(counter[:,:8]==1) and np.all(counter[:,8:]==0)
stats['seeded_partition_counterexample']={'separate_total':1,'seeded_total':0,'different_outputs':256}
print(json.dumps(stats,indent=2));(root/'phase4/primitive-results.json').write_text(json.dumps(stats,indent=2)+'\n')
