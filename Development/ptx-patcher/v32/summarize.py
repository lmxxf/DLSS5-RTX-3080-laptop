from pathlib import Path
import sys,json,importlib.util
p=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('summary',p.parent/'v24/analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
out={};eligible=[];lines=['# V3.2 data-first paired timing audit','','50 warmup / 80 iter. Means of independent process GPU medians; default DVFS. Positive means lower latency. Entire excluded screening round remains in excluded-timing.json, complete replacements in first.json.','','|Candidate|Width|Base ms|Candidate ms|Decrease %|Forward %|Reverse %|','|---|---:|---:|---:|---:|---:|---:|']
for file in ['first','caps','arithmetic','repeat']:
 path=p/(file+'.json')
 if not path.exists():continue
 rows=json.loads(path.read_text());out[file]={}
 for v in sorted({r['variant'] for r in rows}-{'baseline'}):
  out[file][v]={}
  for w in [1280,1600,1920]:
   ds=[r for r in rows if r['width']==w and f'-{v}-' in r['name']]
   if len(ds)!=8:continue
   r=m.summarize(ds,'baseline',v);out[file][v][str(w)]=r;directions=r['directions'];lines.append(f'|{file}/{v}|{w}|{r["baseline_median_ms"]:.5f}|{r["candidate_median_ms"]:.5f}|{r["gain_percent"]:.3f}|{directions["forward"]["gain_percent"]:.3f}|{directions["reverse"]["gain_percent"]:.3f}|')
  complete=out[file][v]
  if file!='repeat' and json.loads((p/'candidates.json').read_text())[v]['sha256']!=json.loads((p/'candidates.json').read_text())['baseline']['sha256'] and len(complete)==3 and all(r['directions'][direction]['gain_percent']>0 for r in complete.values() for direction in ['forward','reverse']):eligible.append(v)
(p/'timing-summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'timing-summary.md').write_text('\n'.join(lines)+'\n');(p/'repeat-eligible.json').write_text(json.dumps(eligible,indent=2)+'\n');print('repeat eligible',eligible)
