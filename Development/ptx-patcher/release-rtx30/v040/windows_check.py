from common import *
d=read(P/'deployment.json');live=read(P/'live.json');packages=read(P/'packages.json');files=[]
for pf in d['profiles']:files.append({'Label':'staged:'+pf['label'],'Path':win(Path(pf['stage'])/'nvngx_dlssnr.dll'),'Expected':SHA,'Kind':'PE'})
for s in live['sites']:files.append({'Label':'live:'+s['label'],'Path':win(s['installed_NR']),'Expected':SHA,'Kind':'PE'})
for x in packages:files.append({'Label':'ZIP:'+x['name'],'Path':win(x['path']),'Expected':x['sha256'],'Kind':'ZIP'})
files.append({'Label':'sealed PTX V4.0','Path':win(CORE),'Expected':SHA,'Kind':'PE'});driver=Path('/mnt/c/Windows/System32/DriverStore/FileRepository/nvtfi.inf_amd64_039ce3d14607c6bc/_nvngx.dll');files.append({'Label':'installed NVIDIA driver NGX core','Path':win(driver),'Expected':sha(driver),'Kind':'PE'});f=TOOLS/'windows-input.json';write(f,{'files':files});rr=run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',win(P/'signatures.ps1'),'-InputPath',win(f)],tag='Windows Get-FileHash and Authenticode');rows=json.loads(rr['stdout'].lstrip('\ufeff'));assert len(rows)==13
for x in rows:
 if x['Kind']=='PE':assert x['Authenticode']==('Valid' if x['Label']=='installed NVIDIA driver NGX core' else 'NotSigned'),x
write(P/'windows-signatures.json',rows);print('PASS13 Windows hashes;patched NR unsigned as expected;installed driver NGX Authenticode Valid')
