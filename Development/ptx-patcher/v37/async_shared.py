"""Refresh a separate FP16 view at collective publication points, keeping old async copy layout."""
from pathlib import Path
import json,re,collections
from analysis_common import Origin,entries,REG,b
from v26.codegen import decode
p=Path(__file__).resolve().parent

def audit():
 a=json.loads((p.parent/'v35/analysis.json').read_text());out={};selected={}
 for fb in ['4','5']:
  parts=dict(entries((p/f'artifacts/raw/fb{int(fb):02}.ptx').read_text()))
  for n,k in a['fatbins'][fb].items():
   entry=parts[n];o=Origin(entry);refresh=[];epochs=[];last=-1
   for j,x in enumerate(o.ins):
    if x['op'].startswith(('bar.sync','barrier.sync')) and x['argv'][0]=='0' and len(x['argv'])==1 and not x['guard']:refresh.append(j+1)
    if x['op'].startswith('mbarrier.') and 'wait' in x['op']:
     bid=o.owner[j];block=o.blocks[bid];tail=block['ins'][-1]
     # Source wait retry branch returns to this block; fall-through is publication.
     if tail['op'].startswith('bra') and tail['guard'] and bid in block['succ']:refresh.append(block['end'])
   all_publications=sorted(set(j for j in refresh if j<len(o.ins)))
   # Only a publication node on every returning CTA path may gain a CTA barrier.
   universe=set(range(len(o.blocks)));returns={i for i,q in enumerate(o.blocks) if not q['succ']};pd={i:({i} if i in returns else set(universe)) for i in universe};change=True
   while change:
    change=False
    for i in universe-returns:
     new={i}|set.intersection(*(pd[t] for t in o.blocks[i]['succ']))
     if new!=pd[i]:pd[i]=new;change=True
   payload_writes=[j for j,x in enumerate(o.ins) if x['op'].startswith(('st.shared','cp.async'))]
   refresh=sorted(set(j for j in refresh if j<len(o.ins) and o.owner[j] in pd[0] and any(w<j for w in payload_writes)))
   for end in all_publications+[len(o.ins)]:
    xs=o.ins[last+1:end];cp=[x for x in xs if x['op'].startswith('cp.async')];st=[x for x in xs if x['op'].startswith('st.shared')];epochs.append({'begin_line':entry.count('\n',0,o.ins[max(last+1,0)]['start'])+1,'publication_index':end,'type':'II_async_or_mixed' if cp else 'I_register_store' if st else 'no_payload_producer','cp_async_sites':len(cp),'st_shared_sites':len(st),'cp_text':[x['text'] for x in cp],'store_text':[x['text'] for x in st]});last=end
   # Fixed point: dirty after any target write/copy, clean after collective refresh.
   writes=set()
   for j,x in enumerate(o.ins):
    if x['op'].startswith(('st.shared','cp.async')):
     roots=o.addr_roots(REG.findall(x['argv'][0]),j)
     if not roots or any('symbol:'+s in roots for s in k['symbols']):writes.add(j)
   before={bid:(False if bid==0 else True) for bid in range(len(o.blocks))};after=before.copy();changed=True
   while changed:
    changed=False
    for bid,block in enumerate(o.blocks):
     state=False if bid==0 or not o.preds[bid] else all(after[q] for q in o.preds[bid]);start=state
     for j in range(block['start'],block['end']):
      if j in refresh:state=True
      if j in writes:state=False
     if before[bid]!=start or after[bid]!=state:before[bid]=start;after[bid]=state;changed=True
   clean={}
   for bid,block in enumerate(o.blocks):
    state=before[bid]
    for j in range(block['start'],block['end']):
     if j in refresh:state=True
     clean[j]=state
     if j in writes:state=False
   goodloads=[l for l in k['MMA_loads'] if clean[l['index']]]
   size=sum(v['bytes'] for v in k['symbols'].values());extra=2*size;baseShared=json.loads((p.parent/'v35/resources.json').read_text())['baseline'][n]['SHARED'];limit=baseShared+extra<=49152
   # Arrival count in source is full block; reject arrive_drop or unclear init.
   full_arrival=bool(re.search(r'mul\.lo\.s32\s+%r\d+,\s*%r\d+,\s*%r\d+;',entry)) and 'arrive_drop' not in entry
   eligible=bool(refresh and goodloads and limit and full_arrival)
   decls=[{'symbol':m[3],'bytes':int(m[2])//8*int(m[4] or 1),'align':int(m[1] or 1)} for m in re.finditer(r'\.shared\s+(?:\.align\s+(\d+)\s+)?\.b(8|16|32|64)\s+(\S+?)(?:\[(\d+)\])?;',entry)]
   out[n]={'all_shared_declarations':decls,'FB':int(fb),'source_cp_async_total':sum(x['op'].startswith('cp.async') for x in o.ins),'epochs':epochs,'all_publication_epochs':epochs,'epoch_scope':'all raw full-CTA bar and mbar-wait retry exits; candidate injection points are a certified subset','publication_points':[{'index':j,'line':entry.count('\n',0,o.ins[j]['start'])+1} for j in refresh],'MMA_shared_loads':len(k['MMA_loads']),'clean_loads':len(goodloads),'original_static_shared':baseShared,'extra_shadow_bytes':extra,'total_static_shared':baseShared+extra,'fits_default_static_48KiB':limit,'eligible_constructive_candidate':eligible,'publication_blocks_postdominate_entry':all(o.owner[j] in pd[0] for j in refresh),'model':'separate view refreshed by cooperative byte decode after waits/barriers; old cp.async address/count and old byte view remain unchanged','instruction_cost_per_original_4B_word':{'LDS_u32':1,'decode_PTX':8,'STS_v2_u32':1},'additional_BAR_per_refresh':1,'scope':'epoch classification includes mixed async/fallback alternatives; full-loop timing still required'}
   if eligible:
    kk=k|{'eligible_shadow':True};from coupled import plan_kernel
    plan=plan_kernel(n,entry,kk);plan['MMA_loads']=goodloads;allowed={l['index'] for l in goodloads};plan['shared_MMA_events']=[e for e in k['shared_MMA_events'] if e['load_index'] in allowed];plan['refresh_points']=refresh;selected[n]=plan
 (p/'fb45-shared-audit.json').write_text(json.dumps(out,indent=2)+'\n');(p/'async-plans.json').write_text(json.dumps(selected,indent=2)+'\n');print({n:(r['clean_loads'],r['MMA_shared_loads'],r['total_static_shared'],r['eligible_constructive_candidate']) for n,r in out.items()})

def refresh_code(k,ordinal):
 lines=['{','.reg .b32 cx,cy,cz,nx,ny,nz,tid,total,off,addr,oldbase,newbase,w,lo,hi,dlssnr_fp8_scale;','.reg .pred done;','mov.u32 cx,%tid.x;','mov.u32 cy,%tid.y;','mov.u32 cz,%tid.z;','mov.u32 nx,%ntid.x;','mov.u32 ny,%ntid.y;','mov.u32 nz,%ntid.z;','mad.lo.u32 tid,cz,ny,cy;','mad.lo.u32 tid,tid,nx,cx;','mul.lo.u32 total,nx,ny;','mul.lo.u32 total,total,nz;','shl.b32 total,total,2;','mov.b32 dlssnr_fp8_scale,0x5c005c00;']
 for si,(symbol,d) in enumerate(k['symbols'].items()):
  label=f'$V36_copy_{ordinal}_{si}';end=label+'_end';lines += ['shl.b32 off,tid,2;',f'mov.u32 oldbase,{symbol};',f'mov.u32 newbase,v36_async_ext{si};',label+':',f'setp.ge.u32 done,off,{d["bytes"]};',f'@done bra {end};','add.u32 addr,oldbase,off;','ld.shared.u32 w,[addr];']+decode('w','lo','hi')+['shl.b32 addr,off,1;','add.u32 addr,newbase,addr;','st.shared.v2.u32 [addr],{lo,hi};','add.u32 off,off,total;',f'bra {label};',end+':']
 return '\n'.join(lines+['bar.sync 0;','}'])

def apply_entry(entry,k,mode):
 from coupled import address,native_memory
 o=Origin(entry);changes=[];decl=['.reg .b32 '+','.join(k['native_declarations'])+';']
 for si,(symbol,d) in enumerate(k['symbols'].items()):decl.append(f'.shared .align 16 .b8 v36_async_ext{si}[{2*d["bytes"]}];')
 for i,j in enumerate(k['refresh_points']):at=o.ins[j]['start'];changes.append((at,at,refresh_code(k,i)+'\n'))
 allowed={l['index'] for l in k['MMA_loads']}
 for l in k['all_loads']:
  if l['index'] not in allowed:continue
  si=list(k['symbols']).index(l['symbol']);lines=['{']+address(l['address'],l['symbol'],f'v36_async_ext{si}')+native_memory('ld.shared',[r for pair in l['native'] for r in pair])+['}'];x=o.ins[l['index']];changes.append((x['end'],x['end'],'\n'+'\n'.join(lines)))
 for a,z,new in sorted(changes,reverse=True):entry=entry[:a]+new+entry[z:]
 at=entry.index('{')+1;return entry[:at]+'\n'+'\n'.join(decl)+'\n'+entry[at:]
if __name__=='__main__':audit()
