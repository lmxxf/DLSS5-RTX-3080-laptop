from pathlib import Path
import sys,subprocess,ctypes as C,numpy as np,json,hashlib
p=Path(__file__).resolve().parent;r=p.parent;art=p/'artifacts/single';art.mkdir(parents=True,exist_ok=True)
subprocess.run(['c++','-O2','-std=c++17','-I'+str(r/'Development/HIP'),str(p/'single_kernel_weights.cpp'),'-ldl','-o',str(art/'prepare')],check=True);subprocess.run([str(art/'prepare'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/small',str(art)],check=True)
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;Q=C.c_uint64;U=C.c_uint
for n,t in {'cuInit':[U],'cuDeviceGet':[C.POINTER(C.c_int),C.c_int],'cuCtxCreate_v2':[C.POINTER(P),U,C.c_int],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuMemAlloc_v2':[C.POINTER(Q),C.c_size_t],'cuMemcpyHtoD_v2':[Q,P,C.c_size_t],'cuMemcpyDtoH_v2':[P,Q,C.c_size_t],'cuLaunchKernel':[P,U,U,U,U,U,U,U,P,P,P]}.items():getattr(d,n).argtypes=t
def ck(x):assert x==0,x
ck(d.cuInit(0));dev=C.c_int();ck(d.cuDeviceGet(C.byref(dev),0));ctx=P();ck(d.cuCtxCreate_v2(C.byref(ctx),0,dev));mods=[]
for base in [r/'phase16/artifacts/tail/modules',p/'artifacts/candidate/modules']:
 m=P();ck(d.cuModuleLoad(C.byref(m),str(base/'c32-wave1-fast.hsaco').encode()));mods.append(m)
def alloc(a):
 a=np.ascontiguousarray(a);q=Q();ck(d.cuMemAlloc_v2(C.byref(q),a.nbytes));ck(d.cuMemcpyHtoD_v2(q,a.ctypes.data,a.nbytes));return q
cache={}
def weight(name,v=0):
 n=name+(f'.v{v+2}.bin' if name.endswith(('-ffn.f32','-attention.f32')) else '.bin')
 if n not in cache:cache[n]=alloc(np.fromfile(art/n,np.uint8))
 return cache[n]
rng=np.random.default_rng(1717);W=H=64;win=64;rgba=alloc(rng.uniform(0,1,(H,W,4)).astype(np.float32));features=alloc(rng.choice(np.array([0,128,0x20,0xa0,0x30,0xb0],np.uint8),(H,W,32)));lowfp8=alloc(rng.choice(np.array([0,0x20,0xa0,0x28,0xa8],np.uint8),(H//2,W//2,32)));lowf32=alloc(rng.uniform(-1,1,(H//2,W//2,64)).astype(np.float32));null=Q(0);rows=[]
def compare(kernel,prefix,sizes,make):
 outputs=[]
 for v in [0,1]:
  bufs=[np.full(n,0xa5,np.uint8) for n in sizes];ptrs=[alloc(a) for a in bufs];fw=weight(prefix+'-ffn.f32',v);aw=weight(prefix+'-attention.f32',v);args=make(fw,aw,ptrs);argv=(P*len(args))(*[C.cast(C.pointer(a),P) for a in args]);fn=P();name=('v3_' if v else '')+kernel+'_w16';ck(d.cuModuleGetFunction(C.byref(fn),mods[v],name.encode()));ck(d.cuLaunchKernel(fn,win,1,1,32,1,1,0,None,argv,None));ck(d.cuCtxSynchronize())
  for a,q in zip(bufs,ptrs):ck(d.cuMemcpyDtoH_v2(a.ctypes.data,q,a.nbytes))
  outputs.append(bufs)
 for a,b in zip(*outputs):assert np.array_equal(a,b),kernel
 rows.append({'kernel':kernel,'block_weights':prefix,'CTAs':win,'output_bytes':sum(sizes),'byte_diff':0,'changed_from_sentinel':sum(int(np.count_nonzero(a!=0xa5)) for a in outputs[0]),'output_sha256':[hashlib.sha256(a.tobytes()).hexdigest() for a in outputs[0]]})
 return alloc(outputs[0][0])
raw=compare('c32_wave1_mapped_b8','block1',[W*H*32],lambda fw,aw,o:[features,fw,aw,o[0],U(win),U(0),U(1),U(W),U(H),U(0),U(0)])
compare('c32_wave1_prefix_b8d','block0',[W*H*32,W*H*8],lambda fw,aw,o:[rgba,null,fw,aw,o[0],o[1],U(win),U(0),U(1),U(W),U(H),U(0),U(0)])
compare('c32_wave1_finish_dcrop_b8d','block4',[W*H*32,W*H*8],lambda fw,aw,o:[raw,fw,aw,o[0],o[1],U(win),U(3),U(1),U(W),U(H),U(0),U(0),U(W),U(0),U(0)])
compare('c32_wave1_finish_b8','block69',[W*H*32],lambda fw,aw,o:[raw,fw,aw,o[0],null,U(win),U(3),U(1),U(W),U(H),U(0),U(0),U(W),U(0),U(0)])
compare('c32_wave1_up_b8','block66',[W*H*32],lambda fw,aw,o:[lowf32,weight('up'),features,fw,aw,o[0],U(win),U(W),U(H),U(0),U(0)])
compare('c32_wave1_post_b8','post70',[W*H*3*4],lambda fw,aw,o:[lowfp8,features,weight('post70-scales.f32'),fw,aw,rgba,weight('post70-head.f32'),o[0],U(win),U(W),U(H),U(0),U(0),C.c_float(.03125)])
print('written-byte fractions:',[(x['kernel'],x['changed_from_sentinel'],x['output_bytes']) for x in rows],flush=True)
assert all(x['changed_from_sentinel']>x['output_bytes']*.9 for x in rows)
(p/'single-kernel-results.json').write_text(json.dumps({'scope':'six isolated C32 W16 kernels,actual Small model weights,matched full synthetic inputs,64 CTAs per kernel,not game captures','results':rows},indent=2)+'\n');print('PASS six isolated C32 kernels:all output bytes0diff with actual model weights')
