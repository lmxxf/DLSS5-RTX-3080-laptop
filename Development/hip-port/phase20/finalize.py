from pathlib import Path
import json,hashlib,csv,re,datetime,numpy as np
p=Path(__file__).resolve().parent;r=p.parent;rows=json.loads((p/'results.json').read_text());s=json.loads((p/'summary.json').read_text());assert len(s)==3 and len(rows)==15
assert all(x['invalid']==x['first_last']==0 and x['LMem0'] for x in rows.values());assert not any(x['quality_gate'] for x in s.values())
mods=p/'artifacts/candidate/modules';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();m={f.name:sha(f) for f in mods.glob('*.hsaco')};(p/'candidate-modules.sha256.json').write_text(json.dumps(m,indent=2)+'\n')
for w in [1280,1600,1920]:
 a=rows[f'candidate-b-{w}'];b=rows[f'candidate-b2-{w}'];assert a['output_sha256']==b['output_sha256']
 for part in ['candidate-b','candidate-b2']:assert json.loads((p/f'{part}-{w}-run.json').read_text())['module_hashes']==m
tele=[]
for row in list(csv.reader((p/'telemetry.csv').open()))[1:]:
 try:tele.append((datetime.datetime.strptime(row[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',v)[0]) for v in row[2:]]))
 except (ValueError,TypeError):pass
tr={}
for f in p.glob('*-run.json'):
 q=json.loads(f.read_text());a,z=map(datetime.datetime.fromisoformat,[q['begin'],q['end']]);ss=[x for x in tele if a<=x[0]<=z and x[-1]>=90];tr[f.stem]={'util90_samples':len(ss),**{k:float(np.median([x[i] for x in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry-summary.json').write_text(json.dumps(tr,indent=2)+'\n')
root=Path('/mnt/c/DLSS5-5090-dll');protected={}
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v21.dll']:protected[str(f)]=sha(f);assert protected[str(f)]=='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed'
for x in json.loads((r.parent/'ptx-patcher/release-rtx30/v020/packages.json').read_text()):protected[x['path']]=sha(Path(x['path']));assert protected[x['path']]==x['sha256']
(p/'protected.json').write_text(json.dumps(protected,indent=2,ensure_ascii=False)+'\n');(p/'validation.json').write_text(json.dumps({'baseline':'Phase19 selected','joint_candidates':1,'formal_ABBA_runs':12,'quick_runs':3,'all_invalid':0,'all_first_last':0,'active_LMem0':32,'candidate_repeat_SHA_equal':True,'finite_half_inputs':63488,'finite_changed_input_count':182,'max_finite_FP8_code_distance':1,'max_finite_output_value_difference':32,'default_promoted':False,'default_retained':'Phase19','reason':'all relative PSNR below50dB;720p/900p F32gold PSNR declines;only0.9..1.1percent speed','PHASE20_HALF_ACT':False,'external_v020_unchanged':True,'deployment':False,'push':False},indent=2)+'\n');print('PASS diagnostic validation;quality gate failed;Phase19 remains default')
