from pathlib import Path
import zipfile,json,hashlib,shutil,copy,struct,re
ROOT=Path('/mnt/c/DLSS5-5090-dll');OUT=ROOT/'发布打包';LIVE=OUT/'Magpie-DLSS5-RTX30-0.1.0';ZIP=OUT/'Magpie-DLSS5-RTX30-0.1.0.zip';BACK=ROOT/'backups/20261024-Magpie-0.1.0-fix';BACK.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
addon=(ROOT/'magpie-fix-test/release-addon.addon64').read_bytes()
sr=(ROOT/'magpie-fix-test/nvngx_dlss.dll').read_bytes()
assert sha(addon)=='88cd04c572af79aa8a51938b42cc86d325ee23e5a8d826cc81665368b3f3ae1f'
profile=[{'name':'FSR3\\FSR3_SR','scalingType':0,'scale':{'x':1.,'y':1.},'parameters':{'opticalFlowMethod':0.}}, {'name':'DLSS\\DLSS_SR','scalingType':1,'scale':{'x':1.,'y':1.},'parameters':{'opticalFlowMethod':0.}}]
def config(data):
 j=json.loads(data.decode('utf-8-sig'));j['scalingModes'][6]['name']='DLSS5-RTX30';j['scalingModes'][6]['effects']=profile;j['profiles'][0]['scalingMode']=6
 return json.dumps(j,ensure_ascii=False,indent=2).encode('utf-8')
readme='''DLSS5 RTX30 0.1.0 - Magpie NVIDIA 修复版

本包仍走CUDA sm_86独立引擎，只含31块Small外置权重（small/93文件），不是PTX/NGX NR直通路线。
默认效果链：FSR3 1x（720p->720p，作为CUDA重打光入口）-> NVIDIA DLSS_SR（放大到屏幕）。不再默认FSR4或XeSSFG。
已补齐nvngx_dlss.dll；它是原生DLSS超分库，不是71块旧版NR模型。
SDK实际对照：无此库时D3D11 SR创建复现bad0000b，加入后返回00000001。RTX3080 Laptop原生DLSS_SR初始化成功。

使用：退出旧Magpie，解压全部文件，用包内默认DLSS5-RTX30预设，在游戏720p窗口前台选择3秒后缩放，启动期间保持游戏前台。
F6切换神经重打光；F9模型切换禁用。F9不要切进已删除的旧模型档位。
不要再把第二级换回FSR4。若特定环境的DLSS_SR不可用，可把第二级改为空间FSR(EASU/RCAS)或Lanczos，保留第一级FSR3 1x；该备用链未在本机作为默认验收。
前后台切换会按Magpie自身逻辑结束全屏缩放；这不等于插件初始化失败。

验证：实际Magpie 1280x720窗口捕获，FSR3->DLSS_SR 3840x2160正常初始化、持续呈现。
ReShade Present计数确认会递增；Magpie插件改为有限启动等待，loader/provider双层hook成功并防止切换hook时误留旧context指针。
CUDA日志确认model=0.5 blocks=31，像素发生改变，连续数百帧神经处理，正常停止无设备移除。
这是程序窗口实测，不冒充已替用户验收《光环》画面。

DLSS5-AMD路径名为兼容名；内部两组各40个模块均为EM_CUDA sm_86。F6/热重载与单遍默认保持。
默认已移除temporal-history.txt旧实验标记；只用31块单帧路径。日志目录会自动创建，日志在DLSS5-AMD/logs/。
源码与GPU/窗口验证记录保存在工程Development/ptx-patcher/magpie-fix。此前frame.exe smoke只覆盖网络/编解码，不覆盖ReShade接管，不能替代本次完整窗口测试。
版本号0.1.0；上游AMD底包0.44只作来源说明。
'''.encode('utf-8-sig')
english=b'''DLSS5 RTX30 0.1.0 - Magpie NVIDIA fix\n\nDefault chain: FSR3 at 1x -> CUDA sm_86 Small NR -> native NVIDIA DLSS SR. FSR4 and XeSSFG are removed from the default preset.\nThe native nvngx_dlss.dll SR runtime is included. It resolves the reproduced D3D11 0xbad0000b creation failure. Only the 31-block Small external NR weights are retained.\nKeep the game window in the foreground during startup. F6 toggles NR. See README.txt for detailed setup, validation and diagnostic logs.\n'''

def rawcopy(src,dst,info):
 assert not info.flag_bits&9
 src.fp.seek(info.header_offset);header=src.fp.read(30);nl,el=struct.unpack_from('<HH',header,26);extra=src.fp.read(nl+el)
 n=copy.copy(info);n.header_offset=dst.fp.tell();dst._writecheck(n);dst._didModify=True;dst.fp.write(header+extra)
 left=info.compress_size
 while left:
  b=src.fp.read(min(left,1048576));assert b;dst.fp.write(b);left-=len(b)
 dst.filelist.append(n);dst.NameToInfo[n.filename]=n;dst.start_dir=dst.fp.tell()

shutil.copy2(ZIP,BACK/ZIP.name)
with zipfile.ZipFile(ZIP) as src:
 old_size=ZIP.stat().st_size;old_sha=sha(ZIP.read_bytes())
 meta=json.loads(src.read('release.json'));meta['magpie_fix']='NVIDIA SR runtime / bounded hook bootstrap / loader-provider context';meta['addon_sha256']=sha(addon);meta['dlss_sr_sha256']=sha(sr)
 updates={'dlss5-amd.addon64':addon,'nvngx_dlss.dll':sr,'config/config.json':config(src.read('config/config.json')),'README.txt':readme,'README.en.txt':english,'release.json':json.dumps(meta,indent=2).encode(),'DLSS5-AMD/logs/.keep':b'Diagnostic logs are created here.\n'}
 remove={'DLSS5-AMD/temporal-history.txt'}
 checks={n:d for d,n in (l.split('  ',1) for l in src.read('SHA256SUMS.txt').decode().splitlines()) if n not in remove}
 for n,b in updates.items():checks[n]=sha(b)
 updates['SHA256SUMS.txt']=''.join(f'{d}  {n}\n' for n,d in sorted(checks.items())).encode()
 temp=ZIP.with_suffix('.zip.tmp')
 with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as dst:
  for info in src.infolist():
   if info.filename in remove:continue
   if info.filename in updates:dst.writestr(info.filename,updates[info.filename])
   else:rawcopy(src,dst,info)
  for n,b in updates.items():
   if n not in src.namelist():dst.writestr(n,b)
 with zipfile.ZipFile(temp) as z:
  assert z.testzip() is None
  for n,b in updates.items():assert z.read(n)==b
  assert not any(n in z.namelist() for n in remove)
 temp.replace(ZIP)
# Back up all live changes before replacing them; leave user logs/cache untouched.
records=[]
for n,b in updates.items():
 p=LIVE/n;old=sha(p.read_bytes()) if p.exists() else None
 if p.exists():
  q=BACK/'original'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 records.append({'file':n,'old_sha256':old,'new_sha256':sha(b)})
for n in remove:
 p=LIVE/n
 if p.exists():q=BACK/'original'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);p.unlink()
for n,b in updates.items():
 p=LIVE/n;p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.install.tmp');temp.write_bytes(b);temp.replace(p);assert sha(p.read_bytes())==sha(b)
(BACK/'manifest.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
# Central binaries used by future builds are updated atomically too.
for name,b in [('dlss5-amd.addon64',addon),('nvngx_dlss.dll',sr)]:
 p=ROOT/name
 if p.exists():shutil.copy2(p,BACK/('central-'+name))
 tmp=p.with_suffix(p.suffix+'.update.tmp');tmp.write_bytes(b);tmp.replace(p)
new_sha=sha(ZIP.read_bytes());(OUT/(ZIP.name+'.sha256')).write_text(new_sha+'  '+ZIP.name+'\n')
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(OUT.glob('*.zip'))))
summary={'old_sha256':old_sha,'sha256':new_sha,'old_size':old_size,'size':ZIP.stat().st_size,'addon_sha256':sha(addon),'sr_sha256':sha(sr),'backup':str(BACK)}
Path(__file__).with_name('deployment.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
