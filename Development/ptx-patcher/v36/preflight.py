from pathlib import Path
import json,hashlib,collections
p=Path(__file__).resolve().parent;cs=json.loads((p/'candidates.json').read_text());res=json.loads((p/'resources.json').read_text());rows=json.loads((p/'smoke.json').read_text());assert len(rows)==3*len(cs)
for r in rows:
 assert r['quality']['nonfinite']==0
 if not cs[r['variant']]['approximate']:assert r['quality']['bitdiff']==r['quality']['maxabs']==0
for n,c in cs.items():assert hashlib.sha256(Path(c['path']).read_bytes()).hexdigest()==c['sha256'] and len(res[n])==38 and all(x[1]=='inline' for x in c['manifest'])
assert json.loads((p/'async-primitive.json').read_text())['word_mismatches']==0
assert all(r['mismatches']==0 for r in json.loads((p/'primitive-tests.json').read_text()))
sass=json.loads((p/'isolated-sass.json').read_text());assert sass['pack4']['core_count']==4 and sass['pack3']['core_count']==3
ra=json.loads((p/'pack-range-audit.json').read_text());assert sum(ra['counts'].values())==8944
# Promote no empirical claim into a static range proof. All candidates only use
# recorded input/output precision to qualify for timed testing.
qualified=[];identical=[]
for n,c in cs.items():
 if n=='baseline':continue
 rr=[r for r in rows if r['variant']==n]
 if c['sha256']==cs['baseline']['sha256']:identical.append(n)
 elif all(r['quality']['quality_pass'] for r in rr):qualified.append(n)
(p/'timing-candidates.json').write_text(json.dumps(qualified,indent=2)+'\n');(p/'preflight.json').write_text(json.dumps({'passed':True,'clean_smoke_runs':len(rows),'timing_candidates':qualified,'baseline_identical_not_rebenchmarked':identical,'range_counts':ra['counts'],'core_SASS':{k:v['core'] for k,v in sass.items()},'no_per_run_log_files':True,'quality_policy':'same predeclared V3.1 reference and 50dB / 1/64 / finite / sky0; empirical output equality is not an intermediate-range proof'},indent=2)+'\n');print('preflight PASS',len(qualified),'timing candidates')
