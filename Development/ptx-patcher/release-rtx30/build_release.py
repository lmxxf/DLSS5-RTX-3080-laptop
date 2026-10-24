from pathlib import Path
import re,zipfile,hashlib,shutil,json,struct
BASE=Path('/mnt/c/DLSS5-5090-dll/amd的dlss5-0.44的打包')
OUT=Path('/mnt/c/DLSS5-5090-dll/发布打包')
STAGE=OUT/'.stage'
ROOT=BASE.parent
MODULES=Path('/home/lmxxf/work/dlss5-assets/native-game-tiled-assets/HIP/gfx1201')
FAST=ROOT/'nvngx_dlssnr_sm86_fast.dll'
SHA='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(FAST)==SHA

def patch_ini(text,updates,drop=()):
 lines=text.splitlines();section='';seen=set();result=[]
 for line in lines:
  m=re.match(r'\s*\[([^]]+)\]',line)
  if m:section=m[1]
  key=line.split('=',1)[0].strip() if '=' in line and not line.lstrip().startswith((';','#')) else None
  if key and (section,key) in drop:continue
  if key and (section,key) in updates:
   line=key+'='+updates[(section,key)];seen.add((section,key))
  result.append(line)
 # Add missing keys inside existing sections, or create new sections.
 for sec in dict.fromkeys(s for s,k in updates):
  missing=[k+'='+v for (s,k),v in updates.items() if s==sec and (s,k) not in seen]
  if not missing:continue
  at=next((i for i,l in enumerate(result) if l.strip()=='['+sec+']'),None)
  if at is None:result+=['','['+sec+']']+missing
  else:result[at+1:at+1]=missing
 return '\r\n'.join(result)+'\r\n'

def patch_flags(text,updates):
 for key,value in updates.items():
  text,n=re.subn(r'(?m)^'+re.escape(key)+r'=.*$',key+'='+value,text)
  if not n:text+='\n'+key+'='+value+'\n'
 return text

NR={'Enabled':'true','RunBeforeSR':'true','NrBackend':'nvidia','Preset':'2','Style':'1','Intensity':'1.0','LocalStructure':'1.0','LocalTone':'1.0','WorkingScale':'1.0','TransferStrength':'1.0','ColourStrength':'1.0','WhitePointSource':'1','WhitePointTrim':'1.0','Passes':'1','MaxRatio':'2.0','ToggleKey':'117'}
UPDATES={('DlssNr',k):v for k,v in NR.items()}
UPDATES.update({('Upscalers','Dx12Upscaler'):'dlss',('Inputs','EnableFfxInputs'):'true',('Inputs','UseFfxInputs'):'true',('Inputs','EnableFsr2Inputs'):'true',('Inputs','UseFsr2Inputs'):'true',('Inputs','EnableFsr3Inputs'):'true',('Inputs','UseFsr3Inputs'):'true',('Inputs','EnableDlssInputs'):'true',('Inputs','EnableHotSwapping'):'false',('Plugins','LoadReshade'):'false',('Spoofing','Dxgi'):'false',('FrameGen','FGInput'):'nofg',('FrameGen','FGOutput'):'nofg',('Menu','ShowFps'):'true'})

def extract(src,dst,route):
 if dst.exists():shutil.rmtree(dst)
 dst.mkdir(parents=True)
 removed=[]
 with zipfile.ZipFile(src) as z:
  for info in z.infolist():
   n=info.filename.replace('\\','/');parts=Path(n).parts
   assert not n.startswith('/') and '..' not in parts
   if info.is_dir():continue
   skip=False
   if route=='cuda':
    if n.startswith('DLSS5-AMD/native-game-tiled-assets/') and n.count('/')==2:
     name=n.rsplit('/',1)[1]
     skip=bool(re.match(r'block.*\.(f16|f32)$',name) or re.match(r'(decoder39-weights|head-matrix)\.(f16|f32)$',name) or re.match(r'post70-.*\.(f16|f32)$',name))
   else:
    skip=n.startswith(('DLSS5-AMD/','shaders/')) or n in ('LmxxfNrRuntime.dll','ReShade64.dll','ReShade.ini','dlss5-amd.addon64')
   if route=='native-ptx' and n in ('dxgi.dll','dlss5-amd.addon64','ReShade.ini','ReShadePreset.ini'):skip=True
   if skip:removed.append(n);continue
   p=dst/n;p.parent.mkdir(parents=True,exist_ok=True)
   with z.open(info) as r,p.open('wb') as w:shutil.copyfileobj(r,w)
 return removed

def stage():
 OUT.mkdir(exist_ok=True)
 profiles=[('Magpie','Magpie-DLSS5-AMD-0.44.zip','Magpie-DLSS5-RTX30-0.1.0','native-ptx'),('REFramework','OptiScaler-REFramework-DLSS5-AMD-0.44.zip','OptiScaler-REFramework-DLSS5-RTX30-0.1.0','ptx'),('OptiScaler','OptiScaler-DLSS5-AMD-0.44.zip','OptiScaler-DLSS5-RTX30-0.1.0','ptx')]
 manifest=[]
 for label,source,name,route in profiles:
  dst=STAGE/name;removed=extract(BASE/source,dst,route)
  if route=='native-ptx':
   import sys
   sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'magpie-native'))
   from patch_preset2 import patch
   patched,patch_manifest=patch((dst/'Magpie.exe').read_bytes());(dst/'Magpie.exe').write_bytes(patched)
   (dst/'preset2-patch.json').write_text(json.dumps(patch_manifest,indent=2))
   shutil.copy2(FAST,dst/'nvngx_dlssnr.dll');shutil.copy2(ROOT/'nvngx_dlss.dll',dst/'nvngx_dlss.dll')
   profile=json.loads((Path(__file__).resolve().parents[1]/'magpie-native/native-profile.json').read_text())
   cfg=dst/'config/config.json';j=json.loads(cfg.read_text(encoding='utf-8-sig'));j['scalingModes'][6]=profile;j['profiles'][0]['scalingMode']=6;j['autoCheckForUpdates']=False;cfg.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
   shutil.copy2(Path(__file__).resolve().parents[1]/'magpie-native/preset2-patch.json',dst/'preset2-patch.json')
  elif route=='cuda':
   shutil.copy2(ROOT/'dlss5-amd.addon64',dst/'dlss5-amd.addon64')
   shutil.copy2(ROOT/'nvngx_dlss.dll',dst/'nvngx_dlss.dll')
   cfg=dst/'config/config.json';j=json.loads(cfg.read_text(encoding='utf-8-sig'))
   j['scalingModes'][6]['name']='DLSS5-RTX30'
   j['scalingModes'][6]['effects']=[{'name':'FSR3\\FSR3_SR','scalingType':0,'scale':{'x':1.,'y':1.},'parameters':{'opticalFlowMethod':0.}}, {'name':'DLSS\\DLSS_SR','scalingType':1,'scale':{'x':1.,'y':1.},'parameters':{'opticalFlowMethod':0.}}]
   j['profiles'][0]['scalingMode']=6;cfg.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
   (dst/'DLSS5-AMD/temporal-history.txt').unlink(missing_ok=True)
   (dst/'DLSS5-AMD/logs').mkdir(exist_ok=True);(dst/'DLSS5-AMD/logs/.keep').write_text('Diagnostic logs are created here.\n')

   assets=dst/'DLSS5-AMD/native-game-tiled-assets'
   fs=sorted(MODULES.glob('*.hsaco'));assert len(fs)==40
   assert all(struct.unpack_from('<H',p.read_bytes(),18)[0]==190 for p in fs)
   for arch in ['gfx1200','gfx1201']:
    for p in fs:shutil.copy2(p,assets/'HIP'/arch/p.name)
   flags=dst/'DLSS5-AMD/default-config.txt'
   flags.write_text(patch_flags(flags.read_text(encoding='utf-8-sig'),{'DLSS5_MULTI_PASS':'0.5','DLSS5_MULTI_PASS_HOTKEY':'0','DLSS5_TEMPORAL_MODE':'0','DLSS5_FAST_HISTORY':'0','DLSS5_STYLE':'1','DLSS5_CODEC_SRGB':'1','DLSS5_HOT_RELOAD':'1'}),encoding='utf-8')
   for config in (dst/'DLSS5-AMD').glob('*config.txt'):
    if config!=flags:config.write_text(patch_flags(config.read_text(encoding='utf-8-sig'),{'DLSS5_MULTI_PASS':'0.5','DLSS5_MULTI_PASS_HOTKEY':'0','DLSS5_TEMPORAL_MODE':'0','DLSS5_FAST_HISTORY':'0'}),encoding='utf-8')
   small=list((assets/'small').glob('*.f16'))+list((assets/'small').glob('*.f32'));assert len(small)==93
   for arch in ['gfx1200','gfx1201']:
    d=assets/'HIP'/arch;(d/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(d.glob('*.hsaco'))))
   d=assets/'HIP';(d/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(d).as_posix()}\n' for p in sorted(d.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
  else:
   shutil.copy2('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/dxgi.dll',dst/'dxgi.dll');assert (dst/'dxgi.dll').stat().st_size==26213888
   shutil.copy2('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content/nvngx.dll_dlssnr.dll',dst/'nvngx.dll_dlssnr.dll')
   shutil.copy2(FAST,dst/'nvngx_dlssnr.dll')
   p=dst/'OptiScaler.ini';p.write_bytes(patch_ini(p.read_text(encoding='utf-8-sig'),UPDATES,drop=[('DlssNr','LmxxfDiagnostic'),('DlssNr','AmdEveryFrame')]).encode('utf-8-sig'))
   strong=patch_ini(p.read_text(encoding='utf-8-sig'),{('DlssNr','TransferStrength'):'1.5',('DlssNr','ColourStrength'):'1.1'})
   (dst/'OptiScaler-效果增强.ini').write_bytes(strong.encode('utf-8-sig'))
   if label=='OptiScaler':
    shutil.copy2(dst/'OptiScaler.ini',dst/'OptiScaler-原始平衡.ini')
    (dst/'OptiScaler.ini').write_bytes(strong.encode('utf-8-sig'))
    assert not (dst/'dinput8.dll').exists()
    # Full support files remain from this base, including the actual FFX loader.
    for f in ['amd_fidelityfx_dx12.dll','amd_fidelityfx_upscaler_dx12.dll','fakenvapi.dll','libxess.dll','D3D12_Optiscaler/D3D12Core.dll']:assert (dst/f).is_file(),f
  for old in ['README.en.txt','SHA256SUMS.txt']:
   (dst/old).unlink(missing_ok=True)
  (dst/'release.json').write_text(json.dumps({'name':name,'route':route,'model':'0.5x Small / 31 blocks only','version':'0.1.0','ptx_sha256':SHA if route in ('ptx','native-ptx') else None},indent=2))
  (dst/'DLSS5-AMD-VERSION.txt').unlink(missing_ok=True)
  (dst/'DLSS5-RTX30-VERSION.txt').write_text('0.1.0\n'+name+'\n31-block Small only\n')
  manifest.append({'name':name,'path':str(dst),'route':route,'removed':removed})
  print('STAGED',name,'removed',len(removed),'files',sum(p.is_file() for p in dst.rglob('*')),flush=True)
 (OUT/'staging-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
 return manifest
if __name__=='__main__':stage()
