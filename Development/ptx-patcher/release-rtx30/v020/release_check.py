from pathlib import Path
import json,zipfile,hashlib,configparser
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';packages=json.loads((p/'packages.json').read_text());SHA='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
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
 assert (out/'archive/v0.1.0'/r['name'].replace('0.2.0','0.1.0')).exists()
sigs=json.loads((p/'windows-signatures-live.json').read_text(encoding='utf-8-sig'));assert len(sigs)==4;assert all(r.get('SHA256',SHA)==SHA for r in sigs)
mag=json.loads((out/'Magpie-DLSS5-RTX30-0.2.0/config/config.json').read_text(encoding='utf-8-sig'));assert any(m['name']=='DLSS5-RTX30-PTX' and m['effects'][0]['name']=='DLSSNR\\DLSSNR_AI_Filter' for m in mag['scalingModes'])
print('PASS all3 final ZIP SHA lists/core/original hosts/default+enhanced INIs/Magpie patch;old archives retained;Windows live SHA status retained')
