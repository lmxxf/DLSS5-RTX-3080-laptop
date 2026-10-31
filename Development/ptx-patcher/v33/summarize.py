from pathlib import Path
import importlib.util,json
p=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('summary',p.parent/'v24/analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out={};eligible=[];lines=['# V3.3 paired serial measurements','','50 warmup / 80 iter, forward ABBA + reverse BAAB; positive = lower latency; means of process GPU medians.','','|Round/candidate|Width|V3.1 ms|Candidate ms|Decrease %|Forward %|Reverse %|','|---|---:|---:|---:|---:|---:|---:|']
for file in ['bench','repeat']:
 f=p/(file+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());out[file]={}
 for v in sorted({r['variant'] for r in rows}-{'baseline'}):
  out[file][v]={}
  for w in [1280,1600,1920]:
   ds=[r for r in rows if r['width']==w and f'-{v}-' in r['name']]
   if len(ds)!=8:continue
   r=m.summarize(ds,'baseline',v);out[file][v][str(w)]=r;d=r['directions'];lines.append(f'|{file}/{v}|{w}|{r["baseline_median_ms"]:.5f}|{r["candidate_median_ms"]:.5f}|{r["gain_percent"]:.3f}|{d["forward"]["gain_percent"]:.3f}|{d["reverse"]["gain_percent"]:.3f}|')
  if file=='bench' and len(out[file][v])==3 and all(r['directions'][d]['gain_percent']>0 for r in out[file][v].values() for d in ['forward','reverse']):eligible.append(v)
(p/'timing-summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'timing-summary.md').write_text('\n'.join(lines)+'\n');(p/'repeat-eligible.json').write_text(json.dumps(eligible,indent=2)+'\n');print('repeat eligible',eligible)
