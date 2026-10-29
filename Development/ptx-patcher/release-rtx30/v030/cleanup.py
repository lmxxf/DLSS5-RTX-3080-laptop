from pathlib import Path
import json,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');assert (p/'validation.json').exists();assert 'PASS ZIP non-NR/non-metadata bytes identical to V020 after smoke' in (p/'release-check.log').read_text();removed=[]
for d in [root/'发布打包/.stage-v0.3.0',root/'release-v030-tools']:
 if d.exists():removed.append({'path':str(d),'bytes':sum(f.stat().st_size for f in d.rglob('*') if f.is_file())});shutil.rmtree(d)
for f in p.glob('*.log'):
 b=f.read_bytes();f.write_bytes(b.replace(b'\r\n',b'\n'))
for f in [p/'windows-signatures.json']:
 t=f.read_text(encoding='utf-8-sig');f.write_text(t)
(p/'cleanup.json').write_text(json.dumps(removed,indent=2,ensure_ascii=False)+'\n');print('Cleaned',sum(x['bytes'] for x in removed),'bytes')
