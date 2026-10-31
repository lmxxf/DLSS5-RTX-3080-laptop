"""Independent raw-data audit; executed before narrative and promotion."""
from pathlib import Path
import json,re,hashlib,datetime,statistics as st
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());counts={};allrows=[];gold_hash={}
for mode,c in cs.items():
 f=Path(c['path']);assert f.stat().st_size==266414592;assert hashlib.sha256(f.read_bytes()).hexdigest()==c['sha256'];assert len(c['manifest'])==15 and all(r[1]=='inline' for r in c['manifest']);assert len(res[mode])==38
 if not mode.startswith('probe_'):assert sum(r['HMMA'] for r in res[mode].values())==13188
assert cs['baseline']['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
strict=0
for file in ['smoke','probes','bench','repeat']:
 f=p/(file+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());counts[file]=len(rows)
 for r in rows:
  path=p/f'{r["name"]}-{r["variant"]}-{r["width"]}.log';text=path.read_text();metrics={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',text.split('SUMMARY')[-1])};assert metrics==r['metrics'];assert r['dll_sha256']==cs[r['variant']]['sha256']
  if not r['variant'].startswith('probe_'):
   strict+=1;assert r['quality']['bitdiff']==r['quality']['maxabs']==r['quality']['nonfinite_output_values']==r['metrics']['nonfinite']==0
   key=(r['warmup'],r['iterations'],r['width'])
   if key not in gold_hash:
    f=root/'ptx-v33-bench'/f'gold-{key[0]}-{key[1]}-{key[2]}.rgb32';assert f.stat().st_size==r['width']*r['height']*12;gold_hash[key]=hashlib.sha256(f.read_bytes()).hexdigest()
   assert r['quality']['sha256']==gold_hash[key]
  if file!='smoke':assert r['warmup']==50 and r['iterations']==80
 allrows.extend(rows)
functional=[n for n in cs if n!='baseline' and not n.startswith('probe_')];assert len(functional)==10
assert counts['smoke']==33 and counts['probes']==84 and counts['bench']==240
ordered=sorted(allrows,key=lambda r:r['begin'])
assert all(a['end']<=b['begin'] for a,b in zip(ordered,ordered[1:]))
stages=json.loads((p/'serial-stages.json').read_text());assert all(r['returncode']==0 for r in stages);assert all(a['end']<=b['begin'] for a,b in zip(stages,stages[1:]))
first_measure=datetime.datetime.fromisoformat(ordered[0]['begin']).timestamp();last_compile=max(f.stat().st_mtime for f in (p/'artifacts').rglob('*') if f.suffix in ('.cubin','.ptx'));assert last_compile<first_measure
for mode in ['phase_pass','remat','remat_call']:
 rows=json.loads((p/f'alias-{mode}.json').read_text());assert len(rows)==7 and all(r['word_bitdiff_against_independent_upfront_lowhigh']==0 for r in rows)
assert all(r['word_bitdiff']==0 for r in json.loads((p/'layer-tests.json').read_text()))
assert all(r['mismatch_pairs']==0 and r['pairs']==16777216 for r in json.loads((p/'primitives.json').read_text())['pack5_quad'])
src=json.loads((p/'source-summary.json').read_text());assert sum(r['decoded_half_events'] for r in src['phase_pass'].values())==11696
assert all(r['decoded_half_events']==r['original_decoded_half_events'] for r in src['phase_pass'].values())
for r in src['phase_pass'].values():assert r['raw_snapshot_b32_peak']==0
forward=json.loads((p/'forwarding-audit.json').read_text());assert len(forward['mixed_records'])==144 and not forward['pure_local_pack_alias_candidates']
identity=json.loads((p/'machine-identity.json').read_text());assert all(identity['quad_fb23']['whole_cubin_equal_to_baseline'][i] for i in range(15) if i not in (2,3))
timing=json.loads((p/'timing-summary.json').read_text());eligible=json.loads((p/'repeat-eligible.json').read_text());winners=[]
for mode in eligible:
 rr=timing.get('repeat',{}).get(mode,{});assert len(rr)==3
 if all(r['directions'][d]['gain_percent']>0 for r in rr.values() for d in ['forward','reverse']) and not identity[mode]['active_text_identical']:winners.append(mode)
probes={};rows=json.loads((p/'probes.json').read_text())
for w in [1280,1600,1920]:
 vals={m:[r['metrics']['gpu_median_ms'] for r in rows if r['width']==w and r['variant']==m] for m in ['baseline','probe_shared','probe_global_family','probe_global','probe_mixed','probe_both','probe_all']};assert all(len(a)==4 for a in vals.values());means={m:st.mean(a) for m,a in vals.items()};base=means['baseline'];probes[w]={'raw_process_medians':vals,'means_ms':means,'base_minus_ms':{m:base-means[m] for m in vals if m!='baseline'},'shared_global_family_interaction_ms':base-means['probe_shared']-means['probe_global_family']+means['probe_all'],'shared_pure_global_interaction_ms':base-means['probe_shared']-means['probe_global']+means['probe_both'],'nonfinite_probe_runs':sum(r['quality']['nonfinite_output_values']>0 for r in rows if r['width']==w),'scope':'destructive sensitivity; categories contain may-origins, not dynamic counts; not additive recoverable budgets'}
(p/'probe-summary.json').write_text(json.dumps(probes,indent=2)+'\n')
protected=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in protected};assert after==protected;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
branch_wins={2:any('quad' in m for m in winners),3:any(m.startswith(('phase','remat')) for m in winners)}
result={'data_checks_pass':True,'counts':counts,'functional_candidates':functional,'strict_successful_runs':strict,'destructive_probe_runs':sum(r['variant'].startswith('probe_') for r in rows),'all_run_processes_serial':True,'all_compile_and_resource_stages_before_timing':True,'serial_stage_count':len(stages),'last_compile_file_time':datetime.datetime.fromtimestamp(last_compile).isoformat(),'first_measurement_begin':ordered[0]['begin'],'repeat_eligible':eligible,'winners':winners,'branch2':{'state':'Open','n':0 if branch_wins[2] else 2},'branch3':{'state':'Open' if branch_wins[3] else 'Pruned','n':0 if branch_wins[3] else 3},'branch4':{'state':'Open','n':1,'safe_forwarding_candidates':0},'protected_paths':len(protected),'protected_unchanged':True,'reference_sha256':cs['baseline']['sha256'],'no_dynamic_stall_or_issued_counters':True,'review_order':'raw logs, exact output SHA, SASS/resources, official occupancy, source counts, serial timing and branches before narrative'}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
