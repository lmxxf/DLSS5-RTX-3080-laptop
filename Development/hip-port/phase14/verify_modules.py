"""Load every final cubin and resolve every PTX entry, even on builder cache hits."""
from pathlib import Path
import argparse,ctypes as C,re,json,hashlib
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--modules',type=Path,default=root/'phase14/artifacts/selected/modules');a=p.parse_args()
d=C.CDLL('/usr/lib/wsl/lib/libcuda.so.1');P=C.c_void_p;I=C.c_int;U=C.c_uint
for n,t in {'cuInit':[U],'cuDeviceGet':[C.POINTER(I),I],'cuCtxCreate_v2':[C.POINTER(P),U,I],'cuModuleLoad':[C.POINTER(P),C.c_char_p],'cuModuleGetFunction':[C.POINTER(P),P,C.c_char_p],'cuModuleUnload':[P]}.items():getattr(d,n).argtypes=t
def check(x):assert x==0,x
check(d.cuInit(0));dev=I();check(d.cuDeviceGet(C.byref(dev),0));ctx=P();check(d.cuCtxCreate_v2(C.byref(ctx),0,dev));rows=[]
for f in sorted(a.modules.glob('*.hsaco')):
 names=re.findall(r'\.visible\s+\.entry\s+(\w+)\s*\(',f.with_suffix('.ptx').read_text());mod=P();check(d.cuModuleLoad(C.byref(mod),str(f.resolve()).encode()))
 for n in names:fn=P();check(d.cuModuleGetFunction(C.byref(fn),mod,n.encode()))
 check(d.cuModuleUnload(mod));rows.append({'module':f.name,'entries':len(names),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
assert len(rows)==40 and sum(r['entries'] for r in rows)==1918
(a.modules.parent/'cuda-load-verification.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS: actually CUDA loaded 40/40 modules; resolved1918 entries')
