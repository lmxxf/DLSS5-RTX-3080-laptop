from common import *
import shutil,zipfile,configparser
assert sha(CORE)==SHA and CORE.stat().st_size==266414592
proc=run([PS,'-NoProfile','-ExecutionPolicy','Bypass','-File',win(P/'processes.ps1')],tag='Windows process preflight');active=json.loads(proc['stdout']) if proc['stdout'].strip() else [];assert not active,active
assert not BACKUP.exists() and not STAGE.exists() and not TOOLS.exists();BACKUP.mkdir(parents=True);STAGE.mkdir();TOOLS.mkdir()
for name in ['ffx_loader_smoke.exe','ffx_nr_smoke.exe']:
 src=ROOT/'release-v020-tools'/name;assert src.is_file();shutil.copy2(src,TOOLS/name)
chain=read(P.parent/'v020/smoke-toolchain.json');assert all(sha(TOOLS/n)==h for n,h in chain['tools'].items())
oldpkgs={x['name']:x for x in read(P.parent/'v030/packages.json')};profiles=[]
from_sources={}
for label in ['OptiScaler-REFramework','OptiScaler','Magpie']:
 src=OUT/f'{label}-DLSS5-RTX30-0.3.0.zip';assert sha(src)==oldpkgs[src.name]['sha256'];dst=STAGE/f'{label}-DLSS5-RTX30-0.4.0'
 with zipfile.ZipFile(src) as z:
  assert z.testzip() is None
  for x in z.infolist():assert not Path(x.filename).is_absolute() and '..' not in Path(x.filename).parts and '\\' not in x.filename
  z.extractall(dst)
 checks={f.relative_to(dst).as_posix():sha(f) for f in dst.rglob('*') if f.is_file()};assert checks['nvngx_dlssnr.dll']==OLD
 profiles.append({'label':label,'name':dst.name,'stage':str(dst),'source_zip':str(src),'source_zip_sha256':sha(src),'preserved_files':{n:h for n,h in checks.items() if n not in META|{'nvngx_dlssnr.dll'}}});from_sources[label]=dst
oni=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content');sb=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64');sites=[{'label':'main-fast','base':str(ROOT),'file':'nvngx_dlssnr_sm86_fast.dll','profile':None},{'label':'onimusha','base':str(oni),'file':'nvngx_dlssnr.dll','profile':'OptiScaler-REFramework'},{'label':'onimusha-storage','base':str(oni/'_storage_'),'file':'nvngx_dlssnr.dll','profile':'OptiScaler-REFramework'},{'label':'stellar','base':str(sb),'file':'nvngx_dlssnr.dll','profile':'OptiScaler'},{'label':'magpie','base':str(OUT/'Magpie-DLSS5-RTX30-0.3.0'),'new_base':str(OUT/'Magpie-DLSS5-RTX30-0.4.0'),'file':'nvngx_dlssnr.dll','profile':'Magpie'}]
saved=[]
def backup(f,label):
 dest=BACKUP/label;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);saved.append({'path':str(f),'backup':str(dest),'sha256':sha(f)})
for s in sites:
 base=Path(s['base']);nr=base/s['file'];assert sha(nr)==OLD;s['old_NR_sha256']=sha(nr);support={}
 if s['profile']:
  pf=next(x for x in profiles if x['label']==s['profile'])
  for n in pf['preserved_files']:
   if (base/n).is_file():support[n]=sha(base/n)
  for n in ['dxgi.dll','dinput8.dll','nvngx.dll_dlssnr.dll','OptiScaler.ini','OptiScaler-增强风格.ini','Magpie.exe']:
   if (base/n).is_file():support[n]=sha(base/n)
 for n in META:
  if (base/n).is_file():backup(base/n,s['label']+'/'+n)
 s['preserved_files']=support
fastmeta=ROOT/'nvngx_dlssnr_sm86_fast.manifest.json'
if fastmeta.exists():backup(fastmeta,'main-fast/'+fastmeta.name)
shutil.copy2(ROOT/'nvngx_dlssnr_sm86_fast.dll',BACKUP/'nvngx_dlssnr-v0.3.0.dll');assert sha(BACKUP/'nvngx_dlssnr-v0.3.0.dll')==OLD
metapaths=[OUT/'SHA256SUMS.txt',OUT/'README.txt',OUT/'release-v0.3.0.json',ROOT/'backups/20261024-StellarBlade-full/manifest.json',OUT/'StellarBlade-install-manifest.json',ROOT/'StellarBlade-install-manifest.json']
for i,f in enumerate(metapaths):
 if f.exists():backup(f,f'other/{i}-{f.name}')
protected={str(f):sha(f) for f in [ROOT/'nvngx_dlssnr.dll',ROOT/'nvngx_dlssnr_sm86_v31_pack5.dll',ROOT/'nvngx_dlssnr_sm86_v38.dll',CORE]}
archives={str(f):sha(f) for version in ['v0.1.0','v0.2.0'] for f in (OUT/'archive'/version).rglob('*') if f.is_file()}
bench=read(P.parents[1]/'v40/timing-summary.json');timing={stage:{w:{k:q[k] for k in ['base_ms','candidate_ms','gain_percent']} for w,q in modes['joint_up_cfg_pack4_fb2356'].items()} for stage,modes in bench.items()}
common=f'''DLSS5 RTX30 v0.4.0 (2026-11-01) / PTX V4.0
31-block Small / Preset2 / Style1; 15/15 O4 original slots; 266414592 B.
模型GPU配对均值（非游戏FPS）：720p 5.61~5.66ms /900p 8.27~8.30ms /1080p 10.99~11.00ms；50 warmup/80 iter，默认DVFS。1080p两轮四进程median均值10.995000/10.986750ms，非逐帧上界。
核心SHA256：{SHA}
500处FB456正零折叠；34入口CFG稳定源UP-Pair（1288处，删除644拆分）；FB2356经验Pack4。38活跃核静态非NOP145461，PRMT18781，STL/LDL99/100。
相对V3.8两轮12/12方向胜出，所测三档27次末帧0bit；不代表未测输入全域等价。经验Pack4保留实证标签，旧版0.3.0保留回退。
退出程序并备份后解压全部文件，不混装三包。OptiScaler默认1.0/1.0，增强风格INI为1.5/1.1；保留游戏曝光设置。修补NR未签名，SHA完整性与NGX运行单独验证。
'''
manifest=read(P.parents[1]/'v40/candidates.json')['joint_up_cfg_pack4_fb2356']['manifest'];assert len(manifest)==15 and all(x[1]=='inline' for x in manifest)
for pf in profiles:
 dst=Path(pf['stage']);oldread=(dst/'README.txt').read_text(encoding='utf-8-sig');marker='Magpie：' if pf['label']=='Magpie' else 'OptiScaler：';tail=oldread[oldread.index(marker):] if marker in oldread else ''
 write(dst/'nvngx_dlssnr.manifest.json',manifest);shutil.copy2(CORE,dst/'nvngx_dlssnr.dll');(dst/'README.txt').write_text(common+tail,encoding='utf-8-sig');(dst/'README.en.txt').write_text(f'''DLSS5 RTX30 v0.4.0 / PTX V4.0 (2026-11-01)
31-block Small / Preset2 / Style1; 15/15 O4 original slots.
Core SHA256: {SHA}
500 positive-zero folds, 1288 stable-source UP conversions across 34 selected entries, and empirical Pack4 in FB02/03/05/06. Static non-NOP145461; PRMT18781; STL/LDL99/100.
Model-only paired process-median means: 5.61~5.66 /8.27~8.30 /10.99~11.00ms (720p/900p/1080p), default DVFS; not game FPS or a per-frame upper bound. Two promotion rounds beat V3.8 in12/12 directions;27 benchmark output checks were0bit; empirical Pack4 is not a universal input-domain guarantee.
Extract ALL files after exiting applications and backing up. Do not mix package variants.
OptiScaler: F6 toggles NR, Insert opens menu. Default strength1.0/1.0; optional OptiScaler-增强风格.ini1.5/1.1. Preserve game-specific exposure settings.
Magpie: windowed input, Administrator, DLSS5-RTX30-PTX profile, Alt+Shift+A; NR then DLSS_SR.
Patched NR is unsigned. Verify SHA and NGX execution separately. Keep0.3.0 for rollback.
''',encoding='utf-8-sig');(dst/'DLSS5-RTX30-VERSION.txt').write_text(f'0.4.0\n{pf["name"]}\nPTX V4.0 /31-block Small only\n');meta=read(dst/'release.json')
 for k in ['gpu_median_ms','gpu_median_ms_cool_run','quality_reference','psnr_db']:meta.pop(k,None)
 meta.update(name=pf['name'],version='0.4.0',date='2026-11-01',ptx_version='V4.0',ptx_sha256=SHA,bit_exact=False,quality_reference='V3.8',tested_output_bitdiff=0,tested_output_checks=27,empirical_pack4=True,paired_process_median_means=timing,metric_scope='model-only paired means, not game FPS or per-frame bound');write(dst/'release.json',meta);(dst/'SHA256SUMS.txt').unlink();assert all(sha(dst/n)==h for n,h in pf['preserved_files'].items())
write(P/'deployment.json',{'version':'0.4.0','NR_sha256':SHA,'source':str(CORE),'profiles':profiles,'sites':sites,'backup':str(BACKUP),'core_backup':str(BACKUP/'nvngx_dlssnr-v0.3.0.dll'),'saved_metadata':saved,'protected_inputs':protected,'historical_archives':archives,'manifest':manifest,'smoke_toolchain':chain['tools'],'timing_evidence':timing,'native_process_preflight':active});print('prepared3 stages;5 old cores verified;metadata+one old NR backed up;configuration bytes preserved')
