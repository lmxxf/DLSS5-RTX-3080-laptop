"""Source-complete Shared access inventory, address DAGs and thread witnesses.
Concrete maps are tagged as resolved/partial; no unresolved path is called proof.
"""
from pathlib import Path
import re,json,collections,math,bisect
from analysis_common import Origin,entries,REG
p=Path(__file__).resolve().parent;old=json.loads((p.parent/'v27/source-audit.json').read_text());caps=json.loads((p/'shared-capacity-api.json').read_text());prof=json.loads((p.parent/'v23/profile.json').read_text());blocks={r['name']:r['block'] for r in prof['1280']['calls']};launch=json.loads((p.parent/'v25/launch-params.json').read_text());params={r['name']:bytes.fromhex(r['hex']) for r in launch['1280']['params']};out={};event_count=0
class Eval:
 def __init__(self,o,symbols,block,parameter_bytes):self.o=o;self.symbols=symbols;self.block=block;self.params=parameter_bytes;self.cache={};self.busy=set();self.partial=set();self.unsupported=collections.Counter()
 def arg(self,a,j,t):
  a=a.strip()
  linear=t;bx,by,bz=self.block;xyz=(t%bx,(t//bx)%by,t//(bx*by));special={'%laneid':linear%32,'%warpid':linear//32,'WARP_SZ':32}
  special.update({f'%tid.{q}':xyz[k] for k,q in enumerate('xyz')});special.update({f'%ntid.{q}':self.block[k] for k,q in enumerate('xyz')});special.update({f'%ctaid.{q}':0 for q in 'xyz'})
  if a in special:return {special[a]}
  if a in self.symbols:return {self.symbols[a]}
  if REG.fullmatch(a):return self.reg(a,j,t)
  try:return {int(a,0)}
  except ValueError:return set()
 def reg(self,r,point,t):
  key=(r,point,t)
  if key in self.cache:return self.cache[key]
  if key in self.busy:self.partial.add(key);return set()
  self.busy.add(key);values=set()
  for j,s in self.o.reach(r,point):
   if j<0:continue
   values.update(self.ins(j,t))
   if len(values)>16:values=set();self.unsupported['too_many_values']+=1;break
  self.busy.remove(key);self.cache[key]=values;return values
 def ins(self,j,t):
  x=self.o.ins[j];op=x['op'];a=x['argv'];result=set();dtype=re.findall(r'\.(?:[busf])(\d+)',op);bits=int(dtype[0]) if dtype else 32
  if '.wide.' in op:bits*=2
  mask=(1<<bits)-1
  if op.startswith('ld.param'):
   m=re.search(r'param_\d+(?:\+(\d+))?\]',a[1]);offset=int(m[1] or 0) if m else None
   if offset is not None and offset+bits//8<=len(self.params):return {int.from_bytes(self.params[offset:offset+bits//8],'little')}
   return set()
  if op.startswith(('ld.','mma.','call','st.')):return set()
  vals=[self.arg(z,j,t) for z in a[1:]]
  if not all(vals):return set()
  import itertools
  for args in itertools.product(*vals):
   if len(result)>16:return set()
   try:
    signed=lambda z,w=32:z-(1<<w) if z&(1<<(w-1)) else z
    stem=op.split('.')[0]
    if stem in ('mov','cvta'):v=args[0]
    elif stem=='cvt':
     v=args[0]
     if '.s32' in op and '.s64.' in op:v=signed(v)
    elif stem=='add':v=args[0]+args[1]
    elif stem=='sub':v=args[0]-args[1]
    elif stem in ('mul','mad'):
     aa,bb=args[:2]
     if '.s32' in op and '.wide.' in op:aa,bb=signed(aa),signed(bb)
     v=aa*bb+(args[2] if stem=='mad' else 0)
     if '.hi.' in op:v>>=bits
    elif stem=='shl':v=args[0]<<min(args[1],bits)
    elif stem=='shr':v=(signed(args[0],bits) if '.s' in op else args[0])>>min(args[1],bits)
    elif stem=='and':v=args[0]&args[1]
    elif stem=='or':v=args[0]|args[1]
    elif stem=='xor':v=args[0]^args[1]
    elif stem=='neg':v=-args[0]
    elif stem=='not':v=~args[0]
    elif stem=='rem':v=args[0]%args[1]
    elif stem=='div':v=args[0]//args[1]
    elif stem=='min':v=min(args)
    elif stem=='max':v=max(args)
    elif stem=='selp':v=args[0] if args[2] else args[1]
    elif stem=='bfe':v=(args[0]>>args[1])&((1<<args[2])-1)
    elif stem=='bfi':v=(args[1]&~(((1<<args[3])-1)<<args[2]))|((args[0]&((1<<args[3])-1))<<args[2])
    elif stem=='lop3':
     v=0
     for k in range(8):
      if args[3]&(1<<k):v|=(args[0] if k&4 else ~args[0])&(args[1] if k&2 else ~args[1])&(args[2] if k&1 else ~args[2])
    elif stem=='prmt' and op=='prmt.b32':
     v=0;source=args[0]|(args[1]<<32)
     for n in range(4):
      select=(args[2]>>(4*n))&15;byte=(source>>(8*(select&7)))&255
      if select&8:byte=255 if byte&128 else 0
      v|=byte<<(8*n)
    elif stem=='setp':
     aa,bb=args[:2]
     if '.s32' in op:aa,bb=signed(aa),signed(bb)
     cmp=op.split('.')[1];v=int({'eq':aa==bb,'ne':aa!=bb,'lt':aa<bb,'le':aa<=bb,'gt':aa>bb,'ge':aa>=bb}[cmp])
    else:self.unsupported[op]+=1;continue
    result.add(v&mask)
   except (ZeroDivisionError,OverflowError,KeyError):pass
  return result
 def address(self,a,j,t):
  m=re.fullmatch(r'\[\s*(%\w+)(?:\s*([+-])\s*(\d+))?\s*\]',a)
  if not m:return set()
  offset=int(m[3] or 0)*(-1 if m[2]=='-' else 1);return {v+offset for v in self.reg(m[1],j,t)}
 def slice(self,r,point,limit=100):
  todo=[(r,point)];seen=set();nodes=[]
  while todo and len(nodes)<limit:
   rr,pp=todo.pop()
   for j,s in self.o.reach(rr,pp):
    if j<0 or (j,s) in seen:continue
    seen.add((j,s));x=self.o.ins[j];nodes.append({'register':s,'index':j,'line':self.o.text.count('\n',0,x['start'])+1,'text':x['text']})
    for a in x['argv'][1:]:todo.extend((z,j) for z in REG.findall(a))
  return {'nodes':nodes,'truncated':bool(todo)}
for fb in range(1,7):
 text=(p/f'artifacts/raw/fb{fb:02}.ptx').read_text()
 for name,entry in entries(text):
  if name not in caps['kernels'] or name not in old['fatbins'][str(fb)]:continue
  records=[r for r in old['fatbins'][str(fb)][name]['records'] if r['leaf_categories']==['shared_load']]
  if not records:continue
  o=Origin(entry);arrays=caps['kernels'][name]['declared_arrays'];symbols={r['symbol']:(i+1)*(1<<20) for i,r in enumerate(arrays)};ev=Eval(o,symbols,blocks[name],params[name]);accesses=[];barriers=[]
  for j,x in enumerate(o.ins):
   op=x['op'];a=x['argv']
   if op.startswith(('bar.sync','barrier.sync')) and not x['guard']:barriers.append(j)
   if (op.startswith(('st.shared','ld.shared')) or op.startswith('cp.async')):
    kind='store' if op.startswith('st.') else ('load' if op.startswith('ld.') else 'async_copy');arg=a[0] if kind!='load' else a[1];roots=o.addr_roots(REG.findall(arg),j);roots=[z[7:] for z in roots if z.startswith('symbol:')]
    dtype=re.findall(r'\.([busf])(\d+)',op);vector=re.search(r'\.v([248])\.',op);size=(int(dtype[-1][1])//8 if dtype else 0)*(int(vector[1]) if vector else 1)
    values=[]
    if kind=='store':values=sorted(o.leaves([d for aa in a[1:] for rr in REG.findall(aa) for d in o.reach(rr,j)]))
    accesses.append({'index':j,'line':entry.count('\n',0,x['start'])+1,'op':op,'kind':kind,'guard':x['guard'],'text':x['text'],'address':arg,'bytes':size,'symbols':roots,'stored_value_origins':values,'address_slice': [ev.slice(rr,j) for rr in REG.findall(arg)]})
  astore={r['index']:r for r in accesses if r['kind']=='store'};aload={r['index']:r for r in accesses if r['kind']=='load'};epoch_cache={};maps={}
  for j,load in aload.items():
   before=[k for k in barriers if k<j];bar=before[-1] if before else None;prev=before[-2] if len(before)>1 else -1
   producers=[s for k,s in astore.items() if prev<k<(bar if bar is not None else j) and set(s['symbols'])&set(load['symbols'])]
   key=(prev,bar,tuple(load['symbols']));owners={};ambiguous=set();unresolved_stores=0
   if key in epoch_cache:owners,ambiguous,unresolved_stores=epoch_cache[key]
   else:
    for store in producers:
     for t in range(math.prod(blocks[name])):
      addresses=ev.address(store['address'],store['index'],t)
      if len(addresses)!=1 or store['guard']:unresolved_stores+=1;continue
      base=next(iter(addresses))
      for off in range(store['bytes']):
       addr=base+off;new=(t,store['index'],off)
       if addr in owners and owners[addr]!=new:ambiguous.add(addr)
       owners[addr]=new
    epoch_cache[key]=(owners,ambiguous,unresolved_stores)
   same=crosslane=crosswarp=unknown=0;witnesses=[];word_sources=collections.defaultdict(set)
   for t in range(math.prod(blocks[name])):
    addresses=ev.address(load['address'],j,t)
    if len(addresses)!=1:unknown+=load['bytes'];continue
    base=next(iter(addresses))
    for off in range(load['bytes']):
     addr=base+off
     if addr not in owners or addr in ambiguous:unknown+=1;continue
     writer,site,poff=owners[addr]
     if writer==t:
      same+=1
      if off%4==0 and poff%4==0:word_sources[off//4].add((astore[site]['line'],poff//4))
     elif writer//32==t//32:crosslane+=1
     else:crosswarp+=1
     if writer!=t and len(witnesses)<4:witnesses.append({'reader_linear_tid':t,'writer_linear_tid':writer,'reader_byte':off,'writer_byte':poff,'write_line':astore[site]['line'],'read_line':load['line'],'synthetic_shared_address':addr})
   maps[j]={'load_line':load['line'],'producer_barrier_index':bar,'producer_store_lines':[s['line'] for s in producers],'same_thread_bytes':same,'cross_lane_bytes':crosslane,'cross_warp_bytes':crosswarp,'unresolved_or_ambiguous_bytes':unknown,'unguarded_store_evaluations_unresolved':unresolved_stores,'same_thread_source_word_choices':{str(w):sorted(v) for w,v in word_sources.items()},'uniform_same_thread_proved':bool(producers) and crosslane==crosswarp==unknown==unresolved_stores==0,'cross_thread_witnesses':witnesses,'scope':'lexical publication epoch witness for 720p archived launch params, CTA(0,0,0); cyclic/unknown definitions are explicitly unresolved, not universal mapping proof'}
  ms=list(__import__('analysis_common').b.dp.FP8_MMA_PATTERN.finditer(entry));groups=[]
  for m in ms:
   if not groups or entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  eventrows=[]
  for r in records:
   point=bisect.bisect_right(o.starts,groups[r['run']][0].start())-1;defs=o.reach(r['register'],point);assert len(defs)==1;d,_=next(iter(defs));assert d in aload
   eventrows.append({'run':r['run'],'register':r['register'],'read_index':d,'read_line':aload[d]['line']});event_count+=1
  for a in accesses:
   a['symbol_async_aliases']=[b['line'] for b in accesses if b['kind']=='async_copy' and set(a['symbols'])&set(b['symbols'])]
  out[name]={'FB':fb,'shared_events':len(records),'event_records':eventrows,'capacity':caps['kernels'][name],'accesses':accesses,'load_mappings':list(maps.values()),'cyclic_address_subexpressions':len(ev.partial),'unsupported_address_ops':dict(ev.unsupported),'uniform_same_thread_loads_proved':sum(m['uniform_same_thread_proved'] for m in maps.values()),'cross_thread_loads_with_witness':sum(bool(m['cross_thread_witnesses']) for m in maps.values()),'unresolved_load_mappings':sum(m['unresolved_or_ambiguous_bytes']>0 for m in maps.values())};print(fb,name,len(records),out[name]['uniform_same_thread_loads_proved'],out[name]['cross_thread_loads_with_witness'],out[name]['unresolved_load_mappings'],flush=True)
assert event_count==2320
result={'scope':'FB01..05:2304 events; FB06 appendix:16; source-complete inventory and address slices, bounded concrete thread witnesses with unresolved cases retained','shared_event_count':event_count,'device':caps['device'],'all_payload_doublings_preserve_current_residency':caps['all_doubled_payload_fit_current_residency'],'capacity_exhaustion_claim_supported':False,'remaining_coupled_layout_path_not_excluded':True,'kernels':out}
(p/'shared-layout-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',event_count)
