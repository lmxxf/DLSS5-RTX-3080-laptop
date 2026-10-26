from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');selected=json.loads((p/'selected.json').read_text());recommended=root/'nvngx_dlssnr_sm86_v21.dll';assert hashlib.sha256(recommended.read_bytes()).hexdigest()==selected['sha256'];rows=[]
def remove(f,reason):
 rows.append({'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'reason':reason});f.unlink()
variants=json.loads((p/'build-results.json').read_text())['variants']
for variant,info in variants.items():
 f=Path(info['path']);assert f.parent==root and f.name.startswith('nvngx_dlssnr_sm86_v21_') and f!=recommended
 assert hashlib.sha256(f.read_bytes()).hexdigest()==info['sha256'];remove(f,'temporary candidate; caps, SHA and control evidence retained')
for f in (root/'ptx-v21-bench').glob('*.rgb32'):remove(f,'output compared to V2 before cleanup; hashes/metrics retained')
for f in (p/'artifacts').rglob('*'):
 if f.is_file():remove(f,'regenerable PTX/fatbin/cubin; final source rebuild identity proved')
(p/'cleanup.json').write_text(json.dumps({'removed_bytes':sum(x['bytes'] for x in rows),'files':rows,'retained':['V2 DLL','recommended V2.1 DLL','source DLL','cuobjdump resource reports','all benchmark/source/telemetry/SHA evidence']},indent=2)+'\n');print('removed bytes:',sum(x['bytes'] for x in rows))
