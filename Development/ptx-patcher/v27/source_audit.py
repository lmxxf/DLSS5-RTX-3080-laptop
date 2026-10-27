"""CFG may-reaching definitions of each unique nonmapped operand per MMA run.
Memory origins stay memory origins: global != proven weight, and shared may hold
locally quantized intermediates. Counts are static run-decode events, not frames.
"""
from pathlib import Path
import sys,re,json,bisect,collections
from functools import partial
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));sys.path.insert(0,str(p.parent/'v25'));import build_sm86_dlls as b
import cfg_loops,ptx_mapped
# Audit parser must recognize state-space qualifiers such as ld.shared::cta.
complete_INS=ptx_mapped.INS
legacy_INS=re.compile(complete_INS.pattern.replace('(?:::[\\w.]+)*',''),complete_INS.flags)
ptx_mapped.INS=legacy_INS
cfg_loops.INS=complete_INS
from cfg_loops import parse
from v26.codegen import render
active=set(json.loads((p.parent/'v26/sass-audit.json').read_text())['decode']);REG=re.compile(r'%[A-Za-z_]+\d+')
b.dp.fp8_pack_sources=partial(b.stock_pack_sources,local_only=False);b.dp.mapped_fp16_sources=b.forward_mapped_fp16_sources

def split_args(args):
 out=[];start=0;depth=0
 for i,c in enumerate(args):
  if c in '{[(':depth+=1
  elif c in '}])':depth-=1
  elif c==',' and depth==0:out.append(args[start:i].strip());start=i+1
 return out+[args[start:].strip()]

class Origin:
 def __init__(self,text):
  self.text=text;self.ins,self.blocks,self.loops=parse(text);self.starts=[x['start'] for x in self.ins];self.owner={};self.preds=collections.defaultdict(set);self.defs=collections.defaultdict(lambda:collections.defaultdict(list));self.cache={};self.leafcache={};self.addrcache={}
  for bid,block in enumerate(self.blocks):
   for to in block['succ']:self.preds[to].add(bid)
   for j in range(block['start'],block['end']):
    self.owner[j]=bid;x=self.ins[j];x['argv']=split_args(x['args']);first=x['argv'][0];x['writes']=REG.findall(first) if first.startswith(('%','{')) and not x['op'].startswith(('st.','red.','prefetch.')) else []
    for r in x['writes']:self.defs[bid][r].append(j)
 def reach(self,r,point):
  key=(r,point)
  if key in self.cache:return self.cache[key]
  todo=[(self.owner[point],point)];seen=set();found=set()
  while todo:
   bid,end=todo.pop()
   if (bid,end) in seen:continue
   seen.add((bid,end));killed=False
   for j in reversed(self.defs[bid].get(r,[])):
    if j>=end:continue
    found.add((j,r))
    if not self.ins[j]['guard']:killed=True;break
   if not killed:
    if not self.preds[bid]:found.add((-1,r))
    else:todo.extend((prev,self.blocks[prev]['end']) for prev in self.preds[bid])
  self.cache[key]=frozenset(found);return self.cache[key]
 def root_kind(self,definition):
  j,r=definition
  if j<0:return 'undefined_or_external'
  x=self.ins[j];op=x['op'];a=x['argv']
  if op.startswith('ld.') and '.shared' in op:return 'ld.shared'
  if op.startswith('ld.') and '.global' in op:return 'ld.global'
  if op.startswith('ld.param'):return 'ld.param'
  if op=='mov.b32' and len(a)>1 and a[1].startswith('{'):return 'mov.pack16'
  if op.startswith('mov.'):
   if len(a)>1 and REG.fullmatch(a[1]):return 'mov.alias'
   return 'mov.constant_or_special'
  return op
 def leaves(self,definitions):
  todo=list(definitions);seen=set();out=set()
  while todo:
   j,r=todo.pop()
   if (j,r) in seen:continue
   seen.add((j,r))
   if j<0:out.add('unresolved');continue
   x=self.ins[j];op=x['op'];a=x['argv']
   if op.startswith('ld.') and '.global' in op:out.add('global_load');continue
   if op.startswith('ld.') and '.shared' in op:out.add('shared_load');continue
   if op=='cvt.rn.satfinite.e4m3x2.f16x2':out.add('local_FP8_quantization');continue
   if op.startswith('mma.'):out.add('local_MMA_result');continue
   if op.startswith('ld.param'):out.add('parameter');continue
   if op.startswith(('mov.','shfl.','prmt.','and.','or.','xor.','shl.','shr.','selp.','cvt.u','cvt.b','cvt.s')):
    refs=[z for arg in a[1:] for z in REG.findall(arg) if not z.startswith('%p')]
    if refs:
     for z in refs:todo.extend(self.reach(z,j))
    else:out.add('constant_or_special')
   else:out.add('local_arithmetic:'+op)
  return frozenset(out or {'cyclic_or_unresolved'})
 def addr_roots(self,refs,point):
  todo=[d for r in refs for d in self.reach(r,point)];seen=set();roots=set()
  while todo:
   j,r=todo.pop()
   if (j,r) in seen:continue
   seen.add((j,r))
   if j<0:continue
   x=self.ins[j];op=x['op'];a=x['argv']
   if op.startswith('ld.param'):
    if op.endswith(('.b64','.u64')):
     m=re.search(r'param_\d+(?:\+(\d+))?\]',x['args']);roots.add('param64+'+(m[1] or '0') if m else 'param64:unknown')
    continue
   if op.startswith('ld.'):roots.add('pointer_loaded_from_memory');continue
   if op.startswith('mov.') and len(a)>1 and a[1].startswith('_'):roots.add('symbol:'+a[1]);continue
   for arg in a[1:]:
    for z in REG.findall(arg):
     if not z.startswith('%p'):todo.extend(self.reach(z,j))
  return sorted(roots)
 def memory_description(self,definitions):
  rows=[];todo=list(definitions);seen=set()
  while todo:
   j,r=todo.pop()
   if j<0 or (j,r) in seen:continue
   seen.add((j,r));x=self.ins[j];a=x['argv'];op=x['op']
   if op.startswith('ld.') and ('.shared' in op or '.global' in op):
    roots=self.addr_roots(REG.findall(a[1]),j);rows.append({'op':op,'roots':roots});continue
   if op.startswith(('mov.','shfl.','prmt.','and.','or.','xor.','shl.','shr.','selp.','cvt.u','cvt.b','cvt.s')):
    for arg in a[1:]:
     for z in REG.findall(arg):
      if not z.startswith('%p'):todo.extend(self.reach(z,j))
  return rows
 def local_alias_identity(self,r,point):
  bid=self.owner[point];defs=self.reach(r,point);seen=set()
  while len(defs)==1:
   j,s=next(iter(defs))
   if j<0 or self.owner[j]!=bid or (j,s) in seen:return None
   seen.add((j,s));x=self.ins[j];a=x['argv']
   if x['guard']:return None
   if x['op'].startswith('mov.') and len(a)>1 and REG.fullmatch(a[1]):defs=self.reach(a[1],j)
   else:return (j,s) # vector-load components are distinguished by destination
  return None

result={};all_peaks={}
for fb in range(7):
 raw=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text();rows={};peak_all=0;peak_active=0
 for entry in re.split(r'(?=\.visible \.entry )',raw)[1:]:
  name=re.match(r'\.visible \.entry (\w+)',entry)[1];ms=list(b.dp.FP8_MMA_PATTERN.finditer(entry))
  if not ms:continue
  groups=[[ms[0]]]
  for m in ms[1:]:
   if entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  sources=b.dp.fp8_pack_sources(entry);original_INS=ptx_mapped.INS
  try:
   ptx_mapped.INS=complete_INS;complete_sources=b.dp.fp8_pack_sources(entry)
  finally:ptx_mapped.INS=original_INS
  peaks=[]
  for g in groups:
   audit=[];render(g,sources,builder=b,audit=audit);peaks.append(audit[0]['temporary_b32_peak']);peak_all=max(peak_all,peaks[-1])
  if name not in active:continue
  peak_active=max(peak_active,max(peaks));origin=Origin(entry);records=[];root_counts=collections.Counter();leaf_counts=collections.Counter();reason_counts=collections.Counter();mapped_count=0;aliases=0
  from ptx_mapped import mapped_at
  for gi,g in enumerate(groups):
   point=bisect.bisect_right(origin.starts,g[0].start())-1;assert origin.ins[point]['op'].startswith('mma.')
   mapping=mapped_at(sources,g[0].start());operands=list(dict.fromkeys(m[k] for m in g for k in ('a0','a1','a2','a3','b0','b1')));mapped_count+=sum(r in mapping for r in operands);identities=collections.defaultdict(list)
   encoded=[r for r in operands if r not in mapping];first={};last={};writes={}
   for mi,m in enumerate(g):
    for reg in set(m[k] for k in ('a0','a1','a2','a3','b0','b1')):first.setdefault(reg,mi);last[reg]=mi
    for reg in (m['d0'],m['d1']):writes.setdefault(reg,mi)
   when={reg:min(first[reg],writes.get(reg,first[reg])) for reg in encoded};live=set();peak_live=set()
   for mi in range(len(g)):
    live.update(reg for reg in encoded if when[reg]==mi)
    if len(live)>len(peak_live):peak_live=set(live)
    live.difference_update(reg for reg in encoded if last[reg]==mi)
   assert 2*len(peak_live)==peaks[gi],(name,gi,peaks[gi],peak_live)

   for r in operands:
    if r in mapping:continue
    defs=origin.reach(r,point);kinds=sorted({origin.root_kind(d) for d in defs});rootclass=kinds[0] if len(defs)==1 else 'multiple_reaching_defs';leaves=sorted(origin.leaves(defs));leafsig='+'.join(leaves);reason=sources.rejected.get(r,'eligible_pack_after_run_text' if r in sources else 'not_a_recognized_FP8_pack');root_counts[rootclass]+=1;leaf_counts[leafsig]+=1;reason_counts[reason]+=1
    identity=origin.local_alias_identity(r,point)
    if identity is not None:identities[identity].append(r)
    records.append({'run':gi,'register':r,'mma_uses_in_run':sum(r in [m[k] for k in ('a0','a1','a2','a3','b0','b1')] for m in g),'reason':reason,'root_category':rootclass,'root_kinds':kinds,'leaf_categories':leaves,'reaching_definitions':[{'instruction_index':j,'register':s,'text':origin.ins[j]['text'] if j>=0 else 'undefined'} for j,s in sorted(defs)],'memory_sources':origin.memory_description(defs),'in_max_pool_run':peaks[gi]==max(peaks),'run_pool_b32':peaks[gi],'live_at_first_peak':r in peak_live})
   aliases+=sum(len(rs)-1 for rs in identities.values() if len(rs)>1)
  writers=[]
  for j,x in enumerate(origin.ins):
   if x['op'].startswith('cp.async.bulk.shared'):
    a=x['argv'];writers.append({'op':x['op'],'shared_roots':origin.addr_roots(REG.findall(a[0]),j),'global_roots':origin.addr_roots(REG.findall(a[1]),j),'value_categories':['global_async_copy']})
   elif x['op'].startswith('st.shared'):
    a=x['argv'];defs=[d for arg in a[1:] for r in REG.findall(arg) for d in origin.reach(r,j)];writers.append({'op':x['op'],'shared_roots':origin.addr_roots(REG.findall(a[0]),j),'value_categories':sorted(origin.leaves(defs))})
  rows[name]={'mapped_static_run_events':mapped_count,'nonmapped_static_run_events':len(records),'root_categories':dict(root_counts),'value_leaf_combinations':dict(leaf_counts),'eligibility_reasons':dict(reason_counts),'same_basic_block_pure_alias_duplicate_events':aliases,'max_pool_b32':max(peaks),'records':records,'shared_writer_may_origins':writers,'mapped_eligibility_parser_delta':{'added_with_complete_opcode_parser':sorted(set(complete_sources)-set(sources)),'removed_with_complete_opcode_parser':sorted(set(sources)-set(complete_sources))}};print(fb,name,len(records),dict(root_counts),flush=True)
 result[str(fb)]=rows;all_peaks[str(fb)]={'all_export_peak':peak_all,'active_peak':peak_active}
(p/'source-audit.json').write_text(json.dumps({'scope':'static unique operand per MMA run, before run execution; may-reaching defs, not dynamic per-frame instruction frequencies','FB_peaks':all_peaks,'fatbins':result},indent=2)+'\n')
