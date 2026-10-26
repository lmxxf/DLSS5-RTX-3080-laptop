from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;art=p/'artifacts';rows=[]
for w in [1280,1600,1920]:
 keep=art/f'outputs/candidate-b-final-{w}.rgb32';h=hashlib.sha256(keep.read_bytes()).hexdigest()
 for f in (art/'outputs').glob(f'*-{w}.rgb32'):
  if f==keep or f.is_symlink():continue
  raw=f.read_bytes();assert hashlib.sha256(raw).hexdigest()==h,f;rows.append({'path':str(f.relative_to(p)),'bytes':len(raw),'sha256':h,'action':'deduplicate to actual final candidate','target':keep.name});f.unlink();f.symlink_to(keep.name)
for directory in list(art.iterdir()):
 if directory.name in ['selected','outputs','benchmark_cuda_nn']:continue
 if directory.is_dir():
  for f in directory.rglob('*'):
   if f.is_file() and not f.is_symlink():rows.append({'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove reproducible experiment/probe artifact'})
  shutil.rmtree(directory)
 elif directory.is_file():rows.append({'path':str(directory.relative_to(p)),'bytes':directory.stat().st_size,'sha256':hashlib.sha256(directory.read_bytes()).hexdigest(),'action':'remove rejected experiment artifact'});directory.unlink()
for f in (art/'selected/modules').iterdir():
 if f.suffix=='.ll' or f.name.endswith('.phase1.cu'):rows.append({'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'action':'remove compiler intermediate'});f.unlink()
(p/'cleanup.json').write_text(json.dumps({'removed_or_deduplicated_bytes':sum(x['bytes'] for x in rows),'files':rows,'retained':'final standalone40modules/PTX/2generated sources,three actual candidate outputs,all SHA/logs/telemetry/resource evidence,Phase17 shared baseline unchanged'},indent=2)+'\n');print(sum(x['bytes'] for x in rows),'bytes removed/deduplicated')
