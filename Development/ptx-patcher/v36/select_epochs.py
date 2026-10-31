from pathlib import Path
import json,collections
from analysis_common import Origin,entries
p=Path(__file__).resolve().parent;plans=json.loads((p.parent/'v35/plans.json').read_text());old=json.loads((p.parent/'v34/shared-layout-audit.json').read_text());chosen={};decisions=[]
for fb in [2,3]:
 candidates=[];parts=dict(entries((p/f'artifacts/raw/fb{fb:02}.ptx').read_text()))
 for n,k in plans.items():
  if k['FB']!=fb:continue
  o=Origin(parts[n]);loadindex={l['line']:l['index'] for l in k['MMA_loads']};stores={s['line']:s for s in k['stores']};groups=collections.defaultdict(list)
  for m in old['kernels'][n]['load_mappings']:
   if m['load_line'] not in loadindex or m['unresolved_or_ambiguous_bytes'] or m['unguarded_store_evaluations_unresolved'] or not m['producer_store_lines']:continue
   j=loadindex[m['load_line']];ss=[stores.get(line) for line in m['producer_store_lines']]
   if any(s is None or o.owner[s['index']]!=o.owner[j] or s['index']>=j for s in ss):continue
   groups[m['producer_barrier_index']].append(m)
  for epoch,mm in groups.items():
   loads={loadindex[m['load_line']] for m in mm};lines={line for m in mm for line in m['producer_store_lines']};events=[e for e in k['shared_MMA_events'] if e['load_index'] in loads]
   kk=k|{'MMA_loads':[l for l in k['MMA_loads'] if l['index'] in loads],'stores':[s for s in k['stores'] if s['line'] in lines],'shared_MMA_events':events};candidates.append((len(events),n,epoch,kk))
 if candidates:
  score,n,epoch,k=max(candidates,key=lambda z:(z[0],z[1]));chosen[n]=k;decisions.append({'FB':fb,'kernel':n,'epoch_instruction':epoch,'MMA_static_events':score,'producer_store_sites':len(k['stores']),'load_sites':len(k['MMA_loads']),'selection':'largest fully mapped same-basic-block local publication segment per FB, before timing; old view retained elsewhere'})
(p/'epoch-plans.json').write_text(json.dumps(chosen,indent=2)+'\n');(p/'epoch-selection.json').write_text(json.dumps(decisions,indent=2)+'\n');print(decisions)
