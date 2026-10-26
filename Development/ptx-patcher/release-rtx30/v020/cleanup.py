from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';stage=out/'.stage-v0.2.0';assert not(p/'cleanup.json').exists(),'Cleanup receipt already exists';rows=[]
for profile in json.loads((p/'deployment.json').read_text())['profiles']:
 d=Path(profile['stage']);assert d.parent==stage and d.is_dir();files=[f for f in d.rglob('*') if f.is_file()];rows.append({'directory':str(d),'bytes':sum(f.stat().st_size for f in files),'files':len(files),'sha256_manifest':hashlib.sha256((d/'SHA256SUMS.txt').read_bytes()).hexdigest()});shutil.rmtree(d)
if stage.exists():stage.rmdir()
for f in (root/'release-v020-tools').glob('*.rgb32'):
 rows.append({'file':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()});f.unlink()
(p/'cleanup.json').write_text(json.dumps({'removed_bytes':sum(r['bytes'] for r in rows),'items':rows,'retained':'all3 v0.2.0 ZIPs/live Magpie,v0.1.0 archive,deployment backups,V2/V2.1 source DLLs,smoke EXEs/header provenance','public_upload':False},indent=2)+'\n');print('removed bytes',sum(r['bytes'] for r in rows))
