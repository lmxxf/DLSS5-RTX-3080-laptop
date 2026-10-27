from pathlib import Path
import json,statistics as st
p=Path(__file__).resolve().parent
def summarize(data,base,candidate):
 a=[r for r in data if r['variant']==base];b=[r for r in data if r['variant']==candidate];mean=lambda rs,k:st.mean(r['metrics'][k] for r in rs);am,bm=mean(a,'gpu_median_ms'),mean(b,'gpu_median_ms');directions={}
 for d in ['forward','reverse']:
  aa=[r for r in a if d in r['name']];bb=[r for r in b if d in r['name']]
  if aa and bb:directions[d]={'baseline_median_ms':mean(aa,'gpu_median_ms'),'candidate_median_ms':mean(bb,'gpu_median_ms'),'gain_percent':100*(1-mean(bb,'gpu_median_ms')/mean(aa,'gpu_median_ms'))}
 return {'runs_per_version':len(a),'baseline_median_ms':am,'candidate_median_ms':bm,'baseline_min_ms':mean(a,'gpu_min_ms'),'candidate_min_ms':mean(b,'gpu_min_ms'),'gain_percent':100*(1-bm/am),'directions':directions}
if __name__=='__main__':
 data=json.loads((p/'bench.json').read_text());assert len(data)==120;result={};lines=['# V2.4 isolated factors and cap controls','','Each process 50 warmup / 80 iterations; means of process GPU medians/minima. Default DVFS. Every candidate is compared to its own bracketing control.','','| Factor | Width | V2.3 median ms | Candidate median ms | V2.3 min ms | Candidate min ms | Time decrease | Forward / reverse |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for v in ['a','bias','b','c','abc']:
  result[v]={}
  for w in [1280,1600,1920]:
   ds=[r for r in data if r['width']==w and f'-{v}-' in r['name']];r=summarize(ds,'baseline',v);result[v][str(w)]=r;d=r['directions'];lines.append(f'| {v} | {w} | {r["baseline_median_ms"]:.5f} | {r["candidate_median_ms"]:.5f} | {r["baseline_min_ms"]:.5f} | {r["candidate_min_ms"]:.5f} | {r["gain_percent"]:.3f}% | {d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}% |')
 caps=json.loads((p/'caps-bench.json').read_text());assert len(caps)==96;result['caps']={};lines+=['','Caps: change one FB relative to ABC (mask15), 1080p forward/reverse ABBA/BAAB.','','| Cap control | ABC median ms | Candidate median ms | ABC min ms | Candidate min ms | Time decrease | Forward / reverse |','|---|---:|---:|---:|---:|---:|---:|']
 for name in sorted(json.loads((p/'caps.json').read_text())):
  ds=[r for r in caps if f'-{name}-' in r['name']];r=summarize(ds,'abc',name);result['caps'][name]=r;d=r['directions'];lines.append(f'| {name} | {r["baseline_median_ms"]:.5f} | {r["candidate_median_ms"]:.5f} | {r["baseline_min_ms"]:.5f} | {r["candidate_min_ms"]:.5f} | {r["gain_percent"]:.3f}% | {d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}% |')
 assert all(r['quality']['bitdiff']==0 and r['metrics']['nonfinite']==0 for r in data+caps)
 (p/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
