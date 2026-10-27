from pathlib import Path
import sys,re,json,collections
from functools import partial
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from codegen import render
from v24.codegen import jit_render
from v23.decode import decode
b.dp.fp8_pack_sources=partial(b.stock_pack_sources,local_only=False);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources;b.even_odd_decode_lines=decode
out={}
for fb in range(7):
 text=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text();peak_old=peak_new=0;total=collections.Counter();kernels={}
 for entry in re.split(r'(?=\.visible \.entry )',text)[1:]:
  name=re.match(r'\.visible \.entry (\w+)',entry)[1];ms=list(b.dp.FP8_MMA_PATTERN.finditer(entry))
  if not ms:continue
  groups=[[ms[0]]]
  for m in ms[1:]:
   if entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  sources=b.dp.fp8_pack_sources(entry);ks=collections.Counter()
  for group in groups:
   old=jit_render(group,sources,builder=b);audit=[];new=render(group,sources,builder=b,audit=audit);a=audit[0]
   assert old.count('mma.sync')==new.count('mma.sync')==2*len(group);assert '0x5410' not in new and '0x7632' not in new
   old_peak=len(set(re.findall(r'vp_\d+_[01]',old)));peak_old=max(peak_old,old_peak);peak_new=max(peak_new,a['temporary_b32_peak'])
   ks.update({k:a[k] for k in ['mma_sites','mapped_operands','encoded_operands','backup_moves']});ks['runs']+=1;ks['old_mapped_PRMT']+=old.count('0x5410')+old.count('0x7632')
  kernels[name]=dict(ks);total.update(ks)
 ptx=(p/f'artifacts/decode/fatbin{fb:02}.ptx').read_text();out[str(fb)]={'max_old_pool_b32':peak_old,'max_new_temporary_b32':peak_new,'totals':dict(total),'kernels':kernels,'whole_generated_selector_5410_count':ptx.count('0x5410'),'whole_generated_selector_7632_count':ptx.count('0x7632')};print(fb,peak_old,'->',peak_new,dict(total),flush=True)
(p/'codegen-audit.json').write_text(json.dumps(out,indent=2)+'\n')
