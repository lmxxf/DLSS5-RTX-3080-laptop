from pathlib import Path
import shutil,hashlib,json,zipfile,copy,struct
ROOT=Path('/mnt/c/DLSS5-5090-dll');OUT=ROOT/'发布打包';LIVE=OUT/'Magpie-DLSS5-RTX30-0.1.0';TEST=ROOT/'magpie-native-test';ZIP=OUT/'Magpie-DLSS5-RTX30-0.1.0.zip';BACK=ROOT/'backups/20261024-Magpie-native-release';BACK.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
expected={'Magpie.exe':'b6f883f9fff78dd546b292ff6ef2d5444d1f931c8e73f96ad17622732d93b3ea','nvngx_dlssnr.dll':'3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a','nvngx_dlss.dll':'83de996b1589957d6bfb3df77e2f2ba7821f1014c73cfc5f8315241a0e4d3253'}
updates={n:(TEST/n).read_bytes() for n in expected}
for n,d in updates.items():assert sha(d)==expected[n],n
# Preserve the user's other profiles/window settings, replacing only the default effect group.
j=json.loads((LIVE/'config/config.json').read_text(encoding='utf-8-sig'));validated=json.loads((TEST/'config/config.json').read_text(encoding='utf-8-sig'))
j['scalingModes'][6]=validated['scalingModes'][6];j['profiles'][0]['scalingMode']=6;j['autoCheckForUpdates']=False
updates['config/config.json']=json.dumps(j,ensure_ascii=False,indent=2).encode('utf-8')
updates['preset2-patch.json']=(TEST/'preset2-patch.json').read_bytes()
readme='''DLSS5 RTX30 0.1.0 - Magpie 原生 PTX 正式包

直接运行本目录Magpie.exe，默认预设DLSS5-RTX30-PTX：
原生DLSSNR（Preset2、Style1、31块Small）-> NVIDIA原生DLSS_SR。
720p窗口捕获后由NR同尺寸重打光，再由DLSS_SR放大到屏幕。
无ReShade dxgi.dll、无dlss5-amd.addon64、无DLSS5-AMD外置权重目录。
不要把旧包的ReShade/add-on/权重目录混拷回来。

Magpie.exe已做最小Preset2补丁：原后端写死Preset0，JSON不能改变。补丁只改Preset Set调用及对应日志，前后SHA/地址见preset2-patch.json。
nvngx_dlssnr.dll为已验证的15/15 O4修复版，SHA256 3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a。
nvngx_dlss.dll为原生SR运行库，不是旧71块NR模型。不要用其它原版Magpie.exe覆盖，否则会丢失Preset2固定。
自动更新关闭，以免后台更新覆盖此已核验EXE。

使用：以720p游戏窗口开始，保持前台，选择3秒后缩放；切换任务会按Magpie逻辑结束全屏缩放。
本路线不再有add-on的F6开关，比较请用Magpie自带效果/对比工具。
日志在logs/magpie.log，应出现Feature18、preset=fixed-2、style1、signed-snippet及evaluateGPU计时。

实测：同一3080 Laptop，720p动画窗口到4K，Feature18连续960次成功、0失败，NR GPU窗口均值15.868~16.199ms。
后级SR和同步也有成本，publication fence约21.1~21.5ms，动画窗口评估节奏约36FPS。
不能把1/16ms直接当成整机实际FPS，也不冒充已经验收光环40+FPS。
仅默认使用31块Small；外置71块旧模型和独立CUDA引擎不在本包。

本目录与正式ZIP均为原生路线B。替换前文件/ZIP和回退说明位于：
C:\\DLSS5-5090-dll\\backups\\20261024-Magpie-native-release
所有文件SHA256见SHA256SUMS.txt。
'''
updates['README.txt']=readme.encode('utf-8-sig')
updates['README.en.txt']=b'''Magpie DLSS5 RTX30 0.1.0 - native PTX release\n\nDefault: native Feature 18 NR (preset 2/style 1) -> native NVIDIA DLSS SR.\nNo ReShade, CUDA add-on or external DLSS5-AMD weights are required. Do not mix old package files back in.\nMagpie.exe has a hash-guarded minimal patch fixing its hard-coded NR preset to 2; see preset2-patch.json. Automatic updates are disabled.\nThe NR DLL is the validated 15/15 O4 Ampere build. 720p NR GPU time was about 16 ms; this is not a guarantee of whole-game FPS.\nUse Magpie's own comparison controls; the old add-on F6 toggle is gone. See README.txt for timing limits and rollback notes.\n'''
meta=json.loads((LIVE/'release.json').read_text());meta.update({'route':'native-ptx','preset':2,'style':1,'model':'31-block Small / preset 2','magpie_exe_sha256':expected['Magpie.exe'],'nr_dll_sha256':expected['nvngx_dlssnr.dll'],'dlss_sr_sha256':expected['nvngx_dlss.dll']})
for k in ['addon_sha256','magpie_fix']:meta.pop(k,None)
meta['validation']='720p capture -> native NR -> 4K DLSS SR; 960 success / 0 failures'
updates['release.json']=json.dumps(meta,indent=2).encode()
updates['DLSS5-RTX30-VERSION.txt']=b'0.1.0\nMagpie-DLSS5-RTX30-0.1.0\nnative PTX / preset 2 / 31-block Small\n'
removed_prefix=('DLSS5-AMD/','shaders/')
removed_names={'dxgi.dll','dlss5-amd.addon64','ReShade.ini','ReShadePreset.ini'}
old_sha=sha(ZIP.read_bytes());old_size=ZIP.stat().st_size
shutil.copy2(ZIP,BACK/ZIP.name)
records=[]
for n,data in updates.items():
 p=LIVE/n;old=sha(p.read_bytes()) if p.exists() else None
 if p.exists():q=BACK/'original'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 records.append({'file':n,'old_sha256':old,'new_sha256':sha(data)})
# Preserve removed live files, including runtime-modified ReShade settings.
for n in removed_names:
 p=LIVE/n
 if p.exists():q=BACK/'original'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
with zipfile.ZipFile(ZIP) as src:
 keep=[n for n in src.namelist() if not n.startswith(removed_prefix) and n not in removed_names]
 checks={n:d for d,n in (l.split('  ',1) for l in src.read('SHA256SUMS.txt').decode().splitlines()) if n in keep}
 for n,d in updates.items():checks[n]=sha(d)
 updates['SHA256SUMS.txt']=''.join(f'{d}  {n}\n' for n,d in sorted(checks.items()) if n!='SHA256SUMS.txt').encode()
 temp=ZIP.with_suffix('.zip.tmp')
 with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
  for info in src.infolist():
   n=info.filename
   if n not in keep:continue
   if n in updates:dst.writestr(n,updates[n]);continue
   assert not info.flag_bits&9
   src.fp.seek(info.header_offset);header=src.fp.read(30);nl,el=struct.unpack_from('<HH',header,26);extra=src.fp.read(nl+el)
   clone=copy.copy(info);clone.header_offset=dst.fp.tell();dst._writecheck(clone);dst._didModify=True;dst.fp.write(header+extra)
   left=info.compress_size
   while left:
    b=src.fp.read(min(left,1048576));assert b;dst.fp.write(b);left-=len(b)
   dst.filelist.append(clone);dst.NameToInfo[n]=clone;dst.start_dir=dst.fp.tell()
  for n,d in updates.items():
   if n not in keep:dst.writestr(n,d)
 with zipfile.ZipFile(temp) as z:
  assert z.testzip() is None
  for n,d in updates.items():assert z.read(n)==d
  assert not any(n.startswith(removed_prefix) or n in removed_names for n in z.namelist())
 temp.replace(ZIP)
# Install verified files atomically into the real launch directory.
for n,data in updates.items():
 p=LIVE/n;p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.install.tmp');tmp.write_bytes(data);tmp.replace(p);assert sha(p.read_bytes())==sha(data)
for n in removed_names:(LIVE/n).unlink(missing_ok=True)
for n in ['DLSS5-AMD','shaders']:
 p=LIVE/n
 if p.exists():shutil.rmtree(p)
(BACK/'manifest.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
new_sha=sha(ZIP.read_bytes());(OUT/(ZIP.name+'.sha256')).write_text(new_sha+'  '+ZIP.name+'\n')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(OUT.glob('*.zip'))))
summary={'old_sha256':old_sha,'sha256':new_sha,'old_size':old_size,'size':ZIP.stat().st_size,'files':expected,'backup':str(BACK)}
Path(__file__).with_name('native-release.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
