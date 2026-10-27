"""Clean only verified V2.3 experiment binaries, preserving canonical recommendation."""
from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert sha(s['path'])==s['sha256'];removed=[]
for meta in ['build.json','sync-probe-build.json','nosleep-build.json']:
 r=json.loads((p/meta).read_text());f=Path(r['path']);assert f.parent==root and 'v23' in f.name and str(f)!=s['path']
 if f.exists():
  assert sha(f)==r['sha256'];removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':r['sha256']});f.unlink()
  manifest=f.with_suffix('.manifest.json')
  if manifest.exists():manifest.unlink()
for prefix in ['events','trace','decode-events']:
 for w in [1280,1920]:
  f=root/f'v23-{prefix}-{w}.rgb32'
  if f.exists():removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
f=root/'nvngx.dll_runner/bench_profile.exe'
if f.exists():removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)});f.unlink()
bench=root/'ptx-v23-bench'
if bench.exists():
 for f in bench.glob('*.rgb32'):removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 if not any(bench.iterdir()):bench.rmdir()
art=p/'artifacts'
if art.exists():
 fs=[f for f in art.rglob('*') if f.is_file()];removed.append({'path':str(art),'files':len(fs),'bytes':sum(f.stat().st_size for f in fs)});shutil.rmtree(art)
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(r['bytes'] for r in removed),'retained':s['path'],'retained_sha256':sha(s['path'])},indent=2)+'\n');print('Cleaned',sum(r['bytes'] for r in removed),'bytes; canonical V2.3 retained')
