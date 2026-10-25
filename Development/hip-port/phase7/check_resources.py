from pathlib import Path
import ctypes as C,json,re,sys
root=Path(__file__).resolve().parent
D=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;I=C.c_int
for n,a in {'cuInit':[C.c_uint],'cuDeviceGet':[C.POINTER(I),I],'cuCtxCreate_v2':[C.POINTER(P),C.c_uint,I],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuFuncGetAttribute':[C.POINTER(I),I,P]}.items():getattr(D,n).argtypes=a
def ok(v):assert v==0,v
ok(D.cuInit(0));d=I();ok(D.cuDeviceGet(C.byref(d),0));ctx=P();ok(D.cuCtxCreate_v2(C.byref(ctx),0,d))
rows=[]
for v in sys.argv[1:]:
 path=root/'artifacts'/v/'modules/c32-wave1-fast.hsaco';m=P();ok(D.cuModuleLoad(C.byref(m),str(path).encode()))
 for name in ['c32_wave1_prefix_b8d_w16','c32_wave1_mapped_b8_w16','c32_wave1_post_b8_w16','c32_wave1_up_b8_w16']:
  f=P()
  if D.cuModuleGetFunction(C.byref(f),m,name.encode()):continue
  row={'variant':v,'kernel':name}
  for key,attr in [('regs',4),('lmem',3),('smem',1)]:
   val=I();ok(D.cuFuncGetAttribute(C.byref(val),attr,f));row[key]=val.value
  rows.append(row)
print(json.dumps(rows,indent=2))
