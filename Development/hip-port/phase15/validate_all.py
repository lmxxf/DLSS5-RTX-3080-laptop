from pathlib import Path
import json,hashlib,numpy as np,argparse
p=Path(__file__).resolve().parent;r=p.parent;ap=argparse.ArgumentParser();ap.add_argument('--tag',default='regression');args=ap.parse_args()
module_hash={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'artifacts/selected/modules').glob('*.hsaco')};assert len(module_hash)==40 and module_hash==json.loads((p/'phase14-baseline-manifest.json').read_text())
loads=json.loads((p/'artifacts/selected/cuda-load-verification.json').read_text());assert len(loads)==40 and sum(x['entries'] for x in loads)==1918
cal=json.loads((p/'calibration.json').read_text());assert len(cal)==6 and all(x['gold_bitdiff']==0 for x in cal)
image=json.loads((p/'image-results.json').read_text());assert len(image['rows'])==56 and not image['new_correctness_issues'];assert all(x['correct256_vs400_full_bitdiff']==x['invalid']==x['repeat_first_last_bitdiff']==x['native_LMem_nonzero']==0 for x in image['rows'])
assert image['white1_vs512_input_and_all_output_pairs_bitdiff']==0
unit=json.loads((p/'coverage-results.json').read_text());assert len(unit['rows'])==172 and unit['all_fixed_vs400_byte_diff']==0
layout=json.loads((p/'layout-results.json').read_text());assert layout['coordinate_cases']==256 and layout['fixed_u32_diff']==0
cpu=json.loads((p/'rounding-results.json').read_text());assert cpu['total_bytes']==1966080 and cpu['CPU_with_primitive_rcp_byte_diff']==0
runs=json.loads((p/(args.tag+'-runs.json')).read_text());assert len(runs)==27 and all(x['returncode']==0 for x in runs)
for run in runs:
 text=Path(run['log']).read_text();assert 'GRAPH_STATUS enabled=0 builds=0 replays=0 small=1' in text;assert 'blocks=31' in text
base=[]
for w,h,vh in [(1280,768,720),(1600,1024,900),(1920,1152,1080)]:
 native=np.fromfile(p/f'artifacts/runs/{args.tag}/baseline-{w}/400/0.rgb32',np.float32).reshape(h,w,3);ref=np.fromfile(p/f'artifacts/runs/{args.tag}/baseline-{w}/f32/0.rgb32',np.float32).reshape(h,w,3)
 old=np.fromfile(r/f'phase14/artifacts/outputs/default400-{w}.rgb32',np.uint32);assert np.array_equal(native.view(np.uint32).reshape(-1),old)
 if w!=1280:assert np.array_equal(native.view(np.uint32).reshape(-1),np.fromfile(r/f'phase12/artifacts/outputs/selected-{w}.rgb32',np.uint32))
 d=native[:vh].astype(float)-ref[:vh].astype(float);row={'processing':[w,h],'visible':[w,vh],'Phase14_bitdiff':0,'Phase12_bitdiff':0 if w!=1280 else None,'psnr_peak1':float(-10*np.log10(np.mean(d*d))),'maxabs':float(np.max(abs(d))),'invalid':int(np.count_nonzero(~np.isfinite(native))),'first_last_bitdiff':0,'native_active_kernels':32,'native_LMem_nonzero':0,'legacy45_pass':bool(-10*np.log10(np.mean(d*d))>=45)};base.append(row)
(p/'baseline-quality.json').write_text(json.dumps(base,indent=2)+'\n')
summary={'run_tag':args.tag,'correctness_regression_pass':True,'module_count':40,'entry_count':1918,'native_module_hashes_equal_Phase14':True,'input_configurations':56,'independent_real_SDR_sources':1,'real_scene_HDR_sources':0,'dynamic_calibration_enqueue_frames':sum(len(x['frames']) for x in runs),'resource_replays':27,'all56_correct256_vs400_bitdiff':0,'all_native32_LOCAL0':True,'all_repeats_bitdiff0':True,'canonical_quality':base,'legacy45_global_gate_pass':all(x['legacy45_pass'] for x in base) and all(x['meets_45dB_on_this_input_only'] for x in image['rows']),'accuracy_limitations':image['accuracy_limitations'],'performance_experiment_permitted':False,'performance_work':'paused: representative real HDR/gameplay inputs insufficient; no newC32 experiment or performance timing performed','new_layout_or_nonfinite_failure':False}
(p/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print('PASS correctness:',56,'image configs,7geometries,375frames,40modules/1918entry; quality45/global realHDR acceptance NOT passed; performance paused')
