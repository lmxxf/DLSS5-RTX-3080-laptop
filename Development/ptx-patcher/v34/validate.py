from pathlib import Path
import json,re,hashlib,datetime,statistics as st
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());counts={};allrows=[];gold={}
for mode,r in cs.items():
 f=Path(r['path']);assert len(r['manifest'])==15 and all(a[1]=='inline' for a in r['manifest']);assert f.stat().st_size==266414592 and hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];assert len(res[mode])==38
assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
for dataset in ['smoke','bench','repeat']:
 f=p/(dataset+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());counts[dataset]=len(rows)
 for r in rows:
  text=(p/f'{r["name"]}-{r["variant"]}-{r["width"]}.log').read_text();metrics={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',text.split('SUMMARY')[-1])};assert metrics==r['metrics'];assert r['dll_sha256']==cs[r['variant']]['sha256'];assert r['metrics']['nonfinite']==r['quality']['bitdiff']==r['quality']['maxabs']==r['quality']['nonfinite_output_values']==0
  key=(r['warmup'],r['iterations'],r['width'])
  if key not in gold:gold[key]=hashlib.sha256((Path('/mnt/c/DLSS5-5090-dll/ptx-v34-bench')/f'gold-{key[0]}-{key[1]}-{key[2]}.rgb32').read_bytes()).hexdigest()
  assert gold[key]==r['quality']['sha256']
  if dataset!='smoke':assert key[:2]==(50,80)
 allrows+=rows
assert counts['smoke']==18 and counts['bench']==120
ordered=sorted(allrows,key=lambda r:r['begin']);assert all(a['end']<=b['begin'] for a,b in zip(ordered,ordered[1:]));stages=json.loads((p/'serial-stages.json').read_text());assert all(r['returncode']==0 for r in stages);assert all(a['end']<=b['begin'] for a,b in zip(stages,stages[1:]));first=datetime.datetime.fromisoformat(ordered[0]['begin']).timestamp();last=max(f.stat().st_mtime for f in (p/'artifacts').rglob('*') if f.suffix in ('.cubin','.ptx'));assert last<first
assert all(r['bitdiff']==0 for r in json.loads((p/'local-gpu-tests.json').read_text()));assert all(r['word_bitdiff']==0 for r in json.loads((p/'shared-forward-gpu-tests.json').read_text()));q=json.loads((p/'quantization-counterexample.json').read_text());assert q['original_half_value']==1.0625 and q['expanded_half_value']==1.0
md=json.loads((p/'multidef36-audit.json').read_text());assert md['event_count']==36 and md['unique_pack_events']==0 and all(r['reaching_definition_count']==2 for r in md['records'])
layout=json.loads((p/'shared-layout-audit.json').read_text());assert layout['shared_event_count']==2320 and layout['capacity_exhaustion_claim_supported']==False
cap=json.loads((p/'shared-capacity-api.json').read_text());assert cap['all_doubled_payload_fit_current_residency'];assert cap['device']=={'shared_per_sm':102400,'shared_per_block_default':49152,'shared_per_block_optin':101376,'driver_reserved_shared_per_block':1024}
plan=json.loads((p/'shared-forward-plan.json').read_text());assert plan['accepted_load_vectors']==36
for mode in ['shared_forward','quad_fb1_shared']:
 text='\n'.join((p/f'artifacts/{mode}/fatbin{fb:02}.ptx').read_text() for fb in range(7));assert text.count('@v34_shape_ok mov.b32')==144 and text.count('@!v34_shape_ok ld.shared')==36
identity=json.loads((p/'machine-identity.json').read_text());assert all(identity['quad_fb1']['cubin_equal_to_baseline'][i] for i in range(15) if i!=1)
timing=json.loads((p/'timing-summary.json').read_text());eligible=json.loads((p/'repeat-eligible.json').read_text());winners=[]
for mode in eligible:
 rr=timing.get('repeat',{}).get(mode,{});assert len(rr)==3
 if all(r['directions'][d]['gain_percent']>0 for r in rr.values() for d in ['forward','reverse']):winners.append(mode)
old=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in old};assert after==old;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
# The requested all-closed precondition is not proved: payload doubling fits
# current residency, and the coupled FP16 representation rewrite remains untested.
branch2win=any(m.startswith('quad') for m in winners);branch4win=any('shared' in m for m in winners)
v={'data_checks_pass':True,'counts':counts,'strict_successful_runs':len(allrows),'all_timing_processes_serial':True,'all_build_and_GPU_query_work_before_timing':True,'first_measurement_begin':ordered[0]['begin'],'last_compiled_artifact_mtime':datetime.datetime.fromtimestamp(last).isoformat(),'repeat_eligible':eligible,'winners':winners,'branch1':{'state':'Pruned','n':3},'branch2':{'state':'Open' if branch2win else 'Pruned','n':0 if branch2win else 3},'branch3':{'state':'Pruned','n':3},'branch4':{'state':'Open','n':0 if branch4win else 2,'reason':'V3.4 whole-batch no-promotion count advances once; ultimate closure condition not met: payload doubling does not reduce current API residency; coupled representation paths are not excluded'},'ultimate_all_closed_condition_met':False,'remaining_open_branches':[i for i,state in [(2,branch2win),(4,True)] if state],'protected_paths':len(after),'protected_unchanged':True,'baseline_sha256':cs['baseline']['sha256'],'review_order':'raw process logs, output SHA, CFG/liveness, source mapping and official capacity queries before narrative'};(p/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
