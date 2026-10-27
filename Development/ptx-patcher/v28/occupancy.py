from pathlib import Path
import json,subprocess,re,ctypes as c,math,sys
p=Path(__file__).resolve().parent;tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump';prof=json.loads((p.parent/'v23/profile.json').read_text());active={r['name']:r for w in prof.values() for r in w['calls']};cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(r):assert r==0,r
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev));rows={};attrs={}
for name,id in [('warp_size',10),('SM_count',16),('max_threads_per_SM',39),('shared_bytes_per_SM',81),('regs_per_SM',82),('max_CTA_per_SM',106)]:
 v=c.c_int();ck(cu.cuDeviceGetAttribute(c.byref(v),id,dev));attrs[name]=v.value
cases=[('baseline',i) for i in range(15)] if len(sys.argv)<2 else [(n,r['FB']) for n,r in json.loads((p/'candidates.json').read_text()).items()]
for tag,fb in cases:
 path=p/f'artifacts/{tag}/fatbin{fb:02}.cubin';text=subprocess.check_output([tool,'-res-usage',str(path)],text=True);mod=c.c_void_p();ck(cu.cuModuleLoad(c.byref(mod),str(path).encode()));kernels={}
 for m in re.finditer(r'Function\s+(\S+):\s*(.*)',text):
  if m[1] not in active:continue
  r={k:int(v) for k,v in re.findall(r'(REG|STACK|LOCAL|SHARED):(\d+)',m[2])};threads=math.prod(active[m[1]]['block']);fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,m[1].encode()));blocks=c.c_int();ck(cu.cuOccupancyMaxActiveBlocksPerMultiprocessor(c.byref(blocks),fn,threads,c.c_size_t(active[m[1]]['dynamic_shared'])));r|={'dynamic_shared':active[m[1]]['dynamic_shared'],'threads':threads,'resident_CTA_per_SM':blocks.value,'resident_warps_per_SM':blocks.value*threads//32,'naive_total_reg_CTA_bound':65536//(threads*(math.ceil(r['REG']/8)*8))};kernels[m[1]]=r
 ck(cu.cuModuleUnload(mod));rows[f'{tag}-fb{fb}']={'FB':fb,'kernels':kernels}
 if fb in [0,4,5]:print(tag,fb,[(n,r['REG'],r['STACK'],r['resident_CTA_per_SM'],r['resident_warps_per_SM']) for n,r in kernels.items()],flush=True)
(p/('occupancy-baseline.json' if len(sys.argv)<2 else 'occupancy-caps.json')).write_text(json.dumps({'device':attrs,'cases':rows,'scope':'CUDA API theoretical resident limit, not achieved dynamic occupancy'},indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
