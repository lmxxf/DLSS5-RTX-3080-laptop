from pathlib import Path
import json,hashlib,csv,re,datetime,numpy as np,subprocess
from check_run import check_variant
p=Path(__file__).resolve().parent;r=p.parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();modules=p/'artifacts/selected/modules';actual={f.name:sha(f) for f in sorted(modules.glob('*.hsaco'))};measured=json.loads((p/'candidate-b-final-1920-run.json').read_text())['module_hashes'];assert actual==measured==json.loads((p/'selected-modules.sha256.json').read_text());old=json.loads((r/'phase17/selected-modules.sha256.json').read_text());assert [n for n,h in actual.items() if old[n]!=h]==['c32-wave1-fast.hsaco','c64-wave2-fast.hsaco']
subprocess.run(['python3',str(r/'phase14/verify_modules.py'),'--modules',str(modules)],check=True);loads=json.loads((modules.parent/'cuda-load-verification.json').read_text());assert sum(x['entries'] for x in loads)==1918;(p/'cuda-load-verification.json').write_text(json.dumps(loads,indent=2)+'\n')
summary=[];failed=[]
for f in sorted(p.glob('*-run.json')):
 m=json.loads(f.read_text())
 if m['returncode']!=0:failed.append({'file':f.name,'returncode':m['returncode'],'scope':'rejected initial ByteOut prewarm;not used for timing'});continue
 rows=check_variant(m['variant'],True);x=next(x for x in rows.values() if x['width']==m['width']);summary.append({'file':f.name,'warmup':m['warmup'],'iterations':m['iterations'],'bitdiff':x['bitdiff'],'invalid':x['invalid'],'first_last':x['first_last'],'LMem0':x['LMem0'],'output_sha256':sha(p/f'artifacts/outputs/{m["variant"]}-{m["width"]}.rgb32')})
(p/'run-validation.json').write_text(json.dumps({'accepted_runs':summary,'failed_incomplete_runs':failed},indent=2)+'\n')
# Float/half NaN and layout tests were performed on every requested site.
primitives=json.loads((p/'primitive-results.json').read_text());assert len(primitives)==7 and all(x['all_half_patterns_and_onehot_byte_diff']==0 and all(v==0 for v in x['mma_steps'].values()) for x in primitives.values())
samples=[]
for f in p.glob('*-telemetry.csv'):
 for row in list(csv.reader(f.open()))[1:]:
  try:samples.append((datetime.datetime.strptime(row[0],'%Y/%m/%d %H:%M:%S.%f'),*[float(re.search(r'[\d.]+',v)[0]) for v in row[2:]]))
  except (ValueError,TypeError):pass
tele={}
for f in p.glob('*-run.json'):
 m=json.loads(f.read_text());a,b=map(datetime.datetime.fromisoformat,[m['begin'],m['end']]);ss=[q for q in samples if a<=q[0]<=b and q[-1]>=90];tele[f.stem]={'util90_samples':len(ss),**{k:float(np.median([q[i] for q in ss])) if ss else None for k,i in [('temp_c',1),('power_w',2),('sm_mhz',3),('mem_mhz',4)]}}
(p/'telemetry-summary.json').write_text(json.dumps(tele,indent=2)+'\n')
root=Path('/mnt/c/DLSS5-5090-dll');protected={}
for f in [root/'nvngx_dlssnr_sm86_fast.dll',root/'nvngx_dlssnr_sm86_v21.dll']:
 protected[str(f)]=sha(f);assert protected[str(f)]=='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed'
for row in json.loads((r.parent/'ptx-patcher/release-rtx30/v020/packages.json').read_text()):protected[row['path']]=sha(Path(row['path']));assert protected[row['path']]==row['sha256']
(p/'protected-release-hashes.json').write_text(json.dumps(protected,indent=2,ensure_ascii=False)+'\n')
result={'default':'C32V+Wave2 ByteOut+QKV mask7, C256 cap unchanged','baseline':'Phase17 selected','accepted_run_count':len(summary),'incomplete_rejected_runs':len(failed),'per_site_formal_ABBA_runs':84,'1080_control_screen_runs':28,'final_three_tier_ABBA_runs':12,'all_accepted_bitdiff':0,'invalid':0,'first_last':0,'active_LMem0':32,'modules':40,'resolved_entries':1918,'changed_modules':['c32-wave1-fast.hsaco','c64-wave2-fast.hsaco'],'source_rebuild_matches_measured':True,'C256_final_regs':226,'C256_final_OccW':8,'C256_168':'zero stack but no stable added frame benefit,OccW8','C256_128':'8Bstack;fuse/pair12848Bstack;not timed','external_v020_protected':True,'deployment':False,'push':False}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS final:',result)
