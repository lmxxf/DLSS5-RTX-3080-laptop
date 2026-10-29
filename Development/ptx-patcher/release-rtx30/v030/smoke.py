from pathlib import Path
import json,subprocess,shutil,hashlib,re
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');d=json.loads((p/'deployment.json').read_text());rows=[];core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';win=lambda f:str(f).replace('/mnt/c/','C:/')
for profile in d['profiles']:
 label=profile['label'];stage=Path(profile['stage']);log=p/(label+'-native-smoke.log');args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,win(stage/'nvngx_dlssnr.dll'),'1280','720','2','3','5',win(root/'release-v030-tools'/f'{label}-native.rgb32'),'sky']
 with log.open('w') as f:ret=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT).returncode
 text=log.read_text();assert ret==0 and 'nonfinite=0' in text and 'SNIP_CREATE18=0x00000001' in text,(label,ret)
 rows.append({'label':label,'test':'NGX Feature18 native DLL load/create/evaluate','returncode':ret,'NR_sha256':hashlib.sha256((stage/'nvngx_dlssnr.dll').read_bytes()).hexdigest(),'summary':text.split('SUMMARY')[-1].strip()})
 if label=='Magpie':continue
 before={f.relative_to(stage).as_posix() for f in stage.rglob('*') if f.is_file()};ini=(stage/'OptiScaler.ini').read_bytes()
 try:
  for exe in ['ffx_nr_smoke.exe','ffx_loader_smoke.exe']:shutil.copy2(root/'release-v030-tools'/exe,stage/exe)
  shutil.copy2(root/'nvngx_dlss.dll',stage/'nvngx_dlss.dll')
  loader=p/(label+'-ffx-loader.log')
  with loader.open('w') as f:rr=subprocess.run([str(stage/'ffx_loader_smoke.exe'),win(stage/'amd_fidelityfx_dx12.dll')],cwd=stage,stdout=f,stderr=subprocess.STDOUT).returncode
  assert rr==0,(label,'FFX loader',rr)
  ffxlog=p/(label+'-ffx-smoke.log');args=[str(stage/'ffx_nr_smoke.exe'),core,win(stage/'amd_fidelityfx_dx12.dll'),'1280','720','2','3','5',win(root/'release-v030-tools'/f'{label}-ffx.rgb32'),'sky']
  with ffxlog.open('w') as f:rr=subprocess.run(args,cwd=stage,stdout=f,stderr=subprocess.STDOUT).returncode
  host=stage/'OptiScaler.log';hosttext=host.read_text(encoding='utf-8-sig',errors='replace') if host.exists() else '';(p/(label+'-host.log')).write_text(hosttext)
  assert rr==0 and 'nonfinite=0' in ffxlog.read_text(),(label,rr)
  assert 'composition:' in hosttext and 'detail 1.00, colour 1.00' in hosttext and ('running before SR' in hosttext or 'before SR' in hosttext),(label,'no NR composition evidence')
  rows.append({'label':label,'test':'FFX loader plus actual FFX→NGX→NR composition','returncode':rr,'default_strength':'1.0/1.0','NR_composition_observed':True,'summary':ffxlog.read_text().split('SUMMARY')[-1].strip()})
 finally:
  (stage/'OptiScaler.ini').write_bytes(ini)
  for f in list(stage.rglob('*')):
   if f.is_file() and f.relative_to(stage).as_posix() not in before:f.unlink()
(p/'smoke-results.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS:3 native package DLL smokes +2 complete FFX→NR package smokes')
