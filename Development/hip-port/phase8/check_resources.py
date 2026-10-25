from pathlib import Path
import ctypes as C,json,sys
root=Path(__file__).resolve().parent
D=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;I=C.c_int
for n,a in {'cuInit':[C.c_uint],'cuDeviceGet':[C.POINTER(I),I],'cuCtxCreate_v2':[C.POINTER(P),C.c_uint,I],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuFuncGetAttribute':[C.POINTER(I),I,P],'cuOccupancyMaxActiveBlocksPerMultiprocessor':[C.POINTER(I),P,I,C.c_size_t]}.items():getattr(D,n).argtypes=a
def ok(v):assert v==0,v
ok(D.cuInit(0));d=I();ok(D.cuDeviceGet(C.byref(d),0));ctx=P();ok(D.cuCtxCreate_v2(C.byref(ctx),0,d));rows=[]
for module,names,threads in [('c32-wave1-fast',['c32_wave1_prefix_b8d_w16','c32_wave1_mapped_b8_w16','c32_wave1_post_b8_w16','c32_wave1_up_b8_w16'],32),('c512-m32-deep',['split_ffn_one_w2f8_w16','split_ffn_one_w2f8_w16_bin'],64),('vit-stream-fast',['vit_stream_project_n64_bb_bout_compactw_w16'],32),('c64-wave2-fast',['c64_wave2_bi_bo_w16'],64),('c64-wave2-fast',['c128_wave2_bi_bo_w16'],128),('c64-wave2-fast',['c256_wave2_bi_bo_w16'],256)]:
 p=root/'artifacts'/(sys.argv[1] if len(sys.argv)>1 else 'full')/'modules'/(module+'.hsaco')
 if not p.exists():continue
 m=P();ok(D.cuModuleLoad(C.byref(m),str(p).encode()))
 for name in names:
  f=P();ok(D.cuModuleGetFunction(C.byref(f),m,name.encode()));r={'module':module,'kernel':name}
  for k,a in [('regs',4),('lmem',3),('smem',1)]:
   x=I();ok(D.cuFuncGetAttribute(C.byref(x),a,f));r[k]=x.value
  x=I();ok(D.cuOccupancyMaxActiveBlocksPerMultiprocessor(C.byref(x),f,threads,0));r['occw']=x.value*threads//32;rows.append(r)
print(json.dumps(rows,indent=2));(root/((sys.argv[1] if len(sys.argv)>1 else 'full')+'-resources.json')).write_text(json.dumps(rows,indent=2)+'\n')
