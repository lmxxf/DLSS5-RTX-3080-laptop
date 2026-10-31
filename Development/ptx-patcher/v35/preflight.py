from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;plans=json.loads((p/'plans.json').read_text());primitives=json.loads((p/'primitive-tests.json').read_text());smoke=json.loads((p/'smoke.json').read_text());cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());records=json.loads((p/'build-records.json').read_text())
assert len(smoke)==24 and len(cs)==8 and all(r['mismatches']==0 for r in primitives)
for r in smoke:
 assert r['quality']['nonfinite']==0
 if not cs[r['variant']]['approximate']:assert r['quality']['bitdiff']==0 and r['quality']['maxabs']==0
for n,k in plans.items():
 if k['FB']==1:assert k['inplace_finite_proved'] and k['fast_word_coverage']==k['store_word_count']
for mode,c in cs.items():
 assert len(c['manifest'])==15 and all(x[1]=='inline' for x in c['manifest']);assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256']
 if mode!='baseline':
  for i in set(range(15))-set(c['target_fbs']):assert (p/f'artifacts/{mode}/fatbin{i:02}.cubin').read_bytes()==(p/f'artifacts/baseline/fatbin{i:02}.cubin').read_bytes()
assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
scope={}
for mode,rr in records.items():
 count=sum(r['shared_native_events'] for mod in rr for r in mod['runs']);scope[mode]={'shared_native_static_run_events':count,'Shared_bytes_per_active_kernel':{n:r['SHARED'] for n,r in res[mode].items() if r['FB'] in cs[mode].get('target_fbs',[])}}
(p/'preflight.json').write_text(json.dumps({'passed':True,'baseline_sha256':cs['baseline']['sha256'],'smoke_runs':24,'exact_smoke_bitdiff':0,'fast_smoke_quality_pass':all(r['quality']['quality_pass'] for r in smoke),'native_event_counts':scope,'all_other_modules_byte_identical':True,'finite_inplace_producer_domain_proved':True,'precision_scope':'finite FP8 producer bytes; actual Pack5 emits no reserved 7f/ff; original byte view preserved or reconstructed exactly; fast modes explicit approximation'},indent=2)+'\n');print('preflight PASS')
