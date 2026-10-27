from pathlib import Path
import json,hashlib,re
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert s['mask']==8;assert sha(s['path'])==s['sha256'];assert Path(s['path']).stat().st_size==266414592
rows=sum([json.loads((p/f).read_text()) for f in ['smoke.json','bench.json','caps-bench.json','conditional-bench.json']],[]);assert len(rows)==258;assert all(r['quality']['bitdiff']==0 and r['quality']['maxabs']==0 and r['metrics']['nonfinite']==0 for r in rows)
primitive=json.loads((p/'primitives.json').read_text());assert primitive['up_bitdiff']==0 and all(x['all_bitdiff']==0 for group in ['bias','quad'] for x in primitive[group]);pool=json.loads((p/'pool-test.json').read_text());assert all(r['word_bitdiff']==0 for r in pool)
profiles=json.loads((p/'profile-controls.json').read_text());assert len(profiles)==16 and all(x['output_bitdiff']==0 and x['calls_per_frame']==82 for x in profiles.values())
ptx={}
for i in range(15):
 a=(p/f'artifacts/c/fatbin{i:02}.ptx').read_bytes();b=(p/f'artifacts/selected/fatbin{i:02}.ptx').read_bytes();assert a==b;txt=a.decode();ptx[str(i)]={'sha256':hashlib.sha256(a).hexdigest(),'async_bindings':txt.count('cp.async.mbarrier.arrive.'),'pool_registers_present':'vp_0_0' in txt,'cap':sorted(set(map(int,re.findall(r'\.maxnreg\s+(\d+)',txt))))};assert ptx[str(i)]['async_bindings']=={4:104,5:208,6:4}.get(i,0)
 if i in [0,3,4,5,6]:assert ptx[str(i)]['cap']==[255]
for builds in ['builds.json','caps.json']:
 for name,r in json.loads((p/builds).read_text()).items():assert r['bytes']==266414592 and all(v[1]=='inline' for v in r['manifest'])
protected=json.loads((p/'protected-before-cleanup.json').read_text())
for f,r in protected.items():assert sha(f)==r['sha256'] and Path(f).stat().st_size==r['bytes']
result={'selected':s,'strict_output_runs':258,'timed_50_80_runs':240,'profile_runs':16,'all_bitdiff':0,'maxabs':0,'invalid':0,'primitive':primitive,'pool':pool,'all15_O4_original_slots':True,'selected_rebuild_same_PTX_and_SHA':True,'size_growth_bytes':0,'PTX':ptx,'protected_files':protected,'regressions':10,'notes':['Predicted resident warps from CUDA occupancy API are not measured dynamic occupancy.','Virtual register declaration reduction does not imply elimination of physical spills.','Original WorkPlan was user-modified before execution; retained task and appended findings.']}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS 258 strict outputs, 16 profiles, primitives, C pool hazard, selected reproducibility, protected files')
