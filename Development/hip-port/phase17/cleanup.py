from pathlib import Path
import json,hashlib,shutil,os
p=Path(__file__).resolve().parent;rows=[]
# Keep one independently produced candidate output per tier; alias identical repeats.
for w in [1280,1600,1920]:
 keep=p/f'artifacts/outputs/candidate-b-nc-abba-{w}.rgb32';h=hashlib.sha256(keep.read_bytes()).hexdigest()
 for f in (p/'artifacts/outputs').glob(f'*-{w}.rgb32'):
  if f==keep or f.is_symlink():continue
  raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
  rows.append({'path':str(f.relative_to(p)),'bytes':len(raw),'sha256':h,'action':'deduplicate by relative symlink','target':keep.name});f.unlink();f.symlink_to(keep.name)
for directory in [p/'artifacts/single',p/'artifacts/probe']:
 for f in directory.iterdir():
  if f.is_file() and (f.suffix in ['.bin','.ll','.hsaco','.ptx'] or f.name in ['host','prepare'] or f.name.endswith('.phase1.cu')):
   rows.append({'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove regenerable fixture/compiler output'});f.unlink()
for f in (p/'artifacts/candidate/modules').iterdir():
 if f.suffix=='.ll' or f.name.endswith('.phase1.cu'):
  rows.append({'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove compiler intermediate'});f.unlink()
shutil.rmtree(p/'artifacts/abi')
(p/'cleanup.json').write_text(json.dumps({'removed_or_deduplicated_bytes':sum(r['bytes'] for r in rows),'files':rows,'retained':'one40-module set/PTX/generated C32 source,three actual candidate RGB outputs,selected alias,all measured hashes/logs/telemetry,shared Phase16 archive untouched'},indent=2)+'\n');print(sum(r['bytes'] for r in rows),'bytes removed/deduplicated')
