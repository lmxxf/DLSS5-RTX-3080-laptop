from pathlib import Path
import json,hashlib,shutil,datetime
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';d=json.loads((p/'deployment.json').read_text());profiles={r['label']:Path(r['stage']) for r in d['profiles']};sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();backup=root/'backups/20261029-v030-metadata';assert not backup.exists();backup.mkdir(parents=True)
oldmag=out/'Magpie-DLSS5-RTX30-0.2.0';newmag=out/'Magpie-DLSS5-RTX30-0.3.0';assert oldmag.is_dir() and not newmag.exists()
oni=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content');sb=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64');sites=[('onimusha','OptiScaler-REFramework',oni),('onimusha-storage','OptiScaler-REFramework',oni/'_storage_'),('stellar','OptiScaler',sb),('magpie','Magpie',oldmag)]
meta=['README.txt','README.en.txt','DLSS5-RTX30-VERSION.txt','release.json','SHA256SUMS.txt','nvngx_dlssnr.manifest.json'];checks={};saved=[]
for label,profile,base in sites:
 assert sha(base/'nvngx_dlssnr.dll')==d['NR_sha256'],base
 checks[label]={n:sha(base/n) for n in ['dxgi.dll','nvngx.dll_dlssnr.dll','Magpie.exe','OptiScaler.ini','OptiScaler-增强风格.ini'] if (base/n).exists()}
 for n in meta:
  f=base/n
  if f.exists():dest=backup/label/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);saved.append({'path':str(f),'sha256':sha(f),'backup':str(dest)})
manifest=json.loads((p.parents[1]/'v31/candidates.json').read_text())['pack5']['manifest'];assert len(manifest)==15 and all(r[1]=='inline' for r in manifest)
for n in ['nvngx_dlssnr_sm86_fast.manifest.json']:
 f=root/n
 if f.exists():shutil.copy2(f,backup/n)
fast=root/'nvngx_dlssnr_sm86_fast.dll';assert sha(fast)==d['NR_sha256'];(root/'nvngx_dlssnr_sm86_fast.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
oldmag.rename(newmag)
records=[]
for label,profile,base in sites:
 if label=='magpie':base=newmag
 stage=profiles[profile]
 for n in meta[:4]:shutil.copy2(stage/n,base/n)
 (base/'nvngx_dlssnr.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 files=[f.relative_to(stage) for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt' and (base/f.relative_to(stage)).is_file()]+[Path('nvngx_dlssnr.manifest.json')]
 (base/'SHA256SUMS.txt').write_text(''.join(f'{sha(base/n)}  {n.as_posix()}\n' for n in sorted(set(files))))
 assert all(sha(base/n)==h for n,h in checks[label].items())
 records.append({'label':label,'path':str(base),'NR_sha256':sha(base/'nvngx_dlssnr.dll'),'preserved':checks[label],'checked_files':len(set(files))})
# Refresh existing install/uninstall current identities without altering original backup information.
for f in [root/'backups/20261024-StellarBlade-full/manifest.json',out/'StellarBlade-install-manifest.json',root/'StellarBlade-install-manifest.json']:
 if not f.exists():continue
 dest=backup/('manifest-'+str(len(saved))+'.json');shutil.copy2(f,dest);saved.append({'path':str(f),'backup':str(dest)});m=json.loads(f.read_text());m['archive']=str(out/'OptiScaler-DLSS5-RTX30-0.3.0.zip');m['archive_sha256']=sha(Path(m['archive']))
 for r in m.get('files',[]):
  if (sb/r['file']).exists():r['new_sha256']=sha(sb/r['file'])
 f.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
(p/'live.json').write_text(json.dumps({'sites':records,'main_fast_sha256':sha(fast),'manifest':manifest,'backup':str(backup),'saved':saved},indent=2,ensure_ascii=False)+'\n');print('PASS five existing core hashes; live metadata/checksums/fast manifest refreshed; config/hosts unchanged')
