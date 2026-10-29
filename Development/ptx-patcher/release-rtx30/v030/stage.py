from pathlib import Path
import json,hashlib,zipfile,shutil,datetime
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';stage=out/'.stage-v0.3.0';core=root/'nvngx_dlssnr_sm86_v31_pack5.dll';SHA='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for b in iter(lambda:s.read(8<<20),b''):h.update(b)
 return h.hexdigest()
assert sha(core)==SHA and core.stat().st_size==266414592;assert not stage.exists()
common=f'''DLSS5 RTX30 v0.3.0（2026-10-29）
PTX V3.1_pack5；31-block Small / Preset2 / Style1；15/15 O4原槽位，无扩节。
RTX3080 Laptop模型GPU median（非游戏帧率）：研发两轮进程median均值720p5.75ms /900p8.42ms /1080p11.35ms（repeat 11.12ms）；低温评估另一轮5.62/8.38/11.07ms。默认DVFS，不能跨轮作严格提速比较。
核心SHA256：{SHA}
相比v0.2.0：原生cp.async.mbarrier绑定、按需解码/寄存器池回收、Low/High K16和mapped直通、C32四核cap168、单对FP16x2→FP8x2核心13→9→5条SASS。
本版为非0-bit升级：对V2.9_fast测试PSNR61.738/60.821/59.645dB，maxabs0.004395/0.007813/0.008301，finite，天空0变号。不是对原生GPU/F32的绝对画质认证。
退出程序、备份后解压全部文件，不混装三包。包内SHA256SUMS.txt校验文件；修补NR无Authenticode签名，SHA完整性与NGX执行另验。
'''
profiles=[]
for label in ['OptiScaler-REFramework','OptiScaler','Magpie']:
 src=out/f'{label}-DLSS5-RTX30-0.2.0.zip';name=f'{label}-DLSS5-RTX30-0.3.0';dst=stage/name
 with zipfile.ZipFile(src) as z:
  assert z.testzip() is None
  for i in z.infolist():assert not Path(i.filename).is_absolute() and '..' not in Path(i.filename).parts
  z.extractall(dst)
 oldread=(dst/'README.txt').read_text(encoding='utf-8-sig');marker='Magpie：' if label=='Magpie' else 'OptiScaler：';note=oldread[oldread.index(marker):] if marker in oldread else ''
 oldchecks={f.relative_to(dst).as_posix():sha(f) for f in dst.rglob('*') if f.is_file()};shutil.copy2(core,dst/'nvngx_dlssnr.dll');(dst/'README.txt').write_text(common+note,encoding='utf-8-sig')
 (dst/'README.en.txt').write_text(f'''DLSS5 RTX30 v0.3.0 (2026-10-29)
PTX V3.1_pack5, 31-block Small / Preset2 / Style1; 15/15 O4 in original slots.
RTX3080 Laptop model-only GPU median: development rounds 5.75/8.42/11.35ms; separate cooler run 5.62/8.38/11.07ms. Not game FPS or cross-run paired speedups.
Core SHA256: {SHA}
Non-bit-exact upgrade; vs V2.9_fast PSNR 61.738/60.821/59.645dB on benchmark inputs.
Exit applications, back up and extract ALL package files; do not mix packages.
OptiScaler: F6 toggles NR, Insert opens menu. Default strength 1.0/1.0; optional OptiScaler-增强风格.ini uses1.5/1.1. Keep game-specific exposure settings.
Magpie: run as administrator, use windowed input and DLSS5-RTX30-PTX profile; Alt+Shift+A starts scaling. Native NR then DLSS_SR, not guaranteed end-to-end 60FPS.
Patched NR is unsigned. SHA integrity and NGX execution checked separately.
''')
 (dst/'DLSS5-RTX30-VERSION.txt').write_text(f'0.3.0\n{name}\nPTX V3.1_pack5 /31-block Small only\n')
 meta=json.loads((dst/'release.json').read_text());meta.update(name=name,version='0.3.0',date='2026-10-29',ptx_version='V3.1_pack5',ptx_sha256=SHA,gpu_median_ms={'720p':5.75,'900p':8.42,'1080p':11.35},gpu_median_ms_cool_run={'720p':5.62,'900p':8.38,'1080p':11.07},bit_exact=False,quality_reference='V2.9_fast',psnr_db=[61.7376742065,60.8212386367,59.6449653817]);(dst/'release.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n');(dst/'SHA256SUMS.txt').unlink()
 changed={'nvngx_dlssnr.dll','README.txt','README.en.txt','release.json','DLSS5-RTX30-VERSION.txt','SHA256SUMS.txt'}
 assert all(sha(dst/n)==h for n,h in oldchecks.items() if n not in changed)
 profiles.append({'label':label,'name':name,'stage':str(dst),'source_zip':str(src),'source_zip_sha256':sha(src),'preserved_files':{n:h for n,h in oldchecks.items() if n not in changed}});print('STAGED',name,flush=True)
(p/'deployment.json').write_text(json.dumps({'version':'0.3.0','NR_sha256':SHA,'profiles':profiles},indent=2,ensure_ascii=False)+'\n')
tools=root/'release-v030-tools';tools.mkdir(exist_ok=True)
for name in ['ffx_loader_smoke.exe','ffx_nr_smoke.exe']:shutil.copy2(root/'release-v020-tools'/name,tools/name)
