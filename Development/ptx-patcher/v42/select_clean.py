from pathlib import Path
import json,copy
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());sp=json.loads((p/'specs.json').read_text());base=sp['baseline'];out={}
for mode,fbs,key,newname in [('pack4_fb1_all',[1],'pack4_entries','pack4_fb1_clean'),('pack4_quad_fb23',[2,3],'quad_entries','pack4_quad_clean')]:
 selected=[];rejected={}
 for n,q in r[mode].items():
  if q['FB'] not in fbs:continue
  bad=[k for k in ['STACK','STL','LDL'] if q[k]>r['baseline'][n][k]]
  if bad:rejected[n]=bad
  else:selected.append(n)
 s=copy.deepcopy(base);s.update(fbs=fbs,branches=[5],approximate=mode.startswith('pack4_fb1'),**{key:selected});sp[newname]=s;out[newname]={'selected':selected,'rejected':rejected,'rule':'before timing: actual STACK/STL/LDL nonincrease; REG not an exclusion; API occupancy recorded separately'}
for q in ['pack4_quad_fb23','pack4_quad_clean']:
 name='joint_A_B_'+q;s=copy.deepcopy(sp[q]);s.update(fbs=[0,1,2,3],pack4_entries=sp['pack4_fb0_nopre']['pack4_entries']+sp['pack4_fb1_clean']['pack4_entries'],branches=[5],approximate=True,components=['pack4_fb0_nopre','pack4_fb1_clean',q]);sp[name]=s
(p/'specs.json').write_text(json.dumps(sp,indent=2)+'\n');(p/'clean-selection.json').write_text(json.dumps(out,indent=2)+'\n');print({n:(len(v['selected']),v['rejected']) for n,v in out.items()})
