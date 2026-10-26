from pathlib import Path
import hashlib,json,os
p=Path(__file__).resolve().parent;rows=[];seen={}
for f in sorted((p/'artifacts/outputs').glob('*.rgb32')):
 if f.is_symlink():continue
 h=hashlib.sha256(f.read_bytes()).hexdigest();size=f.stat().st_size
 if f.name.startswith('quick-'):
  rows.append({'path':str(f.relative_to(p)),'sha256':h,'bytes':size,'action':'remove failed quick output; statistics/log retained'});f.unlink();continue
 if h in seen:
  rows.append({'path':str(f.relative_to(p)),'sha256':h,'bytes':size,'action':'deduplicate to relative symlink','target':str(seen[h].relative_to(p))});f.unlink();f.symlink_to(os.path.relpath(seen[h],f.parent))
 else:seen[h]=f
for f in (p/'artifacts/tail/modules').iterdir():
 if f.suffix=='.ll' or f.name.endswith('.phase1.cu'):
  rows.append({'path':str(f.relative_to(p)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'action':'remove regenerable compiler intermediate'});f.unlink()
(p/'cleanup.json').write_text(json.dumps({'removed_or_deduplicated_bytes':sum(x['bytes'] for x in rows),'files':rows},indent=2)+'\n');print(sum(x['bytes'] for x in rows),'bytes removed/deduplicated')
