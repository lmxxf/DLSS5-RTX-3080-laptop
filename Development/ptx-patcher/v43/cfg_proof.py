"""Conservative all-path register stability, including cycles and guarded writes."""
import collections
class CFGProof:
 def __init__(self,o):
  self.o=o;self.reach_cache={};self.writes=collections.defaultdict(list)
  for j,x in enumerate(o.ins):
   for r in x['writes']:self.writes[r].append(j)
  reachable={0};todo=[0]
  while todo:
   b=todo.pop()
   for q in o.blocks[b]['succ']:
    if q not in reachable:reachable.add(q);todo.append(q)
  self.dom={b:({0} if b==0 else set(reachable)) for b in reachable};change=True
  while change:
   change=False
   for b in sorted(reachable-{0}):
    preds=o.preds[b]&reachable;d={b}|(set.intersection(*(self.dom[q] for q in preds)) if preds else set())
    if d!=self.dom[b]:self.dom[b]=d;change=True
 def reach_blocks(self,b):
  if b in self.reach_cache:return self.reach_cache[b]
  seen=set();todo=list(self.o.blocks[b]['succ'])
  while todo:
   q=todo.pop()
   if q not in seen:seen.add(q);todo.extend(self.o.blocks[q]['succ'])
  self.reach_cache[b]=seen;return seen
 def reachable(self,a,b):
  if a>=len(self.o.ins):return False
  x,y=self.o.owner[a],self.o.owner[b]
  return (a<=b or x in self.reach_blocks(x)) if x==y else y in self.reach_blocks(x)
 def prove(self,j,k,src):
  o=self.o;bj,bk=o.owner[j],o.owner[k];dominates=bj in self.dom.get(bk,set());bad=[]
  if dominates:
   for w in self.writes[src]:
    if w==k:
     # The conversion reads before writing. A later re-entry without any
     # intervening source restoration is conservatively treated as a hazard.
     if self.reachable(k+1,k):bad.append(w)
    elif self.reachable(j+1,w) and self.reachable(w,k):bad.append(w)
  calls=[w for w,x in enumerate(o.ins) if x['op'].startswith('call') and self.reachable(j+1,w) and self.reachable(w,k)]
  return {'dominates':dominates,'split_block':bj,'use_block':bk,'source_write_witnesses':[{'index':w,'text':o.ins[w]['text']} for w in bad],'opaque_call_witnesses':calls,'all_paths_unclobbered':dominates and not bad and not calls,'policy':'all syntactic CFG paths including cycles; guarded source writes clobber; no cycle/reset relaxation'}
