from pathlib import Path
import re,json,bisect,collections
from analysis_common import raw_modules,entries,Origin,REG,b
p=Path(__file__).resolve().parent;archived=json.loads((p.parent/'v27/source-audit.json').read_text());active=json.loads((p.parent/'v34/resources.json').read_text())['baseline'];out={}
for fb,text in raw_modules():
 (p/f'artifacts/raw/fb{fb:02}.ptx').write_text(text);kernels={}
 for name,entry in entries(text):
  if name not in active:continue
  old=archived['fatbins'][str(fb)].get(name,{})
  records=[r for r in old.get('records',[]) if r['leaf_categories']==['shared_load']]
  if not records:continue
  o=Origin(entry);ms=list(b.dp.FP8_MMA_PATTERN.finditer(entry));groups=[]
  for m in ms:
   if not groups or entry[groups[-1][-1].end():m.start()].strip():groups.append([m])
   else:groups[-1].append(m)
  loads={};events=[]
  for r in records:
   point=bisect.bisect_right(o.starts,groups[r['run']][0].start())-1;ds=o.reach(r['register'],point);assert len(ds)==1;j,reg=next(iter(ds));x=o.ins[j];assert x['op'].startswith('ld.shared');roots=[s[7:] for s in o.addr_roots(REG.findall(x['argv'][1]),j) if s.startswith('symbol:')];assert len(roots)==1
   dst=REG.findall(x['argv'][0]);loads[j]={'index':j,'line':entry.count('\n',0,x['start'])+1,'op':x['op'],'destinations':dst,'address':x['argv'][1],'symbol':roots[0],'text':x['text']};events.append({'run':r['run'],'register':reg,'load_index':j,'component':dst.index(reg)})
  symbols=sorted({l['symbol'] for l in loads.values()});decls={}
  for sym in symbols:
   m=re.search(r'\.shared\s+\.align\s+(\d+)\s+\.b8\s+'+re.escape(sym)+r'\[(\d+)\]',entry)
   if m:decls[sym]={'align':int(m[1]),'bytes':int(m[2])}
  stores=[];aliases=[];unsupported=[]
  for j,x in enumerate(o.ins):
   op=x['op'];a=x['argv']
   if op.startswith(('st.shared','cp.async','atom.shared','red.shared','mbarrier')):
    roots=[s[7:] for s in o.addr_roots(REG.findall(a[0]),j) if s.startswith('symbol:')]
    if not set(roots)&set(symbols):continue
    if op.startswith('cp.async'):aliases.append({'line':entry.count('\n',0,x['start'])+1,'text':x['text']})
    elif op.startswith('st.shared') and op.endswith('.u32') and not x['guard']:
     regs=REG.findall(a[1]);size=4*len(regs);stores.append({'index':j,'line':entry.count('\n',0,x['start'])+1,'op':op,'address':a[0],'sources':regs,'bytes':size,'symbols':roots,'origins':sorted(o.leaves([d for r in regs for d in o.reach(r,j)]))})
    else:unsupported.append({'line':entry.count('\n',0,x['start'])+1,'text':x['text']})
  all_ld=[]
  for j,x in enumerate(o.ins):
   if x['op'].startswith('ld.shared'):
    roots=[s[7:] for s in o.addr_roots(REG.findall(x['argv'][1]),j) if s.startswith('symbol:')]
    if set(roots)&set(symbols):all_ld.append({'index':j,'line':entry.count('\n',0,x['start'])+1,'op':x['op'],'address':x['argv'][1],'destinations':REG.findall(x['argv'][0]),'symbol':next(s for s in roots if s in symbols),'text':x['text']})
  eligible=fb in [1,2,3] and not aliases and not unsupported and len(decls)==len(symbols) and all(x['op'].endswith('.u32') and not o.ins[x['index']]['guard'] for x in all_ld)
  kernels[name]={'FB':fb,'symbols':decls,'shared_MMA_events':events,'MMA_loads':list(loads.values()),'all_loads':all_ld,'stores':stores,'cp_async_aliases':aliases,'unsupported_writes':unsupported,'eligible_shadow':eligible,'grain':'u32 words/vectors: each original byte maps to an independent FP16 element; original 16B vectors map to aligned 32B vectors','non_MMA_loads':len(all_ld)-len(loads)}
 out[fb]=kernels
result={'reference':'V3.1_pack5','fatbins':out,'scope':'original PTX, active Small model; independent shadow preserves original Shared view; exact mirror handles any byte values; inplace requires finite pack-derived byte proof'}
(p/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');(p/'acceptance.json').write_text(json.dumps({'exact':{'bitdiff':0,'maxabs':0,'nonfinite':0},'approximate':{'reference':'V3.1_pack5','PSNR_min_db':50,'maxabs_max':1/64,'nonfinite':0,'sky_sign_changes':0},'timing':'50/80, serial forward ABBA and reverse BAAB; repeat every first-round six-direction winner','no_production_deployment':True},indent=2)+'\n')
print({fb:{n:(len(d['stores']),len(d['MMA_loads']),len(d['all_loads']),d['eligible_shadow']) for n,d in ks.items()} for fb,ks in out.items()})
