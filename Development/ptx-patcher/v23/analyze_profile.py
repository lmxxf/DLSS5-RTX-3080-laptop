from pathlib import Path
import json,statistics as st,collections,re,numpy as np,sys
p=Path(__file__).resolve().parent;prefix=(sys.argv[1]+'-') if len(sys.argv)>1 else '';resources=json.loads((p.parent/'v22/resources.json').read_text())['combo'];fb={name:int(i) for i,r in resources.items() for name in r['kernels']}
all_results={}
for w in [1280,1920]:
 rows=[]
 for l in (p/f'{prefix}events-{w}.csv').read_text().splitlines():
  if not l.startswith('KERNEL,'):continue
  x=l.split(',');frame=int(x[1]);
  if frame<50:continue
  rows.append({'frame':frame,'call':int(x[2]),'name':x[4],'FB':fb.get(x[4],-1),'grid':list(map(int,x[5:8])),'block':list(map(int,x[8:11])),'dynamic_shared':int(x[11]),'gpu_ms':float(x[12]),'start':int(x[13]),'end':int(x[14])})
 frames=collections.defaultdict(list)
 for r in rows:frames[r['frame']].append(r)
 assert len(frames)==20;count=len(next(iter(frames.values())));assert all(len(rs)==count for rs in frames.values());calls=[]
 for call in range(count):
  rs=[r for r in rows if r['call']==call];r=rs[0];assert all((s['name'],s['grid'],s['block'])==(r['name'],r['grid'],r['block']) for s in rs)
  calls.append({k:v for k,v in r.items() if k not in ['frame','gpu_ms','start','end']}|{'median_ms':st.median(s['gpu_ms'] for s in rs),'mean_ms':st.mean(s['gpu_ms'] for s in rs)})
 byfb={};byname={}
 for field,out in [('FB',byfb),('name',byname)]:
  for key in sorted(set(r[field] for r in rows),key=str):
   samples=[sum(r['gpu_ms'] for r in rs if r[field]==key) for rs in frames.values()];out[str(key)]={'median_ms':st.median(samples),'mean_ms':st.mean(samples),'calls_per_frame':sum(r[field]==key for r in calls)}
 total=st.median(sum(r['gpu_ms'] for r in rs) for rs in frames.values());span=st.median((max(r['end'] for r in rs)-min(r['start'] for r in rs))/1e6 for rs in frames.values());kind={}
 for tag in ['tilesync','wait','chained']:
  names=[n for n in byname if tag in n];kind[tag]={'unique_names':len(names),'calls':sum(byname[n]['calls_per_frame'] for n in names),'mean_ms':sum(byname[n]['mean_ms'] for n in names)}
 all_results[str(w)]={'calls_per_frame':count,'unique_kernels':len(byname),'sum_kernel_median_ms':total,'first_to_last_span_median_ms':span,'median_interkernel_gap_ms':st.median((max(r['end'] for r in rs)-min(r['start'] for r in rs))/1e6-sum(r['gpu_ms'] for r in rs) for rs in frames.values()),'sum_kernel_mean_ms':st.mean(sum(r['gpu_ms'] for r in rs) for rs in frames.values()),'by_FB':byfb,'by_kernel':byname,'synchronization_variants':kind,'calls':calls}
 print(w,'sum',total,'span',span,'FB',[(i,round(v['median_ms'],4)) for i,v in sorted(byfb.items(),key=lambda t:-t[1]['median_ms'])]);print('top',[(n,round(v['median_ms'],4)) for n,v in sorted(byname.items(),key=lambda t:-t[1]['median_ms'])[:8]])
 # Correctness against trace-only hook run (same 50/20 temporal configuration).
 root=Path('/mnt/c/DLSS5-5090-dll');a=np.fromfile(root/f'v23-{prefix}events-{w}.rgb32',np.uint32);b=np.fromfile(root/f'v23-trace-{w}.rgb32',np.uint32);assert a.shape==b.shape;all_results[str(w)]['event_vs_trace_bitdiff']=int(np.count_nonzero(a!=b));assert all_results[str(w)]['event_vs_trace_bitdiff']==0
(p/f'{prefix}profile.json').write_text(json.dumps(all_results,indent=2)+'\n')
lines=['# V2.2 actual NVAPI D3D12 launch ledger','','50 warmup / 20 measured frames; D3D12 timestamps bracket each unmodified single-kernel LaunchCuKernelChain call. Native CUDA export hooks observed no launches; NVAPI CreateCuModule/CreateCuFunction resolves names. GPU timestamp intervals include dispatch-local overhead; they are not instruction stall counters.','','| Width | FB | Calls/frame | Median aggregate ms |','|---:|---:|---:|---:|']
for w,r in all_results.items():
 for fb,x in sorted(r['by_FB'].items(),key=lambda t:-t[1]['median_ms']):lines.append(f'| {w} | {fb} | {x["calls_per_frame"]} | {x["median_ms"]:.6f} |')
for w,r in all_results.items():
 lines+=['',f'## {w}: all actual launches','','| Order | FB | Kernel | Grid | Block | Median ms |','|---:|---:|---|---|---|---:|']
 for x in r['calls']:lines.append(f'| {x["call"]} | {x["FB"]} | {x["name"]} | {x["grid"]} | {x["block"]} | {x["median_ms"]:.6f} |')
(p/f'{prefix}kernel-ledger.md').write_text('\n'.join(lines)+'\n')
