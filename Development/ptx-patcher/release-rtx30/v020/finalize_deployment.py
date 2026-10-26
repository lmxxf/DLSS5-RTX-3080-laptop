from pathlib import Path
import json,hashlib,shutil,configparser,datetime
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';meta=json.loads((p/'deployment.json').read_text());backup=Path(meta['backup']);profiles={r['label']:Path(r['stage']) for r in meta['profiles']};sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();ONI=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content');SB=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64');MAG=out/'Magpie-DLSS5-RTX30-0.2.0'
assert all(stage.is_dir() for stage in profiles.values()), 'Audited stages already cleaned; do not rerun deployment finalizer without recreating them'
# Complete the RE package support files; keep exactly restored game-specific PTX INIs.
extra=[];stage=profiles['OptiScaler-REFramework'];plan=[]
for sub in ['', '_storage_']:
 for f in stage.rglob('*'):
  if not f.is_file():continue
  rel=f.relative_to(stage)
  if rel.as_posix() in ['OptiScaler.ini','SHA256SUMS.txt']:continue
  if sub and not (f.suffix.lower() in ['.dll','.ini'] or rel.parts[0]=='D3D12_Optiscaler'):continue
  target=ONI/sub/rel
  if target.exists() and sha(target)==sha(f):continue
  saved=backup/'onimusha-package-before'/('storage' if sub else 'root')/rel
  if target.exists():saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
  row={'target':str(target),'old_sha256':sha(target) if target.exists() else None,'new_sha256':sha(f),'backup':str(saved) if saved.exists() else None};extra.append(row);plan.append((f,target))
(backup/'onimusha-package-before.json').write_text(json.dumps(extra,indent=2)+'\n')
for f,target in plan:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);assert sha(f)==sha(target)
# Archive stale logs so the next game launch cannot be mistaken for Phase10.
logs=[]
for label,base in [('onimusha',ONI),('onimusha-storage',ONI/'_storage_'),('stellar',SB)]:
 f=base/'OptiScaler.log'
 if f.exists():
  dst=backup/'logs'/label/'OptiScaler.log';dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(f),str(dst));logs.append({'from':str(f),'backup':str(dst),'sha256':sha(dst)})
# Checksums describe deployed package files, allowing preserved local config values.
checks={}
for label,base in [('OptiScaler-REFramework',ONI),('OptiScaler',SB),('Magpie',MAG)]:
 stage=profiles[label];files=[f.relative_to(stage) for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt']
 assert all((base/rel).is_file() for rel in files)
 (base/'SHA256SUMS.txt').write_text(''.join(f'{sha(base/rel)}  {rel.as_posix()}\n' for rel in sorted(files)));checks[label]={'files':len(files),'manifest_sha256':sha(base/'SHA256SUMS.txt')}
# Preserve the original uninstall backup; update only its current-deployment identities.
full=root/'backups/20261024-StellarBlade-full/manifest.json';shutil.copy2(full,backup/'stellar-full-manifest-before.json');m=json.loads(full.read_text());m['archive']=str(out/'OptiScaler-DLSS5-RTX30-0.2.0.zip');m['archive_sha256']=sha(Path(m['archive']));m['files']=[r for r in m['files'] if (SB/r['file']).exists()]
for r in m['files']:r['new_sha256']=sha(SB/r['file'])
if not any(r['file']=='OptiScaler-增强风格.ini' for r in m['files']):m['files'].append({'file':'OptiScaler-增强风格.ini','status':'new','old_sha256':None,'new_sha256':sha(SB/'OptiScaler-增强风格.ini')})
for f in [full,out/'StellarBlade-install-manifest.json',root/'StellarBlade-install-manifest.json']:f.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n')
for r in m['files']:assert sha(SB/r['file'])==r['new_sha256']

def values(f):
 c=configparser.ConfigParser(strict=False,interpolation=None);c.read_string(f.read_text(encoding='utf-8-sig'));return dict(c['DlssNr'])
for base in [ONI,ONI/'_storage_',SB]:
 assert sha(base/'nvngx_dlssnr.dll')==meta['NR_sha256']
 v=values(base/'OptiScaler.ini')
 for k,val in {'nrbackend':'nvidia','whitepointsource':'1','preset':'2','style':'1','transferstrength':'1.0','colourstrength':'1.0'}.items():assert v[k]==val,(base,k,v[k])
for base in [ONI,ONI/'_storage_']:
 assert sha(base/'dxgi.dll')==meta['original_dxgi_sha256'];assert sha(base/'nvngx.dll_dlssnr.dll')==meta['forwarder_sha256'];assert (base/'dxgi.dll').read_bytes()[0x2b549:0x2b54b]==bytes.fromhex('75 03')
left=[str(f.relative_to(ONI)) for f in ONI.rglob('*') if f.name in ['LmxxfNrRuntime.dll','dlss5-amd.addon64','DLSS5-AMD']];assert not left,left
assert sha(root/'nvngx_dlssnr_sm86_fast.dll')==sha(root/'nvngx_dlssnr_sm86_v21.dll')==sha(MAG/'nvngx_dlssnr.dll')==meta['NR_sha256'];assert (root/'nvngx_dlssnr_sm86_v2.dll').exists()
assert sha(MAG/'Magpie.exe')=='b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea';assert not (out/'Magpie-DLSS5-RTX30-0.1.0').exists()
sig=json.loads((p/'windows-signatures.json').read_text(encoding='utf-8-sig'));assert all(r['Authenticode']=='NotSigned' for r in sig if r['Package']!='NVIDIA driver NGX core');assert next(r for r in sig if r['Package']=='NVIDIA driver NGX core')['Authenticode']=='Valid'
report={'version':'0.2.0','NR_sha256':meta['NR_sha256'],'main_fast_updated':True,'onimusha_root_storage_original_dxgi':True,'onimusha_root_storage_PT X'.replace(' ',''):True,'active_route_a_leftovers':left,'stellar_default':'1.0/1.0','stellar_optional':'OptiScaler-增强风格.ini=1.5/1.1','magpie_directory':str(MAG),'package_checksums':checks,'extra_onimusha_files_installed':len(extra),'old_logs_archived':logs,'stellar_uninstall_manifest_refreshed':True,'smoke_tests':json.loads((p/'smoke-results.json').read_text()),'Authenticode':'driver NGX core Valid;patched NR NotSigned by design;all Windows SHA checks match','public_upload':'not performed;no new URL supplied','backup':str(backup),'in_game_visual_test':'not performed in this release turn'}
(p/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');(backup/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print('PASS final deployment:main fast,Onimusha both mirrors/original host/no HIP,Stellar1.0/1.0,Magpie0.2.0,checksums/signature status')
