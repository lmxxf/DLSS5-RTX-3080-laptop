from pathlib import Path
import json,statistics as st
p=Path(__file__).resolve().parent;rows=json.loads((p/'bench.json').read_text());assert len(rows)==72
assert all(r['quality']['bitdiff']==0 and r['metrics']['nonfinite']==0 for r in rows)
summary={};lines=['# V2.2 single-factor and combined controls','','RTX 3080 Laptop, default DVFS; each process 50 warmup / 80 iterations. Each tier and factor has forward ABBA and reverse BAAB (four runs per version). Values below are means of per-process GPU medians/minima, not pooled frame medians. peak=1 RGB exact comparison uses the same 50/80 baseline output.','','| Factor | Size | V2.1 median ms | Candidate median ms | V2.1 min ms | Candidate min ms | Speed ratio | Forward / reverse gain |','|---|---:|---:|---:|---:|---:|---:|---:|']
for v in ['async','swar','combo']:
 summary[v]={}
 for w in [1280,1600,1920]:
  a=[r for r in rows if r['width']==w and f'-{v}-' in r['name']];base=[r for r in a if r['variant']=='baseline'];cand=[r for r in a if r['variant']==v]
  def mean(rs,k):return st.mean(r['metrics'][k] for r in rs)
  b=mean(base,'gpu_median_ms');c=mean(cand,'gpu_median_ms');dirs={}
  for dr in ['forward','reverse']:
   ba=[r for r in base if r['name'].startswith(dr)];ca=[r for r in cand if r['name'].startswith(dr)];dirs[dr]={'baseline_median_ms':mean(ba,'gpu_median_ms'),'candidate_median_ms':mean(ca,'gpu_median_ms'),'gain_percent':100*(1-mean(ca,'gpu_median_ms')/mean(ba,'gpu_median_ms'))}
  summary[v][str(w)]={'baseline_median_ms':b,'candidate_median_ms':c,'baseline_min_ms':mean(base,'gpu_min_ms'),'candidate_min_ms':mean(cand,'gpu_min_ms'),'speed_ratio':b/c,'gain_percent':100*(1-c/b),'directions':dirs,'bitdiff':0,'maxabs':0,'PSNR':'infinite (bit identical)'}
  r=summary[v][str(w)];lines.append(f'| {v} | {w} | {b:.4f} | {c:.4f} | {r["baseline_min_ms"]:.4f} | {r["candidate_min_ms"]:.4f} | {b/c:.4f}x | {dirs["forward"]["gain_percent"]:.2f}% / {dirs["reverse"]["gain_percent"]:.2f}% |')
res=json.loads((p/'resources.json').read_text());lines+=['','All exports, static SASS counts (not only dynamically active kernels):','','| FB | V2.1 STACK / LDL+STL | Async | SWAR | Combo |','|---|---:|---:|---:|---:|']
for i in range(7):
 fields=[]
 for v in ['baseline','async','swar','combo']:
  r=res[v][str(i)];fields.append(f'{r["max_stack"]} B / {r["totals"]["LDL"]+r["totals"]["STL"]}')
 lines.append(f'| {i:02} | '+ ' | '.join(fields)+' |')
lines+=['','Do not claim zero-stack: O4 spilling increases in FB01/02/05 despite fewer PTX temporaries. FB04 remains 80 B. Async replaces 316 immediate completion pairs with balanced native mbarrier arrivals; four pre-existing non-bulk groups in FB04 remain unchanged.','', 'A preliminary harness compared baseline 1/1 against baseline 50/80 and detected temporal-frame differences (61.786 dB at 720p). These configurations are now separate golds; this is not a candidate mismatch. All 72 timing runs compare against 50/80 gold and are bit identical.','', 'Telemetry starts during forward 720p, after the earliest timed processes; no fixed clocks or power locks were applied. Raw process order and min/median/wall results are in bench.json.']
(p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(p/'results.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:16]))
