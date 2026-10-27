from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;removed=[]
def delete(f):
 if f.is_file():removed.append({'path':str(f),'bytes':f.stat().st_size});f.unlink()
for name in ('factors.json','caps.json','extra.json'):
 for item in json.loads((p/name).read_text()).values():
  f=Path(item['path']);assert f.name.startswith('nvngx_dlssnr_sm86_v27_')
  if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'];delete(f)
  delete(f.with_suffix('.manifest.json'))
cache=p/'artifacts'
if cache.exists():
 removed.append({'path':str(cache),'bytes':sum(f.stat().st_size for f in cache.rglob('*') if f.is_file())});shutil.rmtree(cache)
for d in ('ptx-v27-bench','ptx-v27-profile'):
 root=Path('/mnt/c/DLSS5-5090-dll')/d
 for f in root.glob('*.rgb32'):delete(f)
 if root.exists() and not any(root.iterdir()):root.rmdir()
delete(Path('/mnt/c/DLSS5-5090-dll/nvngx.dll_runner/bench_profile.exe'))
for pattern in ('*.csv','*.log'):
 for f in p.glob(pattern):
  data=f.read_bytes()
  if b'\r\n' in data:f.write_bytes(data.replace(b'\r\n',b'\n'))
(p/'cleanup.json').write_text(json.dumps({'removed':removed,'removed_bytes':sum(x['bytes'] for x in removed),'retained':'canonical V27 DLL and all textual evidence'},ensure_ascii=False,indent=2)+'\n');print('removed bytes',sum(x['bytes'] for x in removed))
