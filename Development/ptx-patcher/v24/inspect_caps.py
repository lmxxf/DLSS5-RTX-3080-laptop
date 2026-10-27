from pathlib import Path
import sys,json,re,subprocess,ctypes as c,math
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';prof=json.loads((p.parent/'v23/profile.json').read_text());active={r['name']:r for w in prof.values() for r in w['calls']}
cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(r):assert r==0,r
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev));result={}
cases=[('abc',i,None) for i in [1,2,4,5]]+[(n,r['FB'],r['cap']) for n,r in json.loads((p/'caps.json').read_text()).items()]
for tag,fb,cap in cases:
 path=p/f'artifacts/{tag}/fatbin{fb:02d}.cubin';res=subprocess.check_output([tool,'-res-usage',str(path)],text=True);sass=subprocess.check_output([tool,'-sass',str(path)],text=True);mod=c.c_void_p();ck(cu.cuModuleLoad(c.byref(mod),str(path).encode()));kernels={}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
  name=m[1]
  if name not in active:continue
  a={k:int(v) for k,v in re.findall(r'(REG|STACK|LOCAL|SHARED):(\d+)',m[2])};fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,name.encode()));blocks=c.c_int();block=active[name]['block'];threads=math.prod(block);ck(cu.cuOccupancyMaxActiveBlocksPerMultiprocessor(c.byref(blocks),fn,threads,c.c_size_t(active[name]['dynamic_shared'])));a|={'threads':threads,'resident_CTA_per_SM':blocks.value,'resident_warps_per_SM':blocks.value*threads//32}
  ch=next(ch for ch in sass.split('Function : ')[1:] if ch.splitlines()[0].strip()==name);a['LDL_STL']=len(re.findall(r'\b(?:LDL|STL)\b',ch));kernels[name]=a
 ck(cu.cuModuleUnload(mod));key=f'{tag}-fb{fb}';result[key]={'FB':fb,'cap':cap,'kernels':kernels};print(key,[(n,r['STACK'],r['resident_warps_per_SM']) for n,r in kernels.items()],flush=True)
(p/'caps-resources.json').write_text(json.dumps(result,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
