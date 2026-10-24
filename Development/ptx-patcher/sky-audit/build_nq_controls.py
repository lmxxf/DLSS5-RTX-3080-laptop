"""Control variables: strict/multidef-only eligibility, no mapped quantization."""
from pathlib import Path
import sys,collections,concurrent.futures,hashlib,json
from build_safe import b
from pe_fatbins import assemble
from ptx_mapped import instructions,Sources
ROOT=Path('/mnt/c/DLSS5-5090-dll')
original_sources=b.dp.fp8_pack_sources

def multidef_sources(text):
 defs=collections.Counter(r for _,_,_,rs,_ in instructions(text) for r in rs)
 downs=collections.defaultdict(list);packs=collections.defaultdict(list)
 for m in b.dp.FP8_DOWN_PATTERN.finditer(text):downs[m['destination']].append(m)
 for p in b.dp.FP8_PACK_PATTERN.finditer(text):packs[p['destination']].append(p)
 out=Sources();out.until={}
 for r,ps in packs.items():
  if len(ps)!=1 or defs[r]!=1:continue
  p=ps[0]
  if p['guard']:continue
  ds=[downs[p[k]] for k in ['low','high']]
  if any(len(v)!=1 or defs[p[k]]!=1 for k,v in zip(['low','high'],ds)):continue
  lo,hi=[v[0] for v in ds]
  if any(d['guard'] or defs[d['source']]!=1 or d.end()>p.start() for d in (lo,hi)):continue
  out[r]=(lo['source'],hi['source'],p.start())
 return out

def no_quant(mapped,operands):
 return [],{s:s for r in operands if r in mapped for s in mapped[r][:2]}
b.fast_mapped_fp16_sources=no_quant

def work(task):
 variant,i,blob=task
 b.dp.fp8_pack_sources=original_sources if variant=='strict_nq' else multidef_sources
 i,fb,msg=b.worker_compile_fatbin((i,blob,True,True,"strict" if variant=="strict_nq" else "multidef",False))
 path=Path(f'/tmp/dlss-sky-audit/{variant}');path.mkdir(exist_ok=True)
 (path/f'fatbin{i:02d}.bin').write_bytes(fb)
 return variant,i,len(fb),msg

if __name__=='__main__':
 data=bytearray((ROOT/'nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(data);locs=b.dp.find_fatbins(data)
 tasks=[(v,i,bytes(data[l.offset:l.offset+l.size])) for i,l in enumerate(locs[:6]) for v in ['strict_nq','multidef_nq']]
 # Six workers: compile both controls while caching unchanged non-network blobs.
 with concurrent.futures.ProcessPoolExecutor(max_workers=6) as pool:
  for f in concurrent.futures.as_completed([pool.submit(work,t) for t in tasks]):
   v,i,size,msg=f.result();print(v,i,msg,flush=True)
 b.dp.apply_host_patches(data,(b.dp.AMPERE,))
 for v in ['strict_nq','multidef_nq']:
  blobs={i:(Path(f'/tmp/dlss-sky-audit/{v}/fatbin{i:02d}.bin') if i<6 else Path(f'/tmp/dlss-sky-audit/safe-o4/fatbin{i:02d}.bin')).read_bytes() for i in range(15)}
  out,manifest=assemble(data,locs,blobs,b.dp);b.fast_update_pe_checksum(out)
  (ROOT/f'nvngx_dlssnr_sm86_{v}.dll').write_bytes(out)
  Path(__file__).with_name(v+'-manifest.json').write_text(json.dumps(manifest,indent=2))
  print(v,'15/15 O4','overflow',[x[0] for x in manifest if x[1]=='section'],'SHA256',hashlib.sha256(out).hexdigest(),flush=True)
