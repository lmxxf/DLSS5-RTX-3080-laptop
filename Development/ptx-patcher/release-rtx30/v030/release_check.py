from pathlib import Path
import json,zipfile,hashlib,configparser
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';packages=json.loads((p/'packages.json').read_text());SHA='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
checks={rel:h for h,rel in [line.split('  ',1) for line in (out/'SHA256SUMS.txt').read_text().splitlines()]};assert set(checks)=={r['name'] for r in packages};assert len(list(out.glob('*.zip')))==3
for r in packages:
 path=Path(r['path']);assert sha(path)==r['sha256']==checks[r['name']];assert (out/(r['name']+'.sha256')).read_text().strip()==r['sha256']+'  '+r['name']
 with zipfile.ZipFile(path) as z:
  assert hashlib.sha256(z.read('nvngx_dlssnr.dll')).hexdigest()==SHA
  if r['name'].startswith('OptiScaler'):
   for name,v1,v2 in [('OptiScaler.ini','1.0','1.0'),('OptiScaler-增强风格.ini','1.5','1.1')]:
    ini=configparser.ConfigParser(strict=False,interpolation=None);ini.read_string(z.read(name).decode('utf-8-sig'));s=ini['DlssNr'];assert s['TransferStrength']==v1 and s['ColourStrength']==v2;assert s['NrBackend']=='nvidia'
   assert hashlib.sha256(z.read('dxgi.dll')).hexdigest()=='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2'
  else:assert hashlib.sha256(z.read('Magpie.exe')).hexdigest()=='b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea'
  assert len(z.namelist())==r['files']
 assert (out/'archive/v0.2.0'/r['name'].replace('0.3.0','0.2.0')).exists()
sigs=json.loads((p/'windows-signatures.json').read_text(encoding='utf-8-sig'));assert len(sigs)==4;assert all(r.get('SHA256',SHA)==SHA for r in sigs)
mag=json.loads((out/'Magpie-DLSS5-RTX30-0.3.0/config/config.json').read_text(encoding='utf-8-sig'));assert any(m['name']=='DLSS5-RTX30-PTX' and m['effects'][0]['name']=='DLSSNR\\DLSSNR_AI_Filter' for m in mag['scalingModes'])
print('PASS all3 final ZIP SHA lists/core/original hosts/default+enhanced INIs/Magpie patch;old archives retained;Windows live SHA status retained')

live=json.loads((p/'live.json').read_text());assert live['main_fast_sha256']==SHA
for site in live['sites']:
 base=Path(site['path']);assert sha(base/'nvngx_dlssnr.dll')==SHA
 assert json.loads((base/'release.json').read_text())['version']=='0.3.0'
 assert all(sha(base/n)==h for n,h in site['preserved'].items())
 for line in (base/'SHA256SUMS.txt').read_text().splitlines():
  h,n=line.split('  ',1);assert sha(base/n)==h
 if (base/'OptiScaler.ini').exists():
  c=configparser.ConfigParser(strict=False,interpolation=None);c.read_string((base/'OptiScaler.ini').read_text(encoding='utf-8-sig'));assert c['DlssNr']['TransferStrength']=='1.0' and c['DlssNr']['ColourStrength']=='1.0'
assert not (out/'release-v0.2.0.json').exists() and (out/'archive/v0.2.0/release-v0.2.0.json').exists()
assert not (out/'Magpie-DLSS5-RTX30-0.2.0').exists()
report={'version':'0.3.0','core_sha256':SHA,'packages':packages,'live_sites':live['sites'],'main_fast_sha256':live['main_fast_sha256'],'smoke':json.loads((p/'smoke-results.json').read_text()),'windows_signatures':sigs,'old020_archived':True,'configs_and_hosts_unchanged':True,'public_upload':False,'git_push':False}
(p/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print('PASS V030 final live manifests, preserved configs/hosts, archived V020, package hashes')

for profile in json.loads((p/'deployment.json').read_text())['profiles']:
 with zipfile.ZipFile(out/(profile['name']+'.zip')) as z:
  for n,h in profile['preserved_files'].items():assert hashlib.sha256(z.read(n)).hexdigest()==h,(profile['label'],n)
print('PASS ZIP non-NR/non-metadata bytes identical to V020 after smoke')
