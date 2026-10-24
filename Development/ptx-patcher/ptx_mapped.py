"""Conservative PTX def/use and basic-block eligibility for mapped FP8 pairs."""
import re,bisect,collections
REG=re.compile(r'%[A-Za-z_]+\d+')
INS=re.compile(r'(?m)(?:^|(?<=[\n{};]))\s*(?P<guard>@!?[\w%]+\s+)?(?P<op>[a-z][\w.]*)\s+(?P<args>[^;]+);')
def instructions(text):
 clean=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:re.sub(r'[^\n]',' ',m[0]),text,flags=re.S)
 result=[]
 for m in INS.finditer(clean):
  op=m['op'];args=m['args'].strip();level=0;end=len(args)
  for j,ch in enumerate(args):
   if ch in '{[(':level+=1
   elif ch in '}])':level-=1
   elif ch==',' and level==0:end=j;break
  first=args[:end].strip()
  writes=REG.findall(first) if first.startswith(('%','{')) and not op.startswith(('st.','red.','prefetch.')) else []
  result.append((m.start(),m.end(),op,writes,m['guard']))
 return result
class Sources(dict):pass
def safe_sources(text,down_pattern,pack_pattern,local_only=True):
 ins=instructions(text);defs=collections.defaultdict(list)
 for begin,end,op,regs,guard in ins:
  for r in regs:defs[r].append((begin,end,guard))
 boundaries=sorted(set([0,len(text)]+[m.start() for m in re.finditer(r'(?m)^\s*[\w$]+\s*:',text)]+[e for b,e,op,rs,g in ins if op in ('bra','bra.uni','ret','exit')]))
 def block(pos):return bisect.bisect_right(boundaries,pos)-1
 downs=collections.defaultdict(list)
 for m in down_pattern.finditer(text):downs[m['destination']].append(m)
 packs=collections.defaultdict(list)
 for m in pack_pattern.finditer(text):packs[m['destination']].append(m)
 out=Sources();out.until={};out.reasons=collections.Counter();out.rejected={};out.defs=defs
 for r,ps in packs.items():
  reason=None;p=ps[0]
  if len(ps)!=1 or len(defs[r])!=1:reason='pack_multidef'
  elif p['guard']:reason='predicated_pack'
  ds=[downs[p[k]] for k in ['low','high']]
  if not reason and any(len(d)!=1 or len(defs[p[k]])!=1 for k,d in zip(['low','high'],ds)):reason='down_multidef'
  if not reason:
   lo,hi=[d[0] for d in ds]
   if lo['guard'] or hi['guard']:reason='predicated_down'
   elif any(len(defs[d['source']])!=1 for d in (lo,hi)):reason='source_multidef'
   elif any(d.end()>p.start() for d in (lo,hi)):reason='conversion_order'
   elif local_only and any(block(d.start())!=block(p.start()) for d in (lo,hi)):reason='cross_block_down'
   elif local_only:
    # Original FP16 definitions must dominate both conversions in this same block.
    for d in (lo,hi):
     srcdef=defs[d['source']][0]
     if srcdef[2] or srcdef[1]>d.start() or block(srcdef[0])!=block(d.start()):reason='source_not_local';break
  if reason:out.reasons[reason]+=1;out.rejected[r]=reason;continue
  out[r]=(lo['source'],hi['source'],p.start());out.until[r]=boundaries[block(p.start())+1] if local_only else float('inf')
 return out

def mapped_at(sources, position):
 return {r:v for r,v in sources.items() if v[2]<position and position<getattr(sources,'until',{}).get(r,float('inf'))}
