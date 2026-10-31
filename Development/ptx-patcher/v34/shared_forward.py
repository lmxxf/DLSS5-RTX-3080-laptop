"""Proof-gated encoded-word forwarding; quantization remains unchanged."""
from pathlib import Path
import re,json,math
from analysis_common import Origin,entries,REG,split_args,ptx_mapped
p=Path(__file__).resolve().parent

def make_plan():
 audit=json.loads((p/'shared-layout-audit.json').read_text());plan={};rejected=[]
 for fb in range(1,6):
  for name,entry in entries((p/f'artifacts/raw/fb{fb:02}.ptx').read_text()):
   if name not in audit['kernels']:continue
   k=audit['kernels'][name];o=Origin(entry)
   reachable=set();todo=[0]
   while todo:
    z=todo.pop()
    if z not in reachable:reachable.add(z);todo.extend(o.blocks[z]['succ'])
   dom={z:({0} if z==0 else set(reachable)) for z in reachable};changed=True
   while changed:
    changed=False
    for z in reachable-{0}:
     parents=o.preds[z]&reachable;new={z}|set.intersection(*(dom[t] for t in parents))
     if new!=dom[z]:dom[z]=new;changed=True
   def between(start,end):
    target=o.owner[end];anc={target};todo=[target]
    while todo:
     z=todo.pop()
     for t in o.preds[z]:
      if t not in anc:anc.add(t);todo.append(t)
    pending=[(o.owner[start],start+1)];seen=set();result=set()
    while pending:
     z,at=pending.pop()
     if z not in anc or (z,at) in seen:continue
     seen.add((z,at));stop=end if z==target and at<=end else o.blocks[z]['end'];result.update(range(at,stop))
     if stop!=end:pending.extend((t,o.blocks[t]['start']) for t in o.blocks[z]['succ'])
    return result
   byline={a['line']:a for a in k['accesses']};accepted=[]
   def tid_only(r,point,seen=None):
    seen=set() if seen is None else seen
    if (r,point) in seen:return False
    seen=seen|{(r,point)};ds=o.reach(r,point)
    if len(ds)!=1:return False
    j,rr=next(iter(ds))
    if j<0:return False
    x=o.ins[j]
    if x['guard'] or x['op'].startswith(('ld.','call','mma.')):return False
    for a in x['argv'][1:]:
     specials=re.findall(r'%[A-Za-z_]+\.[xyz]|%laneid|%warpid|%nctaid\.[xyz]',a)
     if any(s not in ['%tid.x','%tid.y','%tid.z','%ntid.x','%ntid.y','%ntid.z','%laneid'] for s in specials):return False
     for rr in REG.findall(a):
      if not tid_only(rr,j,seen):return False
    return True
   for m in k['load_mappings']:
    if not m['uniform_same_thread_proved']:continue
    load=byline[m['load_line']];j=load['index'];choices=m['same_thread_source_word_choices'];reason=None
    if load['bytes']!=16 or len(choices)!=4 or any(len(choices.get(str(w),[]))!=1 for w in range(4)):reason='not_fixed_vector_source'
    if reason is None:
     pairs=[choices[str(w)][0] for w in range(4)];lines={a[0] for a in pairs}
     if len(lines)!=1 or [a[1] for a in pairs]!=list(range(4)):reason='not_single_ordered_store'
    if reason is None:
     store=byline[next(iter(lines))];s=store['index'];rs=REG.findall(o.ins[s]['argv'][1]);rd=REG.findall(o.ins[j]['argv'][0]);symbol=set(load['symbols'])
     if len(rs)!=4 or len(rd)!=4 or store['guard'] or load['guard']:reason='not_unguarded_vector_pair'
     elif o.owner[s] not in dom.get(o.owner[j],set()) or (o.owner[s]==o.owner[j] and s>=j):reason='store_does_not_dominate_load'
     elif not all(tid_only(r,s) for r in REG.findall(store['address'])) or not all(tid_only(r,j) for r in REG.findall(load['address'])):reason='address_depends_on_params_cycles_or_memory'
     elif any(not all(tid_only(r,a['index']) for r in REG.findall(a['address'])) for a in k['accesses'] if a['line'] in m['producer_store_lines']):reason='epoch_store_dynamic_address'
     elif any(set(o.ins[t].get('writes',[]))&set(rs) for t in between(s,j)):reason='source_overwritten_on_reaching_path'
     elif any(o.ins[t]['op'].startswith(('call','atom.shared','red.shared','cp.async','mbarrier')) for t in between(s,j)):reason='intervening_unknown_memory_effect'
     else:
      # Every store in the publication window has been exhaustively mapped for
      # the shape. After the publication barrier, any further store is rejected.
      bidx=m['producer_barrier_index']
      if any(o.ins[t]['op'].startswith('st.shared') and (entry.count('\n',0,o.ins[t]['start'])+1) not in m['producer_store_lines'] for t in between(s,j)):reason='other_shared_write_on_reaching_path'
      elif any(a['guard'] for a in k['accesses'] if a['line'] in m['producer_store_lines']):reason='guarded_epoch_store'
    if reason:rejected.append({'kernel':name,'line':m['load_line'],'reason':reason});continue
    shape=__import__('json').loads((p.parent/'v23/profile.json').read_text())['1280']['calls'];shape=next(a['block'] for a in shape if a['name']==name)
    accepted.append({'load_line':load['line'],'store_line':store['line'],'destinations':rd,'sources':rs,'address':load['address'],'shape':shape,'proof':'unguarded store dominates load; all reaching paths preserve source words; TID-only address dependency; unique fixed per-thread writer for all 16 bytes; unchanged source words; no intervening unknown memory effects; original quantized words preserved; runtime shape guard falls back otherwise'})
   if accepted:plan[name]=accepted
 out={'kernels':plan,'accepted_load_vectors':sum(len(v) for v in plan.values()),'rejected':rejected,'scope':'encoded word LDS elimination only; FP8 quantization and all Shared stores/barriers preserved; includes non-MMA Shared loads found by full inventory'};(p/'shared-forward-plan.json').write_text(json.dumps(out,indent=2)+'\n');print('accepted',out['accepted_load_vectors'],'entries',len(plan),'rejected',len(rejected));return out

def apply(text,fb,plan_override=None):
 data=plan_override if plan_override is not None else json.loads((p/'shared-forward-plan.json').read_text())['kernels'];parts=re.split(r'(?=\.visible \.entry )',text);changed=0
 for pi,part in enumerate(parts):
  if not part.startswith('.visible .entry '):continue
  name=re.match(r'\.visible \.entry (\w+)',part)[1]
  if name not in data:continue
  replacements=[];shape=data[name][0]['shape']
  for row in data[name]:
   matches=[]
   for m in ptx_mapped.INS.finditer(part):
    if m['op'].startswith('ld.shared'):
     a=split_args(m['args'])
     if REG.findall(a[0])==row['destinations'] and a[1].strip()==row['address']:matches.append(m)
   assert len(matches)==1,(name,row,len(matches));m=matches[0];assert not m['guard'];moves=[f'@v34_shape_ok mov.b32 {d},{s};' for d,s in zip(row['destinations'],row['sources'])];fallback='@!v34_shape_ok '+m[0].strip();replacements.append((m.start(),m.end(),'\n'.join(moves+[fallback])));changed+=1
  for begin,end,new in sorted(replacements,reverse=True):part=part[:begin]+new+part[end:]
  guard=['.reg .b32 v34_sx,v34_sy,v34_sz;','.reg .pred v34_px,v34_py,v34_pz,v34_shape_ok;','mov.u32 v34_sx,%ntid.x;','mov.u32 v34_sy,%ntid.y;','mov.u32 v34_sz,%ntid.z;',f'setp.eq.u32 v34_px,v34_sx,{shape[0]};',f'setp.eq.u32 v34_py,v34_sy,{shape[1]};',f'setp.eq.u32 v34_pz,v34_sz,{shape[2]};','and.pred v34_shape_ok,v34_px,v34_py;','and.pred v34_shape_ok,v34_shape_ok,v34_pz;']
  first=next(ptx_mapped.INS.finditer(part)).start();part=part[:first]+'\n'+'\n'.join(guard[2:])+'\n'+part[first:];at=part.index('{')+1;parts[pi]=part[:at]+'\n'+'\n'.join(guard[:2])+'\n'+part[at:]
 return ''.join(parts),changed
if __name__=='__main__':make_plan()
