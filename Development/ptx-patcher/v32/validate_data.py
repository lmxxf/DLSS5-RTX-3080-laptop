"""Independently check raw logs / hashes / resources before writing narrative."""
from pathlib import Path
import json,hashlib,re,statistics as st
p=Path(__file__).resolve().parent
resources=json.loads((p/'resources.json').read_text());candidates=json.loads((p/'candidates.json').read_text());source=json.loads((p/'source-pools.json').read_text());baseline='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
assert candidates['baseline']['sha256']==baseline
for tag,r in candidates.items():
 f=Path(r['path']);assert f.stat().st_size==266414592 and hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];assert len(r['manifest'])==15 and all(x[1]=='inline' for x in r['manifest'])
assert len(resources)==len(candidates)
for mode,rows in resources.items():
 assert len(rows)==38 and set(rows)==set(resources['baseline']);assert sum(r['HMMA'] for r in rows.values())==13188
for key,total in [('INSN_NONOP',152076),('INSN_WITH_NOP',152807),('HMMA',13188),('PRMT',19861),('STL',107),('LDL',108)]:assert sum(r[key] for r in resources['baseline'].values())==total
allrows=[];counts={}
for file in ['smoke','bench','repair','clean','caps','arithmetic','repeat','probe-bench']:
 f=p/(file+'.json')
 if not f.exists():continue
 rows=json.loads(f.read_text());counts[file]=len(rows)
 for r in rows:
  log=(p/(r['name']+'-'+r['variant']+'-'+str(r['width'])+'.log')).read_text();metrics={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',log.split('SUMMARY')[-1])}
  assert metrics==r['metrics'] and metrics['nonfinite']==0
  assert r['quality']['maxabs']>=0
  if file!='probe-bench':assert r['quality']['bitdiff']==0 and r['quality']['maxabs']==0
  if file not in ['smoke']:assert r['warmup']==50 and r['iterations']==80
 allrows+=rows
first=json.loads((p/'first.json').read_text());clean=json.loads((p/'clean.json').read_text());repair=json.loads((p/'repair.json').read_text());assert first==clean+repair
excluded=json.loads((p/'excluded-timing.json').read_text());assert len(excluded)==72 and {r['name'] for r in excluded}=={r['name'] for r in json.loads((p/'bench.json').read_text())}
for r in allrows:
 if r['variant'].startswith('probe_'):continue
 gold=Path('/mnt/c/DLSS5-5090-dll/ptx-v32-bench')/f'gold-{r["warmup"]}-{r["iterations"]}-{r["width"]}.rgb32'
 assert gold.stat().st_size==r['width']*r['height']*3*4
 assert hashlib.sha256(gold.read_bytes()).hexdigest()==r['quality']['sha256']
assert counts['bench']==72 and counts['repair']==12 and counts['caps']==144
assert counts['probe-bench']==48 and counts['arithmetic']==48 and counts['clean']==60
for file in ['decode-tests.json','shift-tests.json']:
 for r in json.loads((p/file).read_text()):assert r['bitdiff']==0
aliases=json.loads((p/'alias-tests.json').read_text());assert len(aliases)==7 and all(r['word_bitdiff_against_independent_upfront_lowhigh']==0 for r in aliases)
protected=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in protected};assert after==protected
(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
timing=json.loads((p/'timing-summary.json').read_text());eligible=json.loads((p/'repeat-eligible.json').read_text());winners=[]
for v in eligible:
 repeat=timing.get('repeat',{}).get(v,{})
 if len(repeat)==3 and all(r['directions'][direction]['gain_percent']>0 for r in repeat.values() for direction in ['forward','reverse']):winners.append(v)
probe_rows=json.loads((p/'probe-bench.json').read_text());probe={}
for w in [1280,1600,1920]:
 vals={v:[r['metrics']['gpu_median_ms'] for r in probe_rows if r['width']==w and r['variant']==v] for v in ['baseline','probe_p0','probe_p1','probe_p2']};assert all(len(a)==4 for a in vals.values());means={v:st.mean(a) for v,a in vals.items()};base,a,b,both=[means[v] for v in vals];probe[w]={'raw_process_medians':vals,'means_ms':means,'base_minus_p0_ms':base-a,'base_minus_p1_ms':base-b,'interaction_355_ms':base-a-b+both,'P0_pass_signs':[x-y for x,y in zip(vals['baseline'],vals['probe_p0'])],'P1_pass_signs':[x-y for x,y in zip(vals['baseline'],vals['probe_p1'])]}
(p/'probe-summary.json').write_text(json.dumps(probe,indent=2)+'\n')
result={'data_checks_pass':True,'counts':counts,'strict_successful_runs':sum(v for k,v in counts.items() if k!='probe-bench'),'probe_diagnostic_runs':counts['probe-bench'],'excluded_timing_runs':72,'repeat_eligible':eligible,'winners':winners,'protected_paths':len(protected),'all_protected_unchanged':True,'exact_baseline_sha256':baseline,'branch3_n_after':0 if winners else 2,'branch3_state':'Open','branch4_state':'Open','branch2_pack_probe_reassessment_needed':all(x>0 for r in probe.values() for x in r['P0_pass_signs']),'review_order':'raw logs, hashes, resources and probes independently checked before narrative','scope':'finite/bitwise checks apply to tested final frames and primitive fixtures; occupancy is theoretical; destructive probes cannot promote'}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
