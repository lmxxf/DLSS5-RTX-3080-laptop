from pathlib import Path
import json,importlib.util
p=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('summary24',p.parent/'v24/analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows=json.loads((p/'bench.json').read_text());extra=json.loads((p/'extra-bench.json').read_text());assert len(rows)==120 and len(extra)==40
out={};lines=['# V2.7 factor, cap and conditional controls','','Every process: 50 warmup / 80 iter; forward ABBA and reverse BAAB. Means of process GPU median/min. No clock lock; compare each candidate with its own bracketing control.','','| Candidate | Width | V2.6 median ms | Candidate median ms | V2.6 min ms | Candidate min ms | Decrease | Forward / reverse |','|---|---:|---:|---:|---:|---:|---:|---:|']
for v in ['a','b','ab','cap0-168','cap1-192']:
 out[v]={}
 for w in [1280,1600,1920]:
  ds=[r for r in rows if r['width']==w and f'-{v}-' in r['name']];r=m.summarize(ds,'baseline',v);out[v][str(w)]=r;d=r['directions'];lines.append(f'| {v} | {w} | {r["baseline_median_ms"]:.5f} | {r["candidate_median_ms"]:.5f} | {r["baseline_min_ms"]:.5f} | {r["candidate_min_ms"]:.5f} | {r["gain_percent"]:.3f}% | {d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}% |')
lines+=['','Conditional comparisons below use four-kernel cap168 as reference, not V2.6.','','| Addition/change | Width | Four-kernel cap median | Candidate median | Decrease | Forward / reverse |','|---|---:|---:|---:|---:|---:|'];out['conditional']={}
for case,v,ws in [('add-A','a_cap0',[1280,1600,1920]),('prefix-only','prefix168',[1280,1920])]:
 out['conditional'][case]={}
 for w in ws:
  ds=[r for r in extra if r['width']==w and r['name'].startswith(case+'-')];r=m.summarize(ds,'cap0-168',v);out['conditional'][case][str(w)]=r;d=r['directions'];lines.append(f'| {case} | {w} | {r["baseline_median_ms"]:.5f} | {r["candidate_median_ms"]:.5f} | {r["gain_percent"]:.3f}% | {d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}% |')
assert all(r['quality']['bitdiff']==0 and r['metrics']['nonfinite']==0 for r in rows+extra)
lines+=['','Recommendation: cap168 only for prefix, inpview, ds_wait, outview in FB00. Keep post/upsample and all other kernels unchanged. A/B and C64 raised caps are not selected; adding A to the winning cap configuration reverses sign at 720p/1080p. Prefix-only is slower than adjusting all four in both tested tiers/directions.']
(p/'summary.json').write_text(json.dumps(out,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n')
