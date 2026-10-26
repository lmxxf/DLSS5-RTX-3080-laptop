from pathlib import Path
import json,re,numpy as np,hashlib
from check_run import check_variant
p=Path(__file__).resolve().parent;rows={};summary={};quick=json.loads((p/'site-quick-results.json').read_text())
for site in ['contract','result','v','av','byteout','c32-prefix','c32-v']:
 names=['baseline-'+site+'-a','site-'+site+'-b','site-'+site+'-b2','baseline-'+site+'-a2'];sets=[]
 for name in names:
  d=check_variant(name,False);sets.append(d);rows.update(d)
 if not all(len(d)==3 for d in sets):continue
 result={}
 for w in [1280,1600,1920]:
  runs=[next(v for v in d.values() if v['width']==w) for d in sets]
  assert all(x['bitdiff']==x['invalid']==x['first_last']==0 and x['LMem0'] for x in runs),(site,w)
  vals=[x['gpu_median'] for x in runs];aa=(vals[0]+vals[3])/2;bb=(vals[1]+vals[2])/2
  changed={n:{'A_regs':a['regs'],'B_regs':runs[1]['kernels'][n]['regs'],'A_occ':a['occw'],'B_occ':runs[1]['kernels'][n]['occw']} for n,a in runs[0]['kernels'].items() if a['regs']!=runs[1]['kernels'][n]['regs'] or a['occw']!=runs[1]['kernels'][n]['occw']}
  result[w]={'medians_A_B_B_A':vals,'A_mean':aa,'B_mean':bb,'delta_B_minus_A_ms':bb-aa,'speed_ratio':aa/bb,'resource_changes':changed}
 summary[site]=result
(p/'site-results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'site-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# Site-local three-tier ABBA,50warmup/80iter','','GPU median sequences A1/B1/B2/A2. Delta is mean ofB medians minus mean ofA medians,not one measured frame. Raw grouped min/median/wall/profile remain in logs and site-results.json.','', '| Site | Width | A1 | B1 | B2 | A2 | B−A ms |','|---|---:|---:|---:|---:|---:|---:|']
for site,rr in summary.items():
 for w,x in rr.items():lines.append(f'| {site} | {w} | '+' | '.join(f'{v:.3f}' for v in x['medians_A_B_B_A'])+f' | {x["delta_B_minus_A_ms"]:+.4f} |')
(p/'site-summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
