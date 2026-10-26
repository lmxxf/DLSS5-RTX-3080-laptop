from pathlib import Path
import json
from check_run import check_variant
p=Path(__file__).resolve().parent;rows={};summary={}
for name,c in json.loads((p/'control-quick-results.json').read_text()).items():
 if name=='pack2' or not c['resource_gate']:continue
 rr=[]
 for suffix in ['a','b','b2','a2']:
  d=check_variant('screen-'+name+'-'+suffix,True);rows.update(d)
  if len(d)!=1:break
  rr.append(next(iter(d.values())))
 if len(rr)!=4:continue
 vals=[r['gpu_median'] for r in rr];aa=(vals[0]+vals[3])/2;bb=(vals[1]+vals[2])/2;summary[name]={'medians_A_B_B_A':vals,'A_mean':aa,'B_mean':bb,'delta_B_minus_A':bb-aa,'C256_B_resources':{n:k for n,k in rr[1]['kernels'].items() if n.startswith('c256')}}
(p/'screen-results.json').write_text(json.dumps(rows,indent=2)+'\n');(p/'screen-summary.json').write_text(json.dumps(summary,indent=2)+'\n');lines=['# 1080p controls against pack2 (ByteOut+C32V),50/80 ABBA','','| Control | A1 | B1 | B2 | A2 | meanB−meanA ms |','|---|---:|---:|---:|---:|---:|']
for n,r in summary.items():lines.append(f'| {n} | '+' | '.join(f'{v:.3f}' for v in r['medians_A_B_B_A'])+f' | {r["delta_B_minus_A"]:+.4f} |')
(p/'screen-summary.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
