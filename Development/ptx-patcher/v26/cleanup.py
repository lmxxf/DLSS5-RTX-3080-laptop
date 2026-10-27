"""Delete only verified temporary V2.6 data; retain the recommended DLL."""
from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert sha(s['path'])==s['sha256'];removed=[]
r=json.loads((p/'build.json').read_text());f=Path(r['path']);assert f.parent==root and f.name=='nvngx_dlssnr_sm86_v26_lowhigh.dll' and str(f)!=s['path']
if f.exists():assert sha(f)==r['sha256'];removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':r['sha256']});f.unlink()
manifest=f.with_suffix('.manifest.json')
if manifest.exists():manifest.unlink()
bench=root/'ptx-v26-bench'
if bench.exists():
 for f in bench.glob('*.rgb32'):removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 if not any(bench.iterdir()):bench.rmdir()
art=p/'artifacts'
if art.exists():
 files=[f for f in art.rglob('*') if f.is_file()];removed.append({'path':str(art),'files':len(files),'bytes':sum(f.stat().st_size for f in files)});shutil.rmtree(art)
for f,r in json.loads((p/'protected-before-cleanup.json').read_text()).items():assert sha(f)==r['sha256']
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(x['bytes'] for x in removed),'retained':s['path'],'retained_sha256':sha(s['path']),'protected_files_unchanged':True},indent=2)+'\n');print('Removed',sum(x['bytes'] for x in removed),'bytes; V2.6 retained, production/references unchanged')
