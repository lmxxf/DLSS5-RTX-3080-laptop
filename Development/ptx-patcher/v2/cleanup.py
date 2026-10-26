from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');rows=[]
# Preserve original cuobjdump resource reports, not huge regenerable disassembly.
dest=p/'resource-usage';dest.mkdir(exist_ok=True)
for tag in ['old','new','v7']:
 for f in (p/'artifacts'/tag).glob('*-res.txt'):
  if tag=='v7' and '-sm86-' not in f.name:continue
  shutil.copy2(f,dest/(tag+'-'+f.name))
def remove(f):
 rows.append({'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()});f.unlink()
for directory in [root/'discord_v7',root/'ptx-v2-bench']:
 for f in directory.glob('*.rgb32'):remove(f)
for directory in [p/'artifacts/old',p/'artifacts/new',p/'artifacts/v7']:
 for f in directory.iterdir():
  if f.is_file():remove(f)
(p/'cleanup.json').write_text(json.dumps({'removed_bytes':sum(x['bytes'] for x in rows),'files':rows,'new_DLL_retained':str(root/'nvngx_dlssnr_sm86_v2.dll')},indent=2)+'\n');print('removed bytes',sum(x['bytes'] for x in rows))
