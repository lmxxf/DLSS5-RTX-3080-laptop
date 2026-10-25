from pathlib import Path
import json,hashlib,numpy as np
from diag15b_paths import ROOT
p=Path(__file__).resolve().parent;r=p.parent
base=json.loads((p/'phase14-baseline-manifest.json').read_text());assert {f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'artifacts/selected/modules').glob('*.hsaco')}==base
for f,sha in [(r/'phase14/artifacts/gold/f32-720p-1280x768.rgb32','149906da306f42ca462eb2b29047787d8aad4bc9aa52461095fa2da374677ec5'),(r/'phase1/artifacts/outputs/f32-1600.rgb32','cf8b1d270dbceb26f46565e1bb9d66620b902fca8491d60cd47a9a3b1e38cf24'),(r/'phase1/artifacts/outputs/f32-1920.rgb32','8a59ebde0693059f0551c6f0062dd468fcb04d37dd42f1644ee19f846acd3198')]:assert hashlib.sha256(f.read_bytes()).hexdigest()==sha
runs=json.loads((p/'diag15b-runs.json').read_text());assert len(runs)==8 and all(x['returncode']==0 and x['frozen_output_match'] is not False for x in runs)
for case in json.loads((p/'diag15b-inputs.json').read_text()):
 for mode in ['native','f32']:
  path=ROOT/'traces'/case['case']/mode;assert hashlib.sha256((path/'working-input.bin').read_bytes()).hexdigest()==case['input_sha256']
post=json.loads((p/'diag15b-post-verification.json').read_text());assert len(post)==8 and all(x['original_vs_feature_replay_bitdiff']==0 and x['main_output_SHA_unchanged'] for x in post)
expand=json.loads((p/'diag15b-expand.json').read_text())
assert all(x['production_vs_canonical_byte_diff']==x['F32_production_vs_canonical_byte_diff']==x['CPU_full_token_rows']['CPU_RNE_K8_bitdiff']==0 for x in expand['cases'].values())
attention=json.loads((p/'diag15b-attention-cpu.json').read_text());assert sum(x['bytes'] for x in attention['rows'])==8126464 and all(x['CPU_with_rcp_byte_diff']==0 for x in attention['rows'])
head=json.loads((p/'diag15b-head.json').read_text());assert all(x['native_CPU_head_bitdiff']==x['f32_CPU_head_bitdiff']==0 for x in head['cases'].values())
branches=json.loads((p/'diag15b-branches.json').read_text());assert all(x['byte_identical'] and x['current_Prepare_QKV_SHA']!=x['actual_frozen_input_QKV_SHA'] for x in branches['cold_capture_provenance_check'])
summary={'frozen_input_and_main_output_verified':True,'production_default_changed':False,'gold_changed':False,'performance_experiment':False,'actual_input_attention_CPU_bytes':8126464,'actual_input_attention_CPU_byte_diff':0,'expand_CPU_K8_RNE_values':65536,'expand_CPU_K8_RNE_bitdiff':0,'CPU_RGB_head_bitdiff':0,'diagnostic_capture_order_bug_confirmed':True,'production_implementation_bug_proven':False,'entire_network_formal_CPU_proof':False,'classification':'Evidence supports known FP16 accumulation/quantization error propagation and input-pattern/geometry interaction; checked operators and output head reproduced. No specific production fix justified. Fused encoder internals not exhaustively CPU-proven.','quality45_pass':False,'realHDR_visual_acceptance':False}
(p/'diag15b-validation.json').write_text(json.dumps(summary,indent=2)+'\n');print('PASS Phase15B evidence: actual input/output SHA, CPU/operator checks; no default/gold change;45dB not passed')
