from pathlib import Path
import sys,re,json,collections
from functools import partial
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import jit_render,fuse_quads
from v23.decode import decode
b.dp.fp8_pack_sources=partial(b.stock_pack_sources,local_only=False);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources;b.dp.render_fp8_mma_run=b.fast_render_fp8_mma_run;b.even_odd_decode_lines=decode
result={}
for fb in range(7):
 text=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text();peakold=peaknew=runs=0
 for entry in re.split(r'(?=\.visible \.entry )',text):
  matches=list(b.dp.FP8_MMA_PATTERN.finditer(entry))
  if not matches:continue
  groups=[[matches[0]]]
  for m in matches[1:]:
   if entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  sources=b.dp.fp8_pack_sources(entry)
  for group in groups:
   old=b.fast_render_fp8_mma_run(group,sources);new=jit_render(group,sources,builder=b);assert old.count('mma.sync')==new.count('mma.sync')==2*len(group)
   oldregs=len(set(re.findall(r'dlssnr_fp16_\d+_[01]',old)));newregs=len(set(re.findall(r'vp_\d+_[01]',new)));peakold=max(peakold,oldregs);peaknew=max(peaknew,newregs);runs+=1
 lowered,n=b.dp.lower_fp8_mma(text);stats=b.dp.TransformStats();fused=fuse_quads(lowered,stats,True)
 result[str(fb)]={'runs':runs,'max_declared_decode_regs_upfront':peakold,'max_declared_decode_regs_pool':peaknew,'remaining_downs':len(b.dp.FP8_DOWN_PATTERN.findall(lowered)),'remaining_packs':len(b.dp.FP8_PACK_PATTERN.findall(lowered)),'quad_stats':stats.summary()}
 print(fb,result[str(fb)],flush=True)
(p/'codegen-audit.json').write_text(json.dumps(result,indent=2)+'\n')
