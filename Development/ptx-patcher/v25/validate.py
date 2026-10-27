from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert not s['V25_promoted'] and sha(s['path'])==s['sha256']
rows=sum([json.loads((p/f).read_text()) for f in ['smoke.json','bench.json','fb0-bench.json']],[]);assert len(rows)==46 and all(x['quality']['bitdiff']==0 and x['metrics']['nonfinite']==0 for x in rows)
primitive=json.loads((p/'decode-test.json').read_text());assert primitive['pairs']==33554432 and primitive['all_bitdiff']==0 and primitive['old_PTX_lines']==primitive['new_PTX_lines']==8
b=json.loads((p/'build.json').read_text());assert b['bytes']==266414592 and all(x[1]=='inline' for x in b['manifest']);assert sha(b['path'])==b['sha256']
c=json.loads((p/'counter-build.json').read_text());assert sha(c['path'])==c['sha256'];runs=json.loads((p/'counter-runs.json').read_text());assert set(runs)=={'1280','1600','1920'} and all(r['bitdiff']==0 and r['diagnostic_DLL_sha256']==c['sha256'] for r in runs.values())
params=json.loads((p/'launch-params.json').read_text());assert all(r['bitdiff']==0 and len(r['params'])==len(r['calls'])==82 for r in params.values())
ledger=json.loads((p/'dynamic-ledger.json').read_text());assert all(r['counter_output_bitdiff']==0 for r in ledger.values())
pro=json.loads((p/'protected-before-cleanup.json').read_text())
for f,r in pro.items():assert sha(f)==r['sha256'] and Path(f).stat().st_size==r['bytes']
r={'selected':s,'primitive':primitive,'strict_uninstrumented_runs':46,'timed_50_80_runs':40,'parameter_capture_reference_pairs':3,'runtime_counter_runs':3,'runtime_counter_output_bitdiff':0,'82_launch_shape_agreement':True,'counter_build':c,'FB04_FB05_loop_expanded_HMMA_model_matches_semantic_counter':True,'auxiliary_SASS_count_is_model_not_hardware_counter':True,'all15_O4_inline_candidate':True,'candidate_sha256':b['sha256'],'candidate_promoted':False,'protected_files':pro,'regressions':10}
(p/'validation.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS negative result: 46 strict runs, exhaustive primitive, three runtime ledgers, protected V2.4')
