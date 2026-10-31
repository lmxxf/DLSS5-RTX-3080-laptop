from pathlib import Path
import json,collections
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());selected=[];rejected={}
for n,q in r['up_pair_all'].items():
 b=r['baseline'][n];bad=[f for f in ['REG','STACK','STL','LDL'] if q[f]>b[f]]
 if q['resident_CTA_per_SM']<b['resident_CTA_per_SM']:bad.append('resident_CTA_per_SM')
 if bad:rejected[n]=bad
 else:selected.append(n)
assert selected
spec=json.loads((p/'specs.json').read_text());spec['up_pair_clean']={'fbs':sorted({r['baseline'][n]['FB'] for n in selected}),'zero_fbs':[4,5,6],'up':True,'up_entries':selected,'branches':[5]};(p/'specs.json').write_text(json.dumps(spec,indent=2)+'\n');(p/'up-clean-selection.json').write_text(json.dumps({'rule':'before timing, exact active entry filter: REG/STACK/STL/LDL do not increase and API CTA/SM does not fall; all unprofiled entries stay baseline','selected':selected,'rejected':rejected},indent=2)+'\n');print('UP clean entries',len(selected),'rejected',len(rejected))
