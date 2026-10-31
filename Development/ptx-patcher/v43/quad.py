"""Binding-aware same-block fusion with all-CFG-path dead-after proof."""
import re,bisect,collections
from analysis_common import split_args,REG,cfg_loops
AUDIT=[]
class Flow:
 def __init__(self,text):
  self.text=text;self.ins,self.blocks,_=cfg_loops.parse(text);self.starts=[x['start'] for x in self.ins];self.owner={j:i for i,b in enumerate(self.blocks) for j in range(b['start'],b['end'])};self.braces=list(re.finditer(r'[{}]',text));self.bp=[x.start() for x in self.braces];self.paths=[()];stack=[]
  for i,m in enumerate(self.braces):
   if m[0]=='{':stack.append(i)
   elif stack:stack.pop()
   self.paths.append(tuple(stack))
  self.decls=[]
  for m in re.finditer(r'\.reg\s+[^;]+;',text):
   for v in re.finditer(r'(%[A-Za-z_]+)(\d*)(?:<(\d+)>)?',m[0]):self.decls.append((m.start(),self.path(m.start()),v[1],v[2],int(v[3]) if v[3] else None))
  self.bindcache={};self.reads=[];self.writes=[]
  for x in self.ins:
   args=split_args(x['args']) if x['args'] else [];first=args[0] if args else '';writes=REG.findall(first) if first.startswith(('%','{','(')) and not x['op'].startswith(('st.','red.','prefetch.')) else [];reads=[r for arg in (args[1:] if writes else args) for r in REG.findall(arg)]
   self.writes.append({self.bind(r,x['start']) for r in writes});self.reads.append({self.bind(r,x['start']) for r in reads})
 def path(self,pos):return self.paths[bisect.bisect_right(self.bp,pos)]
 def bind(self,r,pos):
  path=self.path(pos);key=(r,path)
  if key in self.bindcache:return self.bindcache[key]
  fits=[]
  for at,scope,prefix,digits,num in self.decls:
   if len(scope)>len(path) or path[:len(scope)]!=scope:continue
   if num is None:ok=r==prefix+digits
   else:ok=bool(re.fullmatch(re.escape(prefix)+r'\d+',r)) and int(r[len(prefix):])<num
   if ok:fits.append((len(scope),at))
  result=(r,max(fits)[1] if fits else -1);self.bindcache[key]=result;return result
 def point(self,pos):
  j=bisect.bisect_right(self.starts,pos)-1
  assert j>=0 and self.ins[j]['start']<=pos<self.ins[j]['end'],(pos,j)
  return j
 def dead_after(self,j,key):
  todo=[(self.owner[j],j+1)];seen=set()
  while todo:
   bid,start=todo.pop()
   if (bid,start) in seen:continue
   seen.add((bid,start));b=self.blocks[bid];killed=False
   for k in range(start,b['end']):
    if key in self.reads[k]:return False,{'read_instruction':k,'text':self.ins[k]['text']}
    if key in self.writes[k] and not self.ins[k]['guard']:killed=True;break
   if not killed:todo.extend((to,self.blocks[to]['start']) for to in b['succ'])
  return True,{'visited_block_positions':len(seen)}

def code(low,high,dst):
 from pack_range import pack
 lines=['{','.reg .b32 vq_lo,vq_hi,vq_t;']
 for src,out in [(low,'vq_lo'),(high,'vq_hi')]:lines += [x.replace('v36_a',out).replace('v36_t','vq_t') for x in pack(src,'UNUSED','pack4')[:-2]]
 return lines+[f'prmt.b32 {dst},vq_lo,vq_hi,0x7531;','}']
def fuse(text,stats,fb,spec,dp=None):
 if dp is None:
  import dlssnr_patcher as dp
 parts=re.split(r'(?=\.visible \.entry )',text);total=0
 for pi,part in enumerate(parts):
  if not part.startswith('.visible .entry '):continue
  name=re.match(r'\.visible \.entry (\w+)',part)[1]
  if fb not in spec.get('quad_fbs',[]) and name not in spec.get('quad_entries',[]):continue
  flow=Flow(part);downs={flow.point(m.start()):m for m in dp.FP8_DOWN_PATTERN.finditer(part)};replacements=[];used=set();reasons=collections.Counter();accepted=[];examples=[]
  for pack in dp.FP8_PACK_PATTERN.finditer(part):
   k=flow.point(pack.start());lo,hi=pack['low'],pack['high']
   if pack['guard'] or lo==hi:reasons['guarded_or_same_half']+=1;continue
   keys=[flow.bind(r,pack.start()) for r in (lo,hi)];bid=flow.owner[k];defs=[]
   for key in keys:
    defs.append(next((j for j in range(k-1,flow.blocks[bid]['start']-1,-1) if key in flow.writes[j]),None))
   if any(j is None or j not in downs for j in defs):
    reasons['not_two_local_down_defs']+=1
    if len(examples)<4:examples.append({'pack':pack[0],'pack_line':part.count('\n',0,pack.start())+1,'last_defs':[flow.ins[j]['text'] if j is not None else 'no definition in this basic block' for j in defs]})
    continue
   a,z=[downs[j] for j in defs]
   if a['guard'] or z['guard'] or any(j in used for j in defs):reasons['guarded_or_already_fused_def']+=1;continue
   source_keys=[flow.bind(m['source'],m.start()) for m in (a,z)]
   if any(flow.bind(m['source'],pack.start())!=key for m,key in zip((a,z),source_keys)):reasons['source_lexical_binding_changes']+=1;continue
   allkeys=set(keys+source_keys);invalid=False
   for j in range(min(defs),k):
    allowed={keys[0]} if j==defs[0] else ({keys[1]} if j==defs[1] else set())
    if (flow.writes[j]&allkeys)-allowed or flow.reads[j]&set(keys):invalid=True;break
   if invalid:reasons['intervening_write_or_half_read']+=1;continue
   proofs=[flow.dead_after(k,key) for key in keys]
   if not all(ok for ok,_ in proofs):reasons['half_live_out']+=1;continue
   body=[line.replace('vq_',f'v42q{total}_') for line in code(a['source'],z['source'],pack['destination'])]
   replacements += [(a.start(),a.end(),''),(z.start(),z.end(),''),(pack.start(),pack.end(),'\n'.join(body))];used.update(defs);accepted.append({'pack_line':part.count('\n',0,pack.start())+1,'down_lines':[part.count('\n',0,m.start())+1 for m in (a,z)],'sources':[a['source'],z['source']],'halves':[lo,hi],'destination':pack['destination'],'block':bid,'proofs':[v for _,v in proofs]});total+=1
  for start,end,new in sorted(replacements,reverse=True):part=part[:start]+new+part[end:]
  parts[pi]=part;AUDIT.append({'FB':fb,'kernel':name,'fused':len(accepted),'rejections':dict(reasons),'accepted':accepted,'rejection_examples':examples})
 stats.add('fused_quad_pairs',total);stats.add('fp16_to_fp8',2*total);return ''.join(parts)
