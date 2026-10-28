from pathlib import Path
import json,importlib.util,sys
p=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('a',p.parent/'v24/analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=sys.argv[1] if len(sys.argv)>1 else 'bench';rows=json.loads((p/(f+'.json')).read_text());out={};lines=['# V2.9 paired controls','','50 warmup / 80 iter, forward ABBA and reverse BAAB; mean of process GPU medians, paired V2.7 reference.','','|Candidate|Width|Baseline ms|Candidate ms|Decrease|Forward / reverse|','|---|---:|---:|---:|---:|---:|']
for v in sorted({r['variant'] for r in rows}-{'baseline'}):
 out[v]={}
 for w in (1280,1600,1920):
  ds=[r for r in rows if r['width']==w and f'-{v}-' in r['name']]
  if len(ds)!=8:continue
  r=m.summarize(ds,'baseline',v);out[v][str(w)]=r;d=r['directions'];lines.append(f'|{v}|{w}|{r["baseline_median_ms"]:.5f}|{r["candidate_median_ms"]:.5f}|{r["gain_percent"]:.3f}%|{d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}%|')
(p/(f+'-summary.json')).write_text(json.dumps(out,indent=2)+'\n');(p/(f+'-results.md')).write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
