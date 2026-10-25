import ctypes as C
import numpy as np
class CUDA:
 def __init__(self):
  self.d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;I=C.c_int;U=C.c_uint;Q=C.c_uint64
  specs={'cuInit':[U],'cuDeviceGet':[C.POINTER(I),I],'cuCtxCreate_v2':[C.POINTER(P),U,I],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuMemFree_v2':[Q],'cuModuleUnload':[P],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P],'cuCtxSynchronize':[]}
  for n,t in specs.items():getattr(self.d,n).argtypes=t
  self.ok(self.d.cuInit(0));dev=I();self.ok(self.d.cuDeviceGet(C.byref(dev),0));self.ctx=P();self.ok(self.d.cuCtxCreate_v2(C.byref(self.ctx),0,dev))
 def ok(self,r):assert r==0,r
 def load(self,p):m=C.c_void_p();self.ok(self.d.cuModuleLoad(C.byref(m),str(p).encode()));return m
 def alloc(self,a):q=C.c_uint64();self.ok(self.d.cuMemAlloc_v2(C.byref(q),a.nbytes));self.ok(self.d.cuMemcpyHtoD_v2(q,a.ctypes.data,a.nbytes));return q
 def run(self,m,name,args,grid,block=32):
  f=C.c_void_p();self.ok(self.d.cuModuleGetFunction(C.byref(f),m,name.encode()));argv=(C.c_void_p*len(args))(*[C.cast(C.pointer(a),C.c_void_p) for a in args]);self.ok(self.d.cuLaunchKernel(f,grid,1,1,block,1,1,0,None,argv,None));self.ok(self.d.cuCtxSynchronize())
 def read(self,p,a):self.ok(self.d.cuMemcpyDtoH_v2(a.ctypes.data,p,a.nbytes));return a
 def free(self,*p):
  for a in p:self.ok(self.d.cuMemFree_v2(a))
