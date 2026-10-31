from pathlib import Path
import json,re,hashlib,datetime
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());rows=[];counts={};gold={}
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[n])==38
for name in ['smoke','timed','repeat']:
 f=p/(('bench' if name=='timed' else name)+'.json')
 if not f.exists():continue
 rr=json.loads(f.read_text());counts[name]=len(rr)
 for r in rr:
  met={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',r['process_output'].split('SUMMARY')[-1])};assert met==r['metrics'] and r['returncode']==0 and r['quality']['nonfinite']==0;assert r['dll_sha256']==cs[r['variant']]['sha256']
  if not cs[r['variant']]['approximate']:
   assert r['quality']['bitdiff']==r['quality']['maxabs']==0;k=(r['warmup'],r['iterations'],r['width'])
   if k not in gold:gold[k]=hashlib.sha256((Path('/mnt/c/DLSS5-5090-dll/ptx-v36-bench')/f'gold-{k[0]}-{k[1]}-{k[2]}.rgb32').read_bytes()).hexdigest()
   assert gold[k]==r['quality']['sha256']
  if name!='smoke':assert (r['warmup'],r['iterations'])==(50,80)
 rows+=rr
nc=len(json.loads((p/'timing-candidates.json').read_text()));assert counts['timed']==nc*24 and counts['smoke']==len(cs)*3
ordered=sorted(rows,key=lambda r:r['begin']);assert all(a['end']<=b['begin'] for a,b in zip(ordered,ordered[1:]));first=datetime.datetime.fromisoformat(ordered[0]['begin']).timestamp();assert max(f.stat().st_mtime for f in (p/'artifacts').rglob('*') if f.suffix in ('.ptx','.cubin'))<first
summary=json.loads((p/'timing-summary.json').read_text());eligible=json.loads((p/'repeat-eligible.json').read_text());winners=[]
for n in eligible:
 first_round=summary['timed'][n];repeat=summary.get('repeat',{}).get(n,{});assert len(repeat)==3
 if all(r['quality_pass'] for r in list(first_round.values())+list(repeat.values())) and all(r['directions'][d]['gain_percent']>0 for r in repeat.values() for d in ['forward','reverse']):winners.append(n)
old=json.loads((p/'protected-before.json').read_text());after={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in old};assert old==after;(p/'protected-after.json').write_text(json.dumps(after,indent=2)+'\n')
branches={}
for b in [5,6,7]:branches[str(b)]={'state':'Open','n':0 if any(cs[n]['branch']==b for n in winners) else 1}
v={'passed':True,'counts':counts,'exact_runs':sum(not cs[r['variant']]['approximate'] for r in rows),'approximate_runs':sum(cs[r['variant']]['approximate'] for r in rows),'all_measurements_serial':True,'construction_and_GPU_queries_before_clean_measurements':True,'repeat_eligible':eligible,'winners':winners,'branches':branches,'protected_paths':len(old),'protected_unchanged':True,'no_production_deployment':True,'scope':'fixed V3.1 baseline, three deterministic benchmark inputs; empirical Pack4 is not a static activation bound; async cases only publication-certified selected loads'};(p/'validation.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
