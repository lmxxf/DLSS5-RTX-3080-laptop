"""Deploy the verified Phase-10 CUDA runtime and modules; keep immutable PTX rollback files."""
from pathlib import Path,PurePosixPath
import zipfile,hashlib,json,re,shutil,datetime
repo=Path(__file__).resolve().parents[4]
game=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content')
backup=Path('/mnt/c/DLSS5-5090-dll/backups/Onimusha-ptx-0.1.0')
archive=Path('/mnt/c/DLSS5-5090-dll/amd的dlss5-0.44的打包/OptiScaler-REFramework-DLSS5-AMD-0.44.zip')
hip=repo/'Development/hip-port';selected=hip/'phase10/artifacts/selected/modules'
runtime=Path(__file__).resolve().parent/'artifacts/runtime/LmxxfNrRuntime.dll'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
assert runtime.is_file();expected=json.loads((selected.parent/'modules.sha256.json').read_text());assert len(expected)==40
for name,h in expected.items():assert sha(selected/name)==h,name
backup.mkdir(parents=True,exist_ok=True)
original={}
for name in ['OptiScaler.ini','nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']:
 p=game/name;dest=backup/name
 if p.exists():
  if dest.exists():assert sha(dest)==sha(p),'Refusing to overwrite a different backup: '+name
  else:shutil.copy2(p,dest)
 else:assert dest.exists(),name
 original[name]={'sha256':sha(dest),'bytes':dest.stat().st_size}
(backup/'backup-manifest.json').write_text(json.dumps(original,indent=2)+'\n')
extracted=[]
with zipfile.ZipFile(archive) as z:
 for info in z.infolist():
  rel=PurePosixPath(info.filename.replace('\\','/'))
  if not rel.parts or rel.parts[0] not in ['DLSS5-AMD','D3D12_Optiscaler','shaders'] or info.is_dir():continue
  assert not rel.is_absolute() and '..' not in rel.parts
  target=game.joinpath(*rel.parts);target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():
   save=backup/'replaced-files'/Path(*rel.parts);save.parent.mkdir(parents=True,exist_ok=True)
   if not save.exists():shutil.copy2(target,save)
  blob=z.read(info);target.write_bytes(blob)
  assert sha(target)==hashlib.sha256(blob).hexdigest(),str(rel)
  extracted.append(str(rel))
print('Extracted and SHA-verified',len(extracted),'support/weight/shader files',flush=True)
assets=game/'DLSS5-AMD/native-game-tiled-assets';mods=assets/'HIP/sm_86';mods.mkdir(parents=True,exist_ok=True)
for old in ['gfx1200','gfx1201']:
 p=assets/'HIP'/old
 if p.exists():shutil.rmtree(p)
for p in (assets/'HIP').glob('*.hsaco'):p.unlink()
for p in mods.glob('*.hsaco'):
 if p.name not in expected:p.unlink()
for name,h in expected.items():
 shutil.copy2(selected/name,mods/name);assert sha(mods/name)==h,name
shutil.copy2(selected/'AMPERE_WEIGHTS_V2',mods/'AMPERE_WEIGHTS_V2')
assert (mods/'AMPERE_WEIGHTS_V2').read_bytes()==(selected/'AMPERE_WEIGHTS_V2').read_bytes()
assert len(list(mods.glob('*.hsaco')))==40
assert not any((assets/'HIP'/n).exists() for n in ['gfx1200','gfx1201'])
def manifest(folder,paths):
 (folder/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(folder).as_posix()}\n' for p in sorted(paths)))
manifest(mods,list(mods.glob('*.hsaco'))+[mods/'AMPERE_WEIGHTS_V2'])
manifest(assets/'HIP',list(mods.glob('*.hsaco'))+[mods/'AMPERE_WEIGHTS_V2'])
shutil.copy2(runtime,game/'LmxxfNrRuntime.dll');assert sha(runtime)==sha(game/'LmxxfNrRuntime.dll')
def update_flags(path,values):
 s=path.read_text(encoding='utf-8-sig') if path.exists() else ''
 for k,v in values.items():
  pat=r'(?m)^'+re.escape(k)+r'=[^\r\n]*'
  if re.search(pat,s):s=re.sub(pat,k+'='+v,s)
  else:s+='\n'+k+'='+v+'\n'
 path.write_text(s,encoding='utf-8')
flags={'DLSS5_MULTI_PASS':'0.5','DLSS5_FAST_NUMERIC':'1','DLSS5_AMPERE_WEIGHTS':'1','DLSS5_CUDA_ARCH_NAME':'sm_86','DLSS5_LAB_C256_SPLIT':'0','DLSS5_STYLE':'1','DLSS5_NETWORK_FREE_RES':'1','DLSS5_HIP_GRAPH':'0','DLSS5_VIT_ADAPTIVE':'0'}
for n in ['default-config.txt','custom-config.txt','native-game-flags.txt']:
 p=game/'DLSS5-AMD'/n
 if n=='default-config.txt' or p.exists():update_flags(p,flags)
# Flip backend only after all files and manifests are in place.
p=game/'OptiScaler.ini';s=p.read_bytes().decode('utf-8-sig');nl='\r\n' if '\r\n' in s else '\n'
s=s.replace('\r\n','\n');values={'Enabled':'true','NrBackend':'lmxxf','WhitePointSource':'1','Preset':'2','Style':'1'}
m=re.search(r'(?ms)^\[DlssNr\]\n.*?(?=^\[|\Z)',s);assert m
block=m[0]
for k,v in values.items():
 pat=r'(?m)^'+re.escape(k)+r'=[^\n]*'
 if re.search(pat,block):block=re.sub(pat,k+'='+v,block)
 else:block+=k+'='+v+'\n'
s=s[:m.start()]+block+s[m.end():]
s=re.sub(r'(?m)^Dx12Upscaler=.*$', 'Dx12Upscaler=dlss',s)
p.write_bytes(s.replace('\n',nl).encode('utf-8'))
for name in ['nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']:
 p=game/name
 if p.exists():
  assert sha(p)==original[name]['sha256'];p.unlink() # Byte-identical rollback copy already verified.
for n in ['shaders/native_codec_encode.hlsl','shaders/native_codec_decode.hlsl','D3D12_Optiscaler/D3D12Core.dll']:
 assert (game/n).is_file(),n
small=list((assets/'small').glob('*.f16'))+list((assets/'small').glob('*.f32'));assert len(small)==93,len(small)
# Replace archived asset manifest after architecture replacement; exclude manifests and runtime logs.
manifest(assets,[p for p in assets.rglob('*') if p.is_file() and p.name!='SHA256SUMS'])
report={'time':datetime.datetime.now().isoformat(),'game':str(game),'backend':'lmxxf','runtime':{'bytes':runtime.stat().st_size,'sha256':sha(runtime)},'backup':str(backup),'original':original,'module_directory':str(mods),'modules':expected,'marker_sha256':sha(mods/'AMPERE_WEIGHTS_V2'),'small_weight_files':len(small),'cso_files':len(list(assets.rglob('*.cso'))),'extracted_files':len(extracted),'ini_sha256':sha(game/'OptiScaler.ini'),'flags':flags,'unchanged_host_dlls':{n:sha(game/n) for n in ['dxgi.dll','dinput8.dll']}}
(backup/'phase10-deployment.json').write_text(json.dumps(report,indent=2)+'\n')
(Path(__file__).resolve().parent/'deployment.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['modules','original']},indent=2),flush=True)
