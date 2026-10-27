from pathlib import Path
import json,hashlib,re
p=Path(__file__).resolve().parent
read=lambda n:json.loads((p/n).read_text())
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for b in iter(lambda:s.read(8<<20),b''):h.update(b)
 return h.hexdigest()
rows=read('bench.json');smoke=read('smoke.json');assert len(rows)==240 and len(smoke)==11
for r in rows+smoke:
 assert r['quality']['bitdiff']==0 and r['quality']['maxabs']==0 and r['metrics']['nonfinite']==0
 if r['width']==1280:assert r['quality']['sky_sign_changes']==0
assert all(r['warmup']==50 and r['iterations']==80 for r in rows)
for name,meta in read('protected.json').items():assert sha(name)==meta['sha256'],name
report=p.parents[1]/'doc/性能评估20261028-0335.md';assert sha(report)==read('audit.json')['report_sha256']
assert sum(map(int,re.findall(r'Ran (\d+) test',(p/'regression.log').read_text())))==13
result={'passed':True,'formal_runs':len(rows),'smoke_runs':len(smoke),'endframe_bitdiff':0,'nonfinite':0,'protected_files_unchanged':True,'source_report_unchanged':True,'regression_tests':13,'all_candidates_original_slot_O4':all('ELF O4' in r['compile'] and all(x[1]=='inline' for x in r['manifest']) for r in read('candidates.json').values())}
if (p/'combo-bench.json').exists():
 extra=read('combo-bench.json');assert all(r['quality']['bitdiff']==0 and r['metrics']['nonfinite']==0 for r in extra);assert len(extra)==24 and all(r['warmup']==50 and r['iterations']==80 and r['quality']['maxabs']==0 for r in extra);result['combo_runs']=len(extra);result['total_formal_runs']=len(rows)+len(extra);result['total_runs']=len(rows)+len(smoke)+len(extra)
if (p/'selected.json').exists():
 s=read('selected.json');assert sha(s['path'])==s['sha256'];result['selection']=s
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',result)
