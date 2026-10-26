from pathlib import Path
import sys,subprocess,ctypes as C,json,hashlib,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;art=p/'artifacts/probe';art.mkdir(parents=True,exist_ok=True)
subprocess.run(['c++','-O2','-std=c++17','-I'+str(r/'Development/HIP'),str(p/'host_probe.cpp'),'-o',str(art/'host')],check=True)
subprocess.run([str(art/'host'),str(art)],check=True)
sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
mod={'name':'phase17_probe','sources':['../phase17/probe.hip'],'defines':['PHASE17_HEADER "'+str(r/'hip/phase17_c32_half.h')+'"'],'l23defines':['PHASE17_HEADER_SHA '+hashlib.sha256((r/'hip/phase17_c32_half.h').read_bytes()).hexdigest()]};res=b.compile_one_module(mod,str(r/'hip'),str(art),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));assert res[1],res
D=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;U=C.c_uint;Q=C.c_uint64
for n,t in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P]}.items():getattr(D,n).argtypes=t
def ck(x):assert x==0,x
ck(D.cuInit(0));dev=C.c_int();ck(D.cuDeviceGet(C.byref(dev),0));ctx=P();ck(D.cuCtxCreate_v2(C.byref(ctx),0,dev));m=P();ck(D.cuModuleLoad(C.byref(m),str(art/'phase17_probe.hsaco').encode()))
def run(name,arr,result):
 args=[]
 for a in arr+[result]:
  ptr=Q();ck(D.cuMemAlloc_v2(C.byref(ptr),a.nbytes));ck(D.cuMemcpyHtoD_v2(ptr,a.ctypes.data,a.nbytes));args.append(ptr)
 out=args[-1];args.append(U(len(result)));argv=(P*len(args))(*[C.cast(C.pointer(x),P) for x in args]);f=P();ck(D.cuModuleGetFunction(C.byref(f),m,name.encode()));ck(D.cuLaunchKernel(f,len(result)//32,1,1,32,1,1,0,None,argv,None));ck(D.cuCtxSynchronize());ck(D.cuMemcpyDtoH_v2(result.ctypes.data,out,result.nbytes))
 for a in args[:-1]:ck(D.cuMemFree_v2(a))
 return result
lut=np.fromfile(art/'half-table.bin',np.uint16);src=(np.arange(4096*8,dtype=np.uint32)*37+np.arange(4096*8,dtype=np.uint32)//256).astype(np.uint8).reshape(4096,8);half=lut[src];result=run('decode',[src,half],np.zeros((4096,8),np.uint32));assert np.array_equal(result[:,:4],result[:,4:])
rng=np.random.default_rng(17);src=rng.choice(np.array([0,128,0x18,0x98,0x28,0xa8,0x38,0xb8],np.uint8),(4096,8));dyn=rng.choice(np.array([0,0x20,0xa0,0x30,0xb0],np.uint8),(4096,8));c=rng.uniform(-2,2,(4096,8)).astype(np.float16).astype(np.float32);result=run('mma',[src,lut[src],dyn,c],np.zeros((4096,32),np.float32));assert np.array_equal(result[:,:8].view(np.uint32),result[:,8:16].view(np.uint32));assert np.array_equal(result[:,16:24].view(np.uint32),result[:,24:32].view(np.uint32))
(p/'primitive-results.json').write_text(json.dumps({'decoder_positions':4096*8,'host_old_bytes_preserved':True,'all256_byte_decoder_patterns_including_reserved_finite_shortcut':True,'MMA_A_and_B_output_elements':4096*8*2,'MMA_accumulation_steps':4,'bitdiff':0,'scope':'existing finite shortcut for7f/ff,not IEEE NaN support'},indent=2)+'\n');print('PASS host append offsets/old bytes,GPU all byte decoder slots,two static MMA sides')
