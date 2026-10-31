"""Re-run source lowering only; stop before CUDA compilation/context creation."""
from pathlib import Path
import sys,json,re
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));sys.path.insert(0,str(p.parent))
import build as build
from ptx_mapped import mapped_at
class StopLowering(Exception):pass
def stop(text,limit):raise StopLowering()
build.stock=stop
raw=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes());build.b.dp.strip_authenticode(raw);locs=build.b.dp.find_fatbins(raw);build.b.dp.apply_host_patches(raw,(build.b.dp.AMPERE,))
orig=build.RENDER;split=build.split.render;allrows={}
for mode,renderer in [('baseline',orig),('split',split)]:
 rows=[]
 def record(matches,packed_sources,*,builder,audit=None):
  target=[];result=renderer(matches,packed_sources,builder=builder,audit=target);r=target[0]
  text=matches[0].string[:matches[0].start()];names=re.findall(r'\.visible \.entry (\w+)',text)
  r['kernel']=names[-1] if names else 'unknown';r['FB']=fb
  operands={m[n] for m in matches for n in ('a0','a1','a2','a3','b0','b1')};mapped=mapped_at(packed_sources,matches[0].start());encoded=operands-set(mapped)
  counts={r:sum(r in {m[n] for n in ('a0','a1','a2','a3','b0','b1')} for m in matches) for r in encoded}
  r['single_use_encoded_operands']=sum(v==1 for v in counts.values());rows.append(r)
  if audit is not None:audit.extend(target)
  return result
 build.MODE=mode
 if mode=='baseline':build.RENDER=record
 else:build.split.render=record
 for fb,l in enumerate(locs[:7]):
  task=(fb,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',build.selected['base_caps'].get(str(fb)),'swar','mbarrier','lowhigh8',8)
  try:build.worker(task)
  except StopLowering:pass
 allrows[mode]=rows;print(mode,len(rows),max(r['temporary_b32_peak'] for r in rows),list({r['kernel'] for r in rows})[:2],flush=True)
(p/'source-pools.json').write_text(json.dumps(allrows,indent=2)+'\n')
