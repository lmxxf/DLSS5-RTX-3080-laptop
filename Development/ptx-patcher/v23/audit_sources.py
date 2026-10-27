from pathlib import Path
import sys,json,re,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from ptx_mapped import mapped_at,instructions
profile=json.loads((p/'profile.json').read_text());active={r['name'] for w in profile.values() for r in w['calls']};result={}
for i in range(7):
 s=(p/f'artifacts/raw/fb{i:02}.ptx').read_text();entries=re.split(r'(?=\.visible \.entry )',s)[1:];rows={}
 for text in entries:
  name=re.match(r'\.visible \.entry (\w+)',text)[1]
  if name not in active:continue
  sources=b.stock_pack_sources(text,local_only=False);matches=list(b.dp.FP8_MMA_PATTERN.finditer(text));stats=collections.Counter()
  for m in matches:
   mapping=mapped_at(sources,m.start())
   for r in set(m[n] for n in ('a0','a1','a2','a3','b0','b1')):
    stats['mma_unique_operand_uses']+=1
    if r in mapping:stats['forwarded_operand_uses']+=1
    elif r in sources.rejected:stats['rejected_use_'+sources.rejected[r]]+=1
    else:stats['other_encoded_operand_uses']+=1
  rows[name]={'raw_mma_sites':len(matches),'mapped_pack_candidates':len(sources)+sum(sources.reasons.values()),'accepted_packs':len(sources),'rejected_packs':dict(sources.reasons),'operand_uses':dict(stats),'nanosleep_sites':text.count('nanosleep.'),'fence_sites':len(re.findall(r'\bfence\.',text)),'relaxed_global_poll_loads':len(re.findall(r'ld\.relaxed\.gpu\.global',text))}
 result[str(i)]=rows
(p/'mapped-sync-audit.json').write_text(json.dumps(result,indent=2)+'\n');tot=collections.Counter()
for rows in result.values():
 for name,r in rows.items():tot.update(r['operand_uses'])
print(dict(tot))
