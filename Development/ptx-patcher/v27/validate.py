from pathlib import Path
import json,hashlib,re
p=Path(__file__).resolve().parent
def read(n):return json.loads((p/n).read_text())
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
 return h.hexdigest()
sel=read('selected.json');assert sha(sel['path'])==sel['sha256'];assert Path(sel['path']).stat().st_size==266414592
reb=read('rebuild-manifest.json');assert len(reb['manifest'])==15 and all(x[1]=='inline' for x in reb['manifest']);assert reb['sha256']==sel['sha256']
rows=read('bench.json')+read('extra-bench.json')+read('smoke.json');assert len(rows)==170
for r in rows:
 assert r['quality']['bitdiff']==0 and r['quality']['maxabs']==0 and r['metrics']['nonfinite']==0
formal=[r for r in rows if r['warmup']==50 and r['iterations']==80];assert len(formal)==160
prof=read('profile-versions.json');assert len(prof)==12
for r in prof:
 assert r['warmup']==50 and r['iterations']==20 and r['nonfinite']==0
 assert sum(x['calls_per_frame'] for x in r['by_FB'].values())==82
for version in ('v22','v24','v26'):
 for w in (1280,1920):assert len({r['output_sha256'] for r in prof if r['version']==version and r['width']==w})==1
scope=read('parser-scope-check.json');assert scope['entries']==112 and not scope['mapping_deltas']
base=p/'artifacts/verify-v26.dll'
if base.exists():
 assert sha(base)=='04b01f0c963061e24d1fd34f5097043d4eeddb001c846d9002e4e2bdc73ad788'
 (p/'parser-binary-check.json').write_text(json.dumps({'V26_rebuilt_sha256':sha(base),'same_as_original':True,'all15_O4':True},indent=2)+'\n')
assert sum(map(int,re.findall(r'Ran (\d+) test', (p/'regression.log').read_text())))==13
report=p.parents[1]/'doc/性能评估20261028-0207.md';assert sha(report)=='72f865c754a42fbc0c0b39ba4bdfd8022a6b016040acbed14c65cf5911e2b7eb'
protected=read('protected-before-cleanup.json')
for name,meta in protected.items():assert sha(name)==meta['sha256']
result={'passed':True,'selected_sha256':sel['sha256'],'bytes':266414592,'O4_inline_fatbins':15,'uninstrumented_runs':170,'formal_50_80_runs':160,'all_endframe_bitdiff':0,'all_nonfinite':0,'profile_captures':12,'launches_per_frame':82,'parser_mapping_entries_unchanged':112,'regression_tests':13,'original_report_unchanged':True,'protected_hashes_unchanged':protected}
(p/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print('PASS',result['uninstrumented_runs'],'runs; protected hashes unchanged')
