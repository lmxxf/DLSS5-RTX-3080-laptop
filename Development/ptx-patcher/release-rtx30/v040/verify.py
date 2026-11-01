from common import *
import zipfile,configparser
D=read(P/'deployment.json');pkgs=read(P/'packages.json');live=read(P/'live.json');sm=read(P/'smoke-results.json');sigs=read(P/'windows-signatures.json');archive=read(P/'archive.json');assert len(pkgs)==3 and len(sm)==5 and all(x['returncode']==x['nonfinite']==0 for x in sm);assert live['complete'] and len(live['sites'])==5;assert sha(CORE)==SHA
listed={n:h for h,n in [s.split('  ',1) for s in (OUT/'SHA256SUMS.txt').read_text().splitlines()]};assert set(listed)=={x['name'] for x in pkgs};assert set(x.name for x in OUT.glob('*.zip'))==set(listed)
results=[]
for x in pkgs:
 f=Path(x['path']);assert sha(f)==x['sha256']==listed[x['name']];assert (OUT/(x['name']+'.sha256')).read_text().strip()==x['sha256']+'  '+x['name'];pf=next(pf for pf in D['profiles'] if x['name']==pf['name']+'.zip');stage=Path(pf['stage'])
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None;checks={n:h for h,n in [s.split('  ',1) for s in z.read('SHA256SUMS.txt').decode('utf-8-sig').splitlines()]};assert set(z.namelist())==set(checks)|{'SHA256SUMS.txt'};assert len(z.namelist())==x['files']
  for n,h in checks.items():
   hh=hashlib.sha256()
   with z.open(n) as s:
    for c in iter(lambda:s.read(8<<20),b''):hh.update(c)
   assert hh.hexdigest()==h,(x['name'],n)
   assert sha(stage/n)==h,(x['name'],'post-smoke-stage',n)
  assert checks['nvngx_dlssnr.dll']==SHA;meta=json.loads(z.read('release.json'));assert meta['version']=='0.4.0' and meta['ptx_sha256']==SHA and meta['ptx_version']=='V4.0';assert json.loads(z.read('nvngx_dlssnr.manifest.json'))==D['manifest'];assert all(checks[n]==h for n,h in pf['preserved_files'].items());assert not any(n.endswith('.log') for n in z.namelist())
  if pf['label']!='Magpie':
   for ini_name,a,b in [('OptiScaler.ini','1.0','1.0'),('OptiScaler-增强风格.ini','1.5','1.1')]:
    cfg=configparser.ConfigParser(strict=False,interpolation=None);cfg.read_string(z.read(ini_name).decode('utf-8-sig'));assert cfg['DlssNr']['TransferStrength']==a and cfg['DlssNr']['ColourStrength']==b and cfg['DlssNr']['NrBackend']=='nvidia'
   assert checks['dxgi.dll']=='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2'
  else:
   assert checks['Magpie.exe']=='b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea';cfg=json.loads(z.read('config/config.json'));assert any(q['name']=='DLSS5-RTX30-PTX' and q['effects'][0]['name']=='DLSSNR\\DLSSNR_AI_Filter' for q in cfg['scalingModes'])
 old=Path(pf['archived_source_zip']);assert sha(old)==pf['source_zip_sha256'];assert not Path(pf['source_zip']).exists();results.append({'name':x['name'],'CRC_pass':True,'member_SHA_pass':True,'stage_after_smoke_SHA_pass':True,'non_core_non_metadata_preserved':True,'version_manifest_pass':True,'archived_old_zip_SHA256':sha(old)})
for s in live['sites']:
 base=Path(s['installed_base']);assert sha(s['installed_NR'])==SHA;assert all(sha(base/n)==h for n,h in s['preserved_files'].items())
 if s['profile']:
  assert read(base/'release.json')['version']=='0.4.0'
  for line in (base/'SHA256SUMS.txt').read_text().splitlines():h,n=line.split('  ',1);assert sha(base/n)==h
assert not (OUT/'Magpie-DLSS5-RTX30-0.3.0').exists();assert (OUT/'Magpie-DLSS5-RTX30-0.4.0').is_dir();assert all(sha(Path(f))==h for f,h in D['historical_archives'].items());assert all(sha(Path(f))==h for f,h in D['protected_inputs'].items());assert sha(D['core_backup'])==OLD
for r in archive['files']:assert sha(r['archive_path'])==r['sha256'] and not Path(r['old_path']).exists() if Path(r['old_path']).name.endswith(('.zip','.sha256','release-v0.3.0.json')) else sha(r['archive_path'])==r['sha256']
assert len(sigs)==13 and all(x['SHA256']==SHA for x in sigs if x['Label'].startswith(('staged:','live:','sealed')))
assert not list(P.glob('*.log')) and not list(STAGE.rglob('*.log'));write(P/'validation.json',{'passed':True,'version':'0.4.0','PTX':'V4.0','core_sha256':SHA,'core_bytes':CORE.stat().st_size,'15_original_slots_O4_manifest':D['manifest'],'live_sites':live['sites'],'backup':str(BACKUP),'packages':pkgs,'package_integrity':results,'smoke':sm,'Windows_SHA_and_Authenticode':sigs,'smoke_test_count':5,'all_test_returncodes_zero':True,'all_test_nonfinite_zero':True,'configs_hosts_bridges_preserved':True,'old030_archived_byte_exact':True,'old010_020_archives_preserved':True,'sealed_inputs_unchanged':True,'per_run_log_fragments':0,'game_UI_or_FPS_retested':False,'public_upload':False,'git_push':False});print('PASS all5 live hashes,3 ZIP CRC/member SHA,5 smoke,13 Windows hashes/signatures;oldarchives/hosts/configs intact')
