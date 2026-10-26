from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;rows=[]
for w in [1280,1600,1920]:
 keep=p/f'artifacts/outputs/candidate-b-m3-{w}.rgb32';h=hashlib.sha256(keep.read_bytes()).hexdigest()
 for f in (p/'artifacts/outputs').glob(f'*-{w}.rgb32'):
  if f==keep or f.is_symlink():continue
  b=f.read_bytes();assert hashlib.sha256(b).hexdigest()==h;rows.append({'path':str(f),'bytes':len(b),'sha256':h,'action':'deduplicate'});f.unlink();f.symlink_to(keep.name)
for name in ['m1','m3','abi']:
 d=p/'artifacts'/name
 for f in d.rglob('*'):
  if f.is_file() and not f.is_symlink():rows.append({'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove temporary prototype'})
 shutil.rmtree(d)
(p/'cleanup.json').write_text(json.dumps({'removed_bytes':sum(r['bytes'] for r in rows),'files':rows},indent=2)+'\n');print(sum(r['bytes'] for r in rows),'bytes removed/deduplicated')
