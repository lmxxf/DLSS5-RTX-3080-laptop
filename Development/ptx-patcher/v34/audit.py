"""Data-first audit: exact launched FP8 set, machine instructions and official occupancy."""
from pathlib import Path
import sys,json,re,subprocess,ctypes as c,math
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b
import v26.codegen as old
import v32.codegen as split
prof=json.loads((p.parent/'v23/profile.json').read_text());active={r['name']:r for w in prof.values() for r in w['calls'] if r['FB']<7}
tool='/home/lmxxf/.local/lib/python3.10/site-packages/triton/backends/nvidia/bin/cuobjdump'
cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(r):assert r==0,r
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev))
rows={}
for mode in sys.argv[1:] or json.loads((p/'candidates.json').read_text()):
 kernels={}
 for fb in range(7):
  f=p/f'artifacts/{mode}/fatbin{fb:02}.cubin';mod=c.c_void_p();ck(cu.cuModuleLoad(c.byref(mod),str(f).encode()))
  res=subprocess.check_output([tool,'-res-usage',str(f)],text=True);sass=subprocess.check_output([tool,'-sass',str(f)],text=True)
  for m in re.finditer(r'Function\s+(\S+):\s*(.*)',res):
   if m[1] not in active:continue
   r={'FB':fb,**{k:int(v) for k,v in re.findall(r'(REG|STACK|SHARED|LOCAL):(\d+)',m[2])}}
   call=active[m[1]];threads=math.prod(call['block']);fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,m[1].encode()));blocks=c.c_int();ck(cu.cuOccupancyMaxActiveBlocksPerMultiprocessor(c.byref(blocks),fn,threads,c.c_size_t(call['dynamic_shared'])))
   r|={'threads':threads,'dynamic_shared':call['dynamic_shared'],'resident_CTA_per_SM':blocks.value,'resident_warps_per_SM':blocks.value*threads//32,'grids':{w:next((q['grid'] for q in v['calls'] if q['name']==m[1]),None) for w,v in prof.items()}};kernels[m[1]]=r
  for part in re.split(r'Function : ',sass)[1:]:
   n=part.splitlines()[0].strip()
   if n not in kernels:continue
   ops=re.findall(r'/\*[0-9a-f]+\*/\s+(?:@!?P\d+\s+)?([A-Z][A-Z0-9_.]*)',part);r=kernels[n];r['INSN_WITH_NOP']=len(ops);r['INSN_NONOP']=sum(op!='NOP' for op in ops)
   for op in ['HMMA','PRMT','LDL','STL','SHF','LOP3','SHFL','HMUL2','LDGSTS','BAR','WARPSYNC','CALL','RET']:r[op]=sum(x.split('.')[0]==op for x in ops)
  ck(cu.cuModuleUnload(mod))
 assert len(kernels)==38,len(kernels)
 rows[mode]=kernels
 print(mode,{k:sum(r[k] for r in kernels.values()) for k in ['INSN_NONOP','HMMA','PRMT','STL','LDL','SHFL']},flush=True)
prior=json.loads((p/'resources.json').read_text()) if (p/'resources.json').exists() else {};prior.update(rows);(p/'resources.json').write_text(json.dumps(prior,indent=2)+'\n');ck(cu.cuCtxDestroy_v2(ctx))
