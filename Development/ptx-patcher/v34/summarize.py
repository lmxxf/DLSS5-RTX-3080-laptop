from pathlib import Path
import json,re,statistics as st
p=Path(__file__).resolve().parent
def direction(row):
 match=re.match(r'^(?:repeat-)?(forward|reverse)-',row['name']);assert match,row['name'];return match[1]
def summarize(rows,base,candidate):
 a=[r for r in rows if r['variant']==base];b=[r for r in rows if r['variant']==candidate];mean=lambda rs,k:st.mean(r['metrics'][k] for r in rs);am,bm=mean(a,'gpu_median_ms'),mean(b,'gpu_median_ms');ds={}
 for d in ['forward','reverse']:
  aa=[r for r in a if direction(r)==d];bb=[r for r in b if direction(r)==d];assert len(aa)==len(bb)==2
  ds[d]={'baseline_median_ms':mean(aa,'gpu_median_ms'),'candidate_median_ms':mean(bb,'gpu_median_ms'),'gain_percent':100*(1-mean(bb,'gpu_median_ms')/mean(aa,'gpu_median_ms'))}
 return {'runs_per_version':len(a),'baseline_median_ms':am,'candidate_median_ms':bm,'baseline_min_ms':mean(a,'gpu_min_ms'),'candidate_min_ms':mean(b,'gpu_min_ms'),'gain_percent':100*(1-bm/am),'directions':ds}
out={};eligible=[];lines=['# V3.4 paired serial measurements','','50 warmup / 80 iter, forward ABBA + reverse BAAB; positive = lower latency; means of process GPU medians.','','|Round/candidate|Width|V3.1 ms|Candidate ms|Decrease %|Forward %|Reverse %|','|---|---:|---:|---:|---:|---:|---:|']
for file in ['bench','repeat']:
 f=p/(file+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());out[file]={}
 for v in sorted({r['variant'] for r in rows}-{'baseline'}):
  out[file][v]={}
  for w in [1280,1600,1920]:
   ds=[r for r in rows if r['width']==w and f'-{v}-' in r['name']]
   if len(ds)!=8:continue
   r=summarize(ds,'baseline',v);out[file][v][str(w)]=r;d=r['directions'];lines.append(f'|{file}/{v}|{w}|{r["baseline_median_ms"]:.5f}|{r["candidate_median_ms"]:.5f}|{r["gain_percent"]:.3f}|{d["forward"]["gain_percent"]:.3f}|{d["reverse"]["gain_percent"]:.3f}|')
  if file=='bench' and len(out[file][v])==3 and all(r['directions'][d]['gain_percent']>0 for r in out[file][v].values() for d in ['forward','reverse']):eligible.append(v)
(p/'timing-summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'timing-summary.md').write_text('\n'.join(lines)+'\n');(p/'repeat-eligible.json').write_text(json.dumps(eligible,indent=2)+'\n');print('repeat eligible',eligible)
