from pathlib import Path
import json,hashlib
from check_run import check_variant
p=Path(__file__).resolve().parent;rows={};summary={};lines=['# Phase19 two-candidate three-tier ABBA,50warmup/80iter','','A=Phase18;B=W16 FFN FP16 append. Report mean of run medians only as a compact comparison;raw logs retain paired min/median/Wall/profile.','', '| Mask | Width | A1 | B1 | B2 | A2 | meanA | meanB | B−A ms |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for mask in [1,3]:
 sets=[]
 for part in ['baseline-a','candidate-b','candidate-b2','baseline-a2']:
  rr=check_variant(part+'-m'+str(mask),True);rows.update(rr);sets.append(rr)
 if not all(len(r)==3 for r in sets):continue
 ss={}
 for w in [1280,1600,1920]:
  rr=[next(x for x in a.values() if x['width']==w) for a in sets];v=[x['gpu_median'] for x in rr];aa=(v[0]+v[3])/2;bb=(v[1]+v[2])/2;ss[w]={'medians_A_B_B_A':v,'A_mean':aa,'B_mean':bb,'delta_B_minus_A':bb-aa,'speed_ratio':aa/bb};lines.append(f'| {mask} | {w} | '+' | '.join(f'{x:.3f}' for x in v)+f' | {aa:.4f} | {bb:.4f} | {bb-aa:+.4f} |')
 summary[mask]=ss
for name in ['quick-m1','quick-m3']:rows.update(check_variant(name,True))
(p/'results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(p/'summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
