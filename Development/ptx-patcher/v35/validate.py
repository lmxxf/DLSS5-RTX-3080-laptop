from pathlib import Path
import json,re,hashlib,datetime
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());rows=[];counts={};gold={}
for mode,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[mode])==38
for file in ['smoke','timed','repeat']:
 f=p/(('bench' if file=='timed' else file)+'.json')
 if not f.exists():continue
 rr=json.loads(f.read_text());counts[file]=len(rr)
 for r in rr:
  metrics={k:float(x) for k,x in re.findall(r'(\w+)=([-+\d.eE]+)',r['process_output'].split('SUMMARY')[-1])};assert metrics==r['metrics'] and r['returncode']==0 and r['quality']['nonfinite']==0;assert r['dll_sha256']==cs[r['variant']]['sha256']
  if not cs[r['variant']]['approximate']:
   assert r['quality']['bitdiff']==r['quality']['maxabs']==0;key=(r['warmup'],r['iterations'],r['width'])
   if key not in gold:gold[key]=hashlib.sha256((Path('/mnt/c/DLSS5-5090-dll/ptx-v35-bench')/f'gold-{key[0]}-{key[1]}-{key[2]}.rgb32').read_bytes()).hexdigest()
   assert r['quality']['sha256']==gold[key]
  if file!='smoke':assert (r['warmup'],r['iterations'])==(50,80)
 rows+=rr
assert counts['smoke']==24 and counts['timed']==168
ordered=sorted(rows,key=lambda r:r['begin']);assert all(a['end']<=b['begin'] for a,b in zip(ordered,ordered[1:]));first=datetime.datetime.fromisoformat(ordered[0]['begin']).timestamp();last=max(f.stat().st_mtime for f in (p/'artifacts').rglob('*') if f.suffix in ('.cubin','.ptx'));assert last<first
summary=json.loads((p/'timing-summary.json').read_text());eligible=json.loads((p/'repeat-eligible.json').read_text());winners=[]
for n in eligible:
 a=summary['timed'][n];b=summary.get('repeat',{}).get(n,{});assert len(b)==3
 if all(r['quality_pass'] for r in list(a.values())+list(b.values())) and all(r['directions'][d]['gain_percent']>0 for r in b.values() for d in ['forward','reverse']):winners.append(n)
prot=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in prot};assert after==prot;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
result={'data_checks_pass':True,'counts':counts,'exact_successful_runs':sum(not cs[r['variant']]['approximate'] for r in rows),'approximate_runs':sum(cs[r['variant']]['approximate'] for r in rows),'all_timing_processes_serial':True,'builds_and_primitive_work_before_timing':True,'repeat_eligible':eligible,'winners':winners,'branch4':{'state':'Open' if winners else 'Pruned','n':0 if winners else 3},'remaining_open_branches':[4] if winners else [],'protected_paths':len(prot),'protected_unchanged':True,'no_production_deployment':True,'review_order':'embedded raw process output, exact output SHA, quality, paired directions and resource tables before narrative'};(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
