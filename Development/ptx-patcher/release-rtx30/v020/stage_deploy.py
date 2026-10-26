from pathlib import Path
import sys,json,hashlib,shutil,zipfile,datetime,re
p=Path(__file__).resolve().parent
def patch_ini(text,updates):
 result=[];section='';seen=set()
 for line in text.splitlines():
  match=re.match(r'\s*\[([^]]+)\]',line)
  if match:section=match[1]
  key=line.split('=',1)[0].strip() if '=' in line and not line.lstrip().startswith((';','#')) else None
  if (section,key) in updates:line=key+'='+updates[section,key];seen.add((section,key))
  result.append(line)
 assert seen==set(updates),set(updates)-seen
 return '\r\n'.join(result)+'\r\n'

ROOT=Path('/mnt/c/DLSS5-5090-dll');OUT=ROOT/'发布打包';STAGE=OUT/'.stage-v0.2.0';BACKUP=ROOT/'backups/20261026-v020';V21=ROOT/'nvngx_dlssnr_sm86_v21.dll';SHA='c7d4c8b6cb5369061b93ce389963209145bc68a5cdfc3c3f0d339a931be3f1ed';DXGI='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2';FWD='4f088f382171b3b3af4e2b34cb71b162788c947a55eeefc6e81e36206c59a0c9'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(V21)==SHA
assert not BACKUP.exists(),'Refuse to overwrite deployment backup';assert not STAGE.exists(),'Use existing stage rather than overwrite'
ONI=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content');SB=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64');OLDMAG=OUT/'Magpie-DLSS5-RTX30-0.1.0';NEWMAG=OUT/'Magpie-DLSS5-RTX30-0.2.0';ORIG=ROOT/'backups/Onimusha-ptx-0.1.0'
assert sha(ORIG/'dxgi.dll')==DXGI and sha(ORIG/'nvngx.dll_dlssnr.dll')==FWD
assert OLDMAG.is_dir() and not NEWMAG.exists();assert (ONI/'_storage_').is_dir()
packages=['OptiScaler-REFramework','OptiScaler','Magpie'];profiles=[]
def ini(data,strength='1.0',colour='1.0'):
 text=data.decode('utf-8-sig');return patch_ini(text,{('DlssNr','NrBackend'):'nvidia',('DlssNr','WhitePointSource'):'1',('DlssNr','Preset'):'2',('DlssNr','Style'):'1',('DlssNr','TransferStrength'):strength,('DlssNr','ColourStrength'):colour}).encode('utf-8-sig')
common='''DLSS5 RTX30 v0.2.0（2026-10-26）\n31-block Small / Preset2 / Style1；三个包统一原生PTX V2.1。\nRTX3080 Laptop模型GPU median：720p 6.66ms /900p 9.70ms /1080p 12.78ms；不是整机游戏帧率。\n偶奇K16原位拆解消除MMA操作数洗牌，FB00/03/04/05/06 maxnreg放宽255；15/15 O4、原槽位。\n核心DLL SHA256: '''+SHA+'''\n退出程序后备份同名文件，再解压全部文件；不要混装三个包。\n包内SHA256SUMS.txt校验每个文件；修补DLL不含NVIDIA Authenticode签名，SHA校验与NGX调用检查另行验证。\n'''
for label in packages:
 old=OUT/f'{label}-DLSS5-RTX30-0.1.0.zip';name=f'{label}-DLSS5-RTX30-0.2.0';dst=STAGE/name
 with zipfile.ZipFile(old) as z:
  assert z.testzip() is None
  for info in z.infolist():
   assert not Path(info.filename).is_absolute() and '..' not in Path(info.filename).parts
  z.extractall(dst)
 shutil.copy2(V21,dst/'nvngx_dlssnr.dll')
 if label!='Magpie':
  assert sha(dst/'dxgi.dll')==DXGI and sha(dst/'nvngx.dll_dlssnr.dll')==FWD
  original=(dst/'OptiScaler.ini').read_bytes();(dst/'OptiScaler.ini').write_bytes(ini(original));(dst/'OptiScaler-增强风格.ini').write_bytes(ini(original,'1.5','1.1'));(dst/'OptiScaler-效果增强.ini').unlink(missing_ok=True)
  note='''OptiScaler：F6切换NR，Insert打开菜单。默认TransferStrength=1.0 /ColourStrength=1.0，减小运动遮罩回退时与原图的强度反差。\n《剑星》转视角闪烁反馈的配置调整，不声称本轮已实玩验收。增强风格可复制OptiScaler-增强风格.ini为OptiScaler.ini（1.5/1.1）。\nWhitePointSource=1读取游戏曝光；鬼武者约512x与剑星约1x不要互抄。\n游戏可选DLSS或支持的FSR输入，输出DLSS SR；必须复制所有配套FFX DLL。\n'''
  note+=('REFramework专用：含dinput8.dll，适用鬼武者/生化9等RE Engine。\n' if label=='OptiScaler-REFramework' else '常规DX12包：不含dinput8.dll；适用剑星等游戏。\n')
 else:
  assert sha(dst/'Magpie.exe')=='b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea'
  note='''Magpie：以管理员运行，窗口模式，选择DLSS5-RTX30-PTX：原生DLSSNR Preset2/Style1 →DLSS_SR。\nAlt+Shift+A开始缩放；保留原生Preset2补丁，不需要ReShade或独立CUDA/HIP资产。\n60Hz捕获/显示可能出现同步台阶，模型GPU时间不是全链路帧率。\n'''
 (dst/'README.txt').write_text(common+note,encoding='utf-8-sig')
 (dst/'README.en.txt').write_text('DLSS5 RTX30 v0.2.0\nPTX V2.1,31-block Small /Preset2 /Style1,15/15 O4 in original slots.\nGPU model median 720p6.66ms /900p9.70ms /1080p12.78ms on RTX3080 Laptop.\nCore SHA256: '+SHA+'\nBack up and extract all files after exiting the application. Do not mix packages.\nStandard/REFramework defaults: TransferStrength=1.0,ColourStrength=1.0; optional OptiScaler-增强风格.ini uses1.5/1.1.\nMagpie uses native DLSSNR then DLSS_SR with Preset2 patched executable.\nPatched NR DLL is unsigned; SHA256 integrity and NGX execution are checked separately.\n',encoding='utf-8')
 (dst/'DLSS5-RTX30-VERSION.txt').write_text('0.2.0\n'+name+'\nPTX V2.1 /31-block Small only\n')
 (dst/'release.json').write_text(json.dumps({'name':name,'version':'0.2.0','route':'native-ptx' if label=='Magpie' else 'ptx','model':'0.5x Small /31 blocks','ptx_sha256':SHA,'gpu_median_ms':{'720p':6.66,'900p':9.70,'1080p':12.78},'default_strength':'1.0/1.0','optional_strength':'1.5/1.1'},indent=2)+'\n')
 (dst/'SHA256SUMS.txt').unlink(missing_ok=True);profiles.append({'label':label,'name':name,'stage':str(dst),'source_zip':str(old),'source_zip_sha256':sha(old)})
 print('STAGED',name,flush=True)
BACKUP.mkdir();records=[]
def backup_file(target,label):
 if not target.exists():records.append({'target':str(target),'old_sha256':None,'backup':None});return
 dst=BACKUP/label;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,dst);assert sha(dst)==sha(target);records.append({'target':str(target),'old_sha256':sha(target),'backup':str(dst)})
backup_file(ROOT/'nvngx_dlssnr_sm86_fast.dll','production/nvngx_dlssnr_sm86_fast.dll');backup_file(ROOT/'nvngx_dlssnr_sm86_fast.manifest.json','production/old.manifest.json')
for sub in ['', '_storage_']:
 d=ONI/sub
 for name in ['dxgi.dll','OptiScaler.ini','nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']:
  backup_file(d/name,'onimusha/'+(sub+'/' if sub else '')+name)
for name in ['nvngx_dlssnr.dll','OptiScaler.ini','OptiScaler-效果增强.ini','OptiScaler-增强风格.ini','README.txt','README.en.txt','release.json','DLSS5-RTX30-VERSION.txt','SHA256SUMS.txt']:backup_file(SB/name,'stellar/'+name)
for name in ['nvngx_dlssnr.dll','release.json','README.txt','README.en.txt','DLSS5-RTX30-VERSION.txt','SHA256SUMS.txt','config/config.json']:backup_file(OLDMAG/name,'magpie/'+name)
(BACKUP/'before.json').write_text(json.dumps(records,indent=2)+'\n')
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);tmp=dst.with_name(dst.name+'.v020-tmp');shutil.copy2(src,tmp);tmp.replace(dst);assert sha(src)==sha(dst)
copy(V21,ROOT/'nvngx_dlssnr_sm86_fast.dll');copy(V21.with_suffix('.manifest.json'),ROOT/'nvngx_dlssnr_sm86_fast.manifest.json')
removed=[]
for sub in ['', '_storage_']:
 d=ONI/sub;copy(ORIG/'dxgi.dll',d/'dxgi.dll');copy(ORIG/'OptiScaler.ini',d/'OptiScaler.ini');copy(ORIG/'nvngx.dll_dlssnr.dll',d/'nvngx.dll_dlssnr.dll');copy(V21,d/'nvngx_dlssnr.dll')
 for name in ['DLSS5-AMD','LmxxfNrRuntime.dll','dlss5-amd.addon64','shaders']:
  src=d/name
  if src.exists():
   dst=BACKUP/'route-a-removed'/('storage' if sub else 'root')/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(src),str(dst));removed.append({'from':str(src),'backup':str(dst)})
# Preserve game-specific settings while changing only the requested strengths/backend invariants.
old=(SB/'OptiScaler.ini').read_bytes();(SB/'OptiScaler-增强风格.ini').write_bytes(ini(old,'1.5','1.1'));(SB/'OptiScaler.ini').write_bytes(ini(old));copy(V21,SB/'nvngx_dlssnr.dll');(SB/'OptiScaler-效果增强.ini').unlink(missing_ok=True)
OLDMAG.rename(NEWMAG);copy(V21,NEWMAG/'nvngx_dlssnr.dll')
for label,dest in [('OptiScaler',SB),('Magpie',NEWMAG)]:
 stage=Path(next(x['stage'] for x in profiles if x['label']==label))
 for name in ['release.json','README.txt','README.en.txt','DLSS5-RTX30-VERSION.txt']:copy(stage/name,dest/name)
report={'version':'0.2.0','time':datetime.datetime.now().isoformat(),'NR_sha256':SHA,'original_dxgi_sha256':DXGI,'forwarder_sha256':FWD,'backup':str(BACKUP),'profiles':profiles,'backup_files':records,'route_a_removed':removed,'magpie_rename':{'from':str(OLDMAG),'to':str(NEWMAG)},'onimusha_storage_both_updated':True}
(p/'deployment.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');(BACKUP/'deployment.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n');print('DEPLOYED main fast /Onimusha root+storage /StellarBlade /Magpie',flush=True)
