import sys,re,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dlssnr_patcher as d
from ptx_mapped import safe_sources
def legacy_sources(text):
 downs=collections.defaultdict(list);packs=collections.defaultdict(list)
 for m in d.FP8_DOWN_PATTERN.finditer(text):downs[m["destination"]].append(m["source"])
 for m in d.FP8_PACK_PATTERN.finditer(text):
  lo,hi=downs[m["low"]],downs[m["high"]]
  if len(lo)==len(hi)==1:packs[m["destination"]].append((lo[0],hi[0],m.start()))
 return {r:vs[0] for r,vs in packs.items() if len(vs)==1}
for i in range(7):
 text=Path('/tmp/dlss-sky-audit/fatbin%02d.ptx'%i).read_text();counts=collections.Counter();uses=collections.Counter();example=[]
 for e in re.split(r'(?m)^\s*(?:\.visible\s+)?\.entry\b',text)[1:]:
  old=legacy_sources(e);safe=safe_sources(e,d.FP8_DOWN_PATTERN,d.FP8_PACK_PATTERN);counts.update(safe.reasons);counts['safe_pack']+=len(safe)
  for m in d.FP8_MMA_PATTERN.finditer(e):
   for k in ['a0','a1','a2','a3','b0','b1']:
    r=m[k]
    if r not in old or old[r][2]>=m.start():continue
    reason=safe.rejected.get(r)
    if not reason:reason='safe_use' if old[r][2]<m.start()<safe.until[r] else 'cross_block_use'
    uses[reason]+=1
  if '%r1352' in safe.rejected and 'cc_vit_attention_fp8' in e[:2000]:example.append(('%r1352',safe.rejected['%r1352'],safe.defs['%r1352']))
 print(i,'packs',dict(counts),'uses',dict(uses),'example',example,flush=True)
