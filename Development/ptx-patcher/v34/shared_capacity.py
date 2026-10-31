from pathlib import Path
import sys,re,json,ctypes as c
from analysis_common import entries
p=Path(__file__).resolve().parent;res=json.loads((p.parent/'v33/resources.json').read_text())['baseline'];cu=c.CDLL('/usr/lib/wsl/lib/libcuda.so.1')
def ck(n):assert n==0,n
ck(cu.cuInit(0));dev=c.c_int();ck(cu.cuDeviceGet(c.byref(dev),0));ctx=c.c_void_p();ck(cu.cuCtxCreate_v2(c.byref(ctx),0,dev));attrs={}
for name,id in [('shared_per_sm',81),('shared_per_block_default',8),('shared_per_block_optin',97),('driver_reserved_shared_per_block',111)]:
 v=c.c_int();ck(cu.cuDeviceGetAttribute(c.byref(v),id,dev));attrs[name]=v.value
rows={}
for fb in range(1,7):
 mod=c.c_void_p();ck(cu.cuModuleLoad(c.byref(mod),str(p/f'artifacts/baseline/fatbin{fb:02}.cubin').encode()));parts=dict(entries((p/f'artifacts/raw/fb{fb:02}.ptx').read_text()))
 for name,r in res.items():
  if r['FB']!=fb:continue
  declarations=[]
  for m in re.finditer(r'\.shared\s+(?:\.align\s+\d+\s+)?\.(b|u|s|f)(\d+)\s+(\S+?)(?:\[(\d*)\])?\s*;',parts[name]):
   size=int(m[2])//8*int(m[4] or '1');declarations.append({'symbol':m[3],'bytes':size,'payload':size>32 and not re.search(r'barrier|mbarrier',m[3],re.I)})
  extra=sum(d['bytes'] for d in declarations if d['payload']);fn=c.c_void_p();ck(cu.cuModuleGetFunction(c.byref(fn),mod,name.encode()));threads=r['threads']
  def occ(dynamic):
   v=c.c_int();ret=cu.cuOccupancyMaxActiveBlocksPerMultiprocessor(c.byref(v),fn,threads,c.c_size_t(dynamic));return {'returncode':ret,'CTA_per_SM':v.value}
  base=occ(r['dynamic_shared']);assert base['CTA_per_SM']==r['resident_CTA_per_SM'];default=occ(r['dynamic_shared']+extra)
  setret=cu.cuFuncSetAttribute(fn,8,extra) if extra else 0;optin=occ(r['dynamic_shared']+extra) if setret==0 else None
  rows[name]={'FB':fb,'threads':threads,'REG':r['REG'],'cubin_static_shared_bytes':r['SHARED'],'declared_arrays':declarations,'expanded_payload_extra_bytes':extra,'hypothetical_total_shared_per_CTA':r['SHARED']+extra,'baseline':base,'double_payload_default_attribute':default,'set_max_dynamic_shared_returncode':setret,'double_payload_optin':optin,'current_residency_preserved_with_optin':optin is not None and optin['returncode']==0 and optin['CTA_per_SM']>=base['CTA_per_SM'],'scope':'counterfactual resource query: add payload bytes as dynamic Shared to actual baseline cubin, static registers and block kept fixed; no layout rewrite or speed claim'}
 ck(cu.cuModuleUnload(mod))
ck(cu.cuCtxDestroy_v2(ctx));out={'device':attrs,'kernels':rows,'all_doubled_payload_fit_current_residency':all(r['current_residency_preserved_with_optin'] for r in rows.values()),'scope':'includes FB06 appendix; CUDA API includes allocation/reserved resource constraints; not naive 101376/CTA division'};(p/'shared-capacity-api.json').write_text(json.dumps(out,indent=2)+'\n');print(attrs)
for fb in range(1,7):
 a=[r for r in rows.values() if r['FB']==fb];print(fb,[(r['cubin_static_shared_bytes'],r['expanded_payload_extra_bytes'],r['baseline']['CTA_per_SM'],r['double_payload_optin']) for r in a])
