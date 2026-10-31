from pathlib import Path
import json,copy
p=Path(__file__).resolve().parent;r=json.loads((p/'resources.json').read_text());sp=json.loads((p/'specs.json').read_text());sel=[];reject={}
for n,q in r['fb123_quad_diagnostic'].items():
 if q['FB']!=1:continue
 bad=[k for k in ['STACK','STL','LDL'] if q[k]>r['baseline'][n][k]]
 if q['resident_CTA_per_SM']<r['baseline'][n]['resident_CTA_per_SM']:bad.append('resident_CTA_per_SM')
 if bad:reject[n]=bad
 else:sel.append(n)
s=copy.deepcopy(sp['baseline']);s.update(fbs=[1,2,3],pack4_entries=sel,quad_entries=sel+sp['fb1_pack4_fb23_quad']['quad_entries'],approximate=True,branches=[5]);sp['fb123_pack4_quad_clean']=s;(p/'specs.json').write_text(json.dumps(sp,indent=2)+'\n');(p/'clean-selection.json').write_text(json.dumps({'FB01_selected':sel,'FB01_rejected':reject,'rule':'before timing: STACK/STL/LDL no increase relative V4.0, API CTA/SM no decrease; no REG exclusion','FB23_entries':sp['fb1_pack4_fb23_quad']['quad_entries']},indent=2)+'\n');print('FB01 selected',sel,'rejected',reject)
