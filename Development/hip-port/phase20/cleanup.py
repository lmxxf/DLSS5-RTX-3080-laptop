from pathlib import Path
import hashlib,json,os,shutil
p=Path(__file__).resolve().parent;r=p.parent;rows=[]
for w in [1280,1600,1920]:
 candidate=p/f'artifacts/outputs/candidate-b-{w}.rgb32';ref=r/f'phase19/artifacts/outputs/candidate-b-m3-{w}.rgb32'
 for f in (p/'artifacts/outputs').glob(f'*-{w}.rgb32'):
  if f==candidate or f.is_symlink():continue
  target=ref if f.name.startswith('baseline') else candidate;h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==hashlib.sha256(target.read_bytes()).hexdigest();rows.append({'file':str(f),'bytes':f.stat().st_size,'sha256':h,'action':'deduplicate'});f.unlink();f.symlink_to(os.path.relpath(target,f.parent))
probe=p/'artifacts/probe'
for f in probe.rglob('*'):
 if f.is_file():rows.append({'file':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove reproducible probe build'})
shutil.rmtree(probe)
for f in (p/'artifacts/candidate/modules').iterdir():
 if f.name.endswith('.phase1.cu') or f.suffix=='.ll':rows.append({'file':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove compiler intermediate'});f.unlink()
(p/'cleanup.json').write_text(json.dumps({'removed_bytes':sum(x['bytes'] for x in rows),'files':rows,'default':'Phase19 retained','candidate':'explicit diagnostic only'},indent=2)+'\n');print(sum(x['bytes'] for x in rows),'bytes removed/deduplicated')
