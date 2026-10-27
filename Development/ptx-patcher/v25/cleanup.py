"""Verified cleanup for an unpromoted experiment; keep the V2.4 recommendation."""
from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();s=json.loads((p/'selected.json').read_text());assert not s['V25_promoted'] and sha(s['path'])==s['sha256'];removed=[]
allowed={'nvngx_dlssnr_sm86_v25_hybrid.dll','nvngx_dlssnr_sm86_v25_fb0.dll','nvngx_dlssnr_v25_counter_DIAGNOSTIC.dll'}
for meta in ['build.json','fb0-build.json','counter-build.json']:
 r=json.loads((p/meta).read_text());f=Path(r['path']);assert f.parent==root and f.name in allowed
 if f.exists():assert sha(f)==r['sha256'];removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':r['sha256']});f.unlink()
 manifest=f.with_suffix('.manifest.json')
 if manifest.exists():manifest.unlink()
for name in ['bench_profile.exe','bench_counter.exe']:
 f=root/'nvngx.dll_runner'/name
 if f.exists():removed.append({'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)});f.unlink()
bench=root/'ptx-v25-bench'
if bench.exists():
 for f in bench.glob('*.rgb32'):removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
 if not any(bench.iterdir()):bench.rmdir()
art=p/'artifacts'
if art.exists():
 fs=[f for f in art.rglob('*') if f.is_file()];removed.append({'path':str(art),'files':len(fs),'bytes':sum(f.stat().st_size for f in fs)});shutil.rmtree(art)
for f,r in json.loads((p/'protected-before-cleanup.json').read_text()).items():assert sha(f)==r['sha256']
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(x['bytes'] for x in removed),'recommendation_retained':s,'protected_files_unchanged':True,'formal_V25_DLL_created':False},indent=2)+'\n');print('Removed',sum(x['bytes'] for x in removed),'bytes; V2.4 retained, no formal V2.5 promoted')
