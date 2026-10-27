from pathlib import Path
import sys,json,statistics as st
p=Path(__file__).resolve().parent
import importlib.util
spec=importlib.util.spec_from_file_location('v24_analyze',p.parent/'v24/analyze.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);summarize=mod.summarize
# Executed as __main__, importing the v24 module named analyze is intentional.
primary=json.loads((p/'bench.json').read_text());single=json.loads((p/'fb0-bench.json').read_text());assert len(primary)==24 and len(single)==16;result={};lines=['# V2.5 Hybrid controls — negative result','','50 warmup / 80 iterations, forward ABBA and reverse BAAB. Means of per-process GPU medians/minima; default DVFS, no clocks locked. Every output is compared against same-configuration V2.4.','','| Scope | Width | V2.4 median ms | Candidate median ms | V2.4 min ms | Candidate min ms | Time decrease | Forward / reverse |','|---|---:|---:|---:|---:|---:|---:|---:|']
for tag,rs,v in [('all_FB',primary,'hybrid'),('FB00_only',single,'fb0')]:
 result[tag]={}
 for w in sorted(set(x['width'] for x in rs)):
  r=summarize([x for x in rs if x['width']==w],'baseline',v);result[tag][str(w)]=r;d=r['directions'];lines.append(f'| {tag} | {w} | {r["baseline_median_ms"]:.5f} | {r["candidate_median_ms"]:.5f} | {r["baseline_min_ms"]:.5f} | {r["candidate_min_ms"]:.5f} | {r["gain_percent"]:.3f}% | {d["forward"]["gain_percent"]:.3f}% / {d["reverse"]["gain_percent"]:.3f}% |')
assert all(x['quality']['bitdiff']==0 and x['metrics']['nonfinite']==0 for x in primary+single)
(p/'summary.json').write_text(json.dumps(result,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
