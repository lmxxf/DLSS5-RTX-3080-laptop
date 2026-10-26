from pathlib import Path
import json
from check_run import check_variant
p=Path(__file__).resolve().parent;rows={};sets=[]
for name in ['baseline-a-final','candidate-b-final','candidate-b2-final','baseline-a2-final']:
 d=check_variant(name,True);rows.update(d);sets.append(d)
(p/'final-results.json').write_text(json.dumps(rows,indent=2)+'\n');summary={};lines=['# Final Phase18 vsPhase17,50/80 three-tier ABBA','','A=Phase17;B=ByteOut+C32V+QKV mask7,no C256 cap. GPU min/median/wall kept in the same run,PROFILE_TOTAL is an independent instrumented frame.','', '| Width | A1 median | B1 median | B2 median | A2 median | meanA | meanB | Speed ratio |','|---|---:|---:|---:|---:|---:|---:|---:|']
for w in [1280,1600,1920]:
 if not all(any(x['width']==w for x in d.values()) for d in sets):continue
 rr=[next(x for x in d.values() if x['width']==w) for d in sets];v=[x['gpu_median'] for x in rr];aa=(v[0]+v[3])/2;bb=(v[1]+v[2])/2;summary[w]={'medians_A_B_B_A':v,'A_mean':aa,'B_mean':bb,'speed_ratio':aa/bb,'delta_B_minus_A':bb-aa};lines.append(f'| {w} | '+' | '.join(f'{t:.3f}' for t in v)+f' | {aa:.4f} | {bb:.4f} | {aa/bb:.4f}× |')
lines+=['','## Six C32 and nine Wave2 profiles','','| Run | Width | Kernel | ms | REG | LOCAL | Shared | OccW |','|---|---:|---|---:|---:|---:|---:|---:|']
for name,r in rows.items():
 for n,k in r['kernels'].items():
  if n.startswith(('c32_wave1','c64_wave2','c128_wave2','c256_wave2')):lines.append(f'| {name} | {r["width"]} | {n} | {k["ms"]:.6f} | {int(k["regs"])} | {int(k["lmem"])} | {int(k["smem"])} | {int(k["occw"])} |')
(p/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n');(p/'final-summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines[:10]))
