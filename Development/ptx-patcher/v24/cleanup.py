"""Remove only SHA-verified V2.4 temporary binaries; retain canonical V2.4."""
from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert sha(s['path'])==s['sha256'];removed=[]
for filename in ['builds.json','caps.json']:
 for name,r in json.loads((p/filename).read_text()).items():
  f=Path(r['path']);assert f.parent==root and f.name==f'nvngx_dlssnr_sm86_v24_{name}.dll' and str(f)!=s['path']
  if f.exists():
   assert sha(f)==r['sha256'];removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':r['sha256']});f.unlink()
  manifest=f.with_suffix('.manifest.json')
  if manifest.exists():manifest.unlink()
f=root/'nvngx.dll_runner/bench_profile.exe'
if f.exists():removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)});f.unlink()
bench=root/'ptx-v24-bench'
if bench.exists():
 for f in bench.glob('*.rgb32'):removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 if not any(bench.iterdir()):bench.rmdir()
profile=root/'ptx-v24-profile'
if profile.exists() and not any(profile.iterdir()):profile.rmdir()
art=p/'artifacts'
if art.exists():
 fs=[f for f in art.rglob('*') if f.is_file()];removed.append({'path':str(art),'files':len(fs),'bytes':sum(f.stat().st_size for f in fs)});shutil.rmtree(art)
f=p/'codegen-adjacent-audit.json'
if f.exists():f.unlink()
for f,r in json.loads((p/'protected-before-cleanup.json').read_text()).items():assert sha(f)==r['sha256']
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(x['bytes'] for x in removed),'retained':s['path'],'retained_sha256':sha(s['path']),'protected_files_unchanged':True},indent=2)+'\n');print('Cleaned',sum(x['bytes'] for x in removed),'bytes, retained canonical V2.4 and protected deployment')
