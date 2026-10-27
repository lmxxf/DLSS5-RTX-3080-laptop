"""Delete only this experiment's verified temporary products."""
from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;s=json.loads((p/'selected.json').read_text());root=Path('/mnt/c/DLSS5-5090-dll');out=Path(s['path']);assert hashlib.sha256(out.read_bytes()).hexdigest()==s['sha256']
removed=[]
for v,r in json.loads((p/'builds.json').read_text()).items():
 f=Path(r['path']);assert f.parent==root and f.name==f'nvngx_dlssnr_sm86_v22_{v}.dll'
 if f.exists():
  assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'];removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 manifest=f.with_suffix('.manifest.json')
 if manifest.exists():manifest.unlink()
art=p/'artifacts'
if art.exists():
 fs=[f for f in art.rglob('*') if f.is_file()];removed.append({'path':str(art),'files':len(fs),'bytes':sum(f.stat().st_size for f in fs)});shutil.rmtree(art)
bench=root/'ptx-v22-bench'
if bench.exists():
 for f in bench.glob('*.rgb32'):
  removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 if not any(bench.iterdir()):bench.rmdir()
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(r['bytes'] for r in removed),'retained':s['path'],'retained_sha256':s['sha256']},indent=2)+'\n');print('Removed',sum(r['bytes'] for r in removed),'bytes; retained selected V2.2 DLL')
