from pathlib import Path
import sys,json,math,collections
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));from sass_loops import parse_sass
inv=json.loads((p/'natural-loops.json').read_text());ids=json.loads((p/'counter-build.json').read_text())['ids'];counts=json.loads((p/'counter-runs.json').read_text());params=json.loads((p/'launch-params.json').read_text());sass={}
for fb in [4,5]:
 for ch in (p/f'artifacts/base-fb{fb:02}.sass').read_text().split('Function : ')[1:]:
  n=ch.splitlines()[0].strip()
  if n in inv:sass[n]=parse_sass(ch)
out={}
for w,r in counts.items():
 result={};totals={str(fb):collections.Counter() for fb in [0,4,5]}
 # Exact shape agreement between instrumented frame 1 and parameter-capture frame 50.
 observed=[]
 for line in (p/f'count-{w}.csv').read_text().splitlines():
  if line.startswith('KERNEL,1,'):
   a=line.split(',');observed.append({'name':a[4],'grid':list(map(int,a[5:8])),'block':list(map(int,a[8:11]))})
 assert observed==params[w]['calls']
 for name,id in ids.items():
  cs=[c for c in observed if c['name']==name];warps=sum(math.prod(c['grid'])*math.prod(c['block'])//32 for c in cs);c=r['counts'].get(str(id),{});fb=inv[name]['FB'];loops=inv[name]['loops'];visits=[c.get(str(j+1),0) for j in range(len(loops))];h=c.get('0',0);prmt=c.get('3',0);unmapped=c.get('6',0);mapped=c.get('7',0)
  assert prmt==2*(unmapped+mapped);assert c.get('5',0)==2*unmapped
  row={'FB':fb,'calls':len(cs),'launched_warps':warps,'measured_HMMA_warp_instructions':h,'HMMA_per_launched_warp':h/warps if warps else 0,'loops':[{'header':l['header'],'MMA_sites':l['mma_sites'],'header_warp_visits':v,'mean_iterations_per_launched_warp':v/warps if warps else 0} for l,v in zip(loops,visits)],'measured_decoder_PTX_PRMT':prmt,'measured_decoder_PTX_integer_mov':c.get('4',0),'measured_decoder_PTX_HMUL2':c.get('5',0),'unmapped_pair_events':unmapped,'mapped_pair_events':mapped,'hybrid_decoder_PRMT_semantic_prediction':prmt-unmapped}
  total=totals[str(fb)];total.update({'HMMA_measured':h,'decoder_PRMT_PTX_measured':prmt,'decoder_INT_MOV_PTX_measured':c.get('4',0),'decoder_HMUL2_PTX_measured':c.get('5',0),'unmapped_pair_events':unmapped,'mapped_pair_events':mapped})
  if name in sass:
   ins,blocks,sloops=sass[name];sloops=[l for l in sloops if l['mma_sites']];assert len(sloops)==len(loops)
   reachable=set();todo=[0]
   while todo:
    n=todo.pop()
    if n in reachable:continue
    reachable.add(n);todo.extend(blocks[n]['succ'])
   def histogram(nodes):
    ctr=collections.Counter()
    for n in nodes:
     for x in blocks[n]['ins']:
      if x['guard']=='@!PT':continue
      ctr[x['sass_op'].split('.')[0]]+=1
    return ctr
   static=histogram(reachable);model=collections.Counter({k:v*warps for k,v in static.items()})
   for l,sl,v in zip(loops,sloops,visits):
    assert 2*l['mma_sites']==sl['mma_sites'];extra=v-warps;assert extra>=0
    for k,n in histogram(sl['nodes']).items():model[k]+=n*extra
   assert model.get('HMMA',0)==h,(name,model.get('HMMA'),h)
   row['compute_loop_expanded_SASS_model']=dict(model);row['auxiliary_model_total']=sum(model.values())-h;row['auxiliary_model_scope']='reachable block union; compute loops weighted by runtime warp visits; non-MMA loops once; retries/predication/divergent-path activity not hardware-counted'
   total.update({'auxiliary_SASS_model':row['auxiliary_model_total'],'PRMT_SASS_model':model.get('PRMT',0)})
  result[name]=row
 clock=1695 if w=='1280' else 1605
 for total in totals.values():total['TC_floor_ms_assuming_4_cycles']=4*total['HMMA_measured']/(48*clock*1000)
 out[w]={'height':r['height'],'counter_output_bitdiff':r['bitdiff'],'assumed_SM_clock_MHz':clock,'kernels':result,'totals':{k:dict(v) for k,v in totals.items()}}
(p/'dynamic-ledger.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# Loop-corrected workload ledger','','HMMA and MMA-decoder PTX events below are measured by an independent instrumented V2.4 DLL (one lane per converged MMA warp), with exact RGB agreement. Loop headers are measured directly. SASS auxiliary totals are a compute-loop-expanded model, not a hardware dynamic instruction counter. The model assumes one pass through non-MMA loops and unions conditional blocks; spin retries and actual predication/divergence are not measured. Instrumented timings are never used for speed claims.','','| Width | FB | Measured HMMA warp instructions | Decoder PRMT PTX events | Loop-expanded auxiliary SASS model | TC floor ms at assumed clock |','|---:|---:|---:|---:|---:|---:|']
for w,r in out.items():
 for fb,t in r['totals'].items():lines.append(f'| {w} | {fb} | {t["HMMA_measured"]:,} | {t["decoder_PRMT_PTX_measured"]:,} | {t.get("auxiliary_SASS_model","not modeled")} | {t["TC_floor_ms_assuming_4_cycles"]:.6f} |')
lines+=['','## Measured compute-loop trips per launched warp','','| Width | Kernel | Loop trips | HMMA / warp |','|---:|---|---|---:|']
for w,r in out.items():
 for n,t in r['kernels'].items():
  if t['FB'] not in [4,5] or not t['loops']:continue
  lines.append(f'| {w} | {n} | '+', '.join(f'{x["mean_iterations_per_launched_warp"]:g}' for x in t['loops'])+f' | {t["HMMA_per_launched_warp"]:g} |')
(p/'dynamic-ledger.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:18]))
