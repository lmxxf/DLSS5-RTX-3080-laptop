from pathlib import Path
import ctypes as C,sys,json,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
from phase11_transform import HALF_PACK_HELPER
from phase12_transform import ADAPTER
from phase20_transform import helper
orig=b.assemble_module_source;b.assemble_module_source=lambda *a,**k:orig(*a,**k).replace('using U=unsigned;',HALF_PACK_HELPER+ADAPTER+helper()+'\nusing U=unsigned;');out=p/'artifacts/probe';out.mkdir(parents=True,exist_ok=True)
res=b.compile_one_module({'name':'actprobe','sources':['../phase20/probe.hip'],'defines':[],'l23defines':[]},str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res
D=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;Q=C.c_uint64;U=C.c_uint
for n,t in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P]}.items():getattr(D,n).argtypes=t
def ck(x):assert x==0,x
ck(D.cuInit(0));dev=C.c_int();ck(D.cuDeviceGet(C.byref(dev),0));ctx=P();ck(D.cuCtxCreate_v2(C.byref(ctx),0,dev));m=P();ck(D.cuModuleLoad(C.byref(m),str(out/'actprobe.hsaco').encode()));f=P();ck(D.cuModuleGetFunction(C.byref(f),m,b'actprobe'));data=np.zeros((65536,4),np.uint32);ptr=Q();ck(D.cuMemAlloc_v2(C.byref(ptr),data.nbytes));finite=np.isfinite(np.arange(65536,dtype=np.uint16).view(np.float16));idx=np.arange(256,dtype=np.int32);exp=(idx&127)>>3;mag=np.where(exp==0,(idx&7)*2.**-9,(1+(idx&7)/8)*2.**(exp-7));lut=np.where(idx&128,-mag,mag);rows={}
for mode,name in [(0,'C32'),(1,'Wave2')]:
 a=[ptr,U(mode)];args=(P*2)(*[C.cast(C.pointer(x),P) for x in a]);ck(D.cuLaunchKernel(f,2048,1,1,32,1,1,0,None,args,None));ck(D.cuCtxSynchronize());ck(D.cuMemcpyDtoH_v2(data.ctypes.data,ptr,data.nbytes));old=data[:,:2].copy().view(np.uint8);new=data[:,2:].copy().view(np.uint8);diff=np.any(old!=new,axis=1);delta=abs(lut[old]-lut[new]);rows[name]={'half_patterns_tested':65536,'finite_half_count':int(finite.sum()),'finite_input_changed_count':int(np.count_nonzero(diff&finite)),'finite_changed_fraction':float(np.mean(diff[finite])),'finite_max_output_value_error':float(delta[finite].max()),'finite_max_magnitude_code_distance':int(abs((old[finite].astype(int)&127)-(new[finite].astype(int)&127)).max()),'nonfinite_changed_count':int(np.count_nonzero(diff&~finite))};print(name,rows[name],flush=True)
(p/'primitive-results.json').write_text(json.dumps(rows,indent=2)+'\n')
