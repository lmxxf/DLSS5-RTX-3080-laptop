from pathlib import Path
import json
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());selected=[];rejected={}
for n,q in r['up_pair_cfg_all'].items():
 b=r['baseline'][n];bad=[k for k in ['REG','STACK','STL','LDL'] if q[k]>b[k]]
 if q['resident_CTA_per_SM']<b['resident_CTA_per_SM']:bad.append('resident_CTA_per_SM')
 if bad:rejected[n]=bad
 else:selected.append(n)
assert selected;sp=json.loads((p/'specs.json').read_text());sp['up_pair_cfg_clean']={'fbs':sorted({r['baseline'][n]['FB'] for n in selected}),'zero_fbs':[4,5,6],'up':True,'up_entries':selected,'cfg':True,'branches':[5]};sp['joint_up_fb2345_pack4_fb2356']={**sp['up_pair_fb2345'],'fbs':[2,3,4,5,6],'pack4':[2,3,5,6]};sp['joint_up_cfg_pack4_fb2356']={**sp['up_pair_cfg_clean'],'fbs':sorted(set(sp['up_pair_cfg_clean']['fbs'])|{2,3,5,6}),'pack4':[2,3,5,6]};(p/'specs.json').write_text(json.dumps(sp,indent=2)+'\n');(p/'cfg-clean-selection.json').write_text(json.dumps({'rule':'before timing, actual CFG-all cubin: REG/STACK/STL/LDL nonincrease, API CTA/SM nondecrease; unprofiled and excluded entries stay baseline','selected':selected,'rejected':rejected},indent=2)+'\n');print('CFG clean selected',len(selected),'rejected',len(rejected))
