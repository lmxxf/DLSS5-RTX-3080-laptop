from pathlib import Path
import hashlib,zipfile,json,shutil,sys
sys.path.insert(0,str(Path(__file__).parent))
from build_release import OUT,STAGE,sha,SHA

COMMON='''DLSS5 RTX 30 系 0.1.0（2026-10-24）
仅使用31块0.5x Small新版模型。RTX 3080 Laptop / sm_86实测；其它RTX30型号未逐卡测试。
三个包不要混装：Magpie原生Feature18、另外两个OptiScaler包均使用原版PTX改写、15/15 O4。
先退出游戏、备份同名文件，再把包内全部文件解压到真正游戏exe所在目录。
F6切换NR，Insert打开OptiScaler菜单（Magpie包沿用其原界面）。
未实测内容不作为保证：游戏内观感、所有游戏的FSR接管、各RTX30型号兼容性需按实际游戏验收。
'''
PTX='''
【PTX路线】
包含26,213,888字节的新版dxgi.dll、NR转发桥、修复后的nvngx_dlssnr.dll及完整原包辅助DLL。
NR DLL SHA256: 3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a
原slot容纳15/15 O4；过滤多定义mapped，已修复3080 Laptop天空红绿横带。
不含AMD独立引擎、DLSS5-AMD资产目录或71块旧模型外置权重；Preset固定2，Style=1，单遍。
不要复制原版71块模型310.8 DLL进来；不要把Preset改为旧模型档位。

【游戏选DLSS或FSR】
Dx12Upscaler=dlss：这是输出后端，不等于输入只能选DLSS。
EnableFfxInputs=true、UseFfxInputs=true，FSR2/3输入开启，EnableHotSwapping=false，固定转到DLSS输出。
包内amd_fidelityfx_dx12.dll是26KB loader，必须与amd_fidelityfx_upscaler_dx12.dll等配套一起复制，不能只拷4个文件。
游戏原生nvngx_dlss.dll及NVIDIA驱动NGX也必须可用；包不覆盖游戏插件目录的原生DLSS SR库。
Windows FFX API smoke已验证：FFX输入->NGX/DLSS->NR实际分发，日志出现FFX input、primary feature ready、composition，输出无NaN/Inf。
这不是所有游戏内FSR实现的通用兼容保证；选择后查看OptiScaler.log是否出现FFX input和running before SR。
4K推荐先在游戏内选Quality；完整FFX查询实测Quality=2560x1440，Balanced=2258x1270，Performance=1920x1080，Ultra Performance=1280x720。
低内部渲染尺寸本来就会丢细节。NR重打光不等于恢复所有720p细节；不要把“4K输出”当“4K渲染”。

【曝光与效果】
WhitePointSource=1、WhitePointTrim=1，由游戏配对的pre-exposure / exposure决定白点。
《剑星》配对白点约1x，《鬼武者》约520x；数字是尺度，不是效果强度，不能互抄。
旧0.44 add-on编码对RGB各通道做肩部压缩；本包新版宿主对亮度做SoftKnee并保色相，另有不同的OkLab近灰保护、色域处理和2x亮度护栏。
因此旧版与本版不能只凭同样Style=1就视为完全相同的视觉管线，也不能把差别一概归为曝光错误。
增强配置只改TransferStrength/ColourStrength，不调假曝光，不增加模型遍数；具体游戏观感需实测。
'''
A='''
【Magpie / CUDA独立引擎】
NVIDIA修复：默认FSR3 1x -> DLSS_SR，补齐nvngx_dlss.dll；不用FSR4/XeSSFG默认链，已通过完整720p捕获与31块连续600帧验证。
Magpie没有游戏NGX接口，因此本包不走PTX直通，使用sm_86版dlss5-amd.addon64及两套各40个CUDA模块。
gfx1200/gfx1201是兼容目录名，文件本体是EM_CUDA/sm_86，不是AMD机器码。
保留small/全部93个权重，以及noise.f32等公共资源和原有shader。
已经删除根目录71块模型的block*、decoder39/head-matrix/post70专属权重。
默认DLSS5_MULTI_PASS=0.5，F9模型档位切换禁用，避免切进已删除的71块模型。
历史/时序实验默认关闭；本包不支持需要另一模型history-head的跨模型历史路径。
DLSS5_CODEC_SRGB=1：Magpie输入是已经显示编码的桌面画面，不再重复HDR编码。
使用：打开Magpie，沿用本包原有DLSSNR效果/捕获配置，先从720p或900p窗口测试再放大。
Windows frame.exe已用本包裁剪后资产、sm_86模块跑通31块Small：3帧有限、输出非黑、首末相同，无旧权重依赖。
该smoke验证的是初始化/推理/编解码，不等同于已验收所有Magpie窗口捕获场景。
原包中上游说明和源码仅供追溯；路线、型号、模型范围以本README为准。
'''

profiles=json.loads((OUT/'staging-manifest.json').read_text())
for m in profiles:
 d=Path(m['path']);name=m['name']
 if m['route']=='native-ptx':readme=(Path(__file__).resolve().parents[1]/'magpie-native/release-README.txt').read_text(encoding='utf-8-sig')
 elif m['route']=='cuda':readme=COMMON+A
 elif 'REFramework' in name:
  readme=COMMON+PTX+'''\n【REFramework专用】\n适用于《鬼武者》《生化9》等RE Engine，保留dinput8.dll，默认细节/色彩均1.0，与已实测《鬼武者》一致。\n可将OptiScaler-效果增强.ini复制为OptiScaler.ini试1.5/1.1增强；仍为31块单遍。\n此包不要用于《剑星》等普通UE/DX12游戏；普通游戏请用不含dinput8.dll的常规包。\n'''
 else:
  readme=COMMON+PTX+'''\n【常规DX12 / 剑星】\n不含dinput8.dll、ReShade64.dll或dlss5-amd.addon64。\n默认细节1.5、色彩1.1，保留单遍/Style1/游戏曝光；已通过同配置FFX->NR smoke。\n如希望回到原始1.0/1.0，退出游戏后把OptiScaler-原始平衡.ini复制为OptiScaler.ini。\n先在同一固定场景用F6比较，Quality/Performance档位应保持不变。\n原《剑星》amd_fidelityfx_dx12.dll必须先备份，本包将它替换为配套loader。\n'''
 (d/'README.txt').write_text(readme,encoding='utf-8-sig')
 (d/'README.en.txt').write_text(f'DLSS5 RTX 30 Series - Project Release 0.1.0\nPackage: {name}\nRoute: {m["route"]}\nOnly the 31-block Small model is enabled.\nClose the game/application and back up existing files before extracting all files. Do not mix the three packages.\nFor OptiScaler, extract beside the actual game executable. F6 toggles NR. The standard package includes complete FFX support libraries.\nMagpie uses the CUDA sm_86 independent engine. Legacy model switching is disabled.\nSee README.txt for detailed settings and validation scope.\n',encoding='utf-8')
 for n in ['README-Experimental.txt','RELEASE-NOTES.md']:(d/n).unlink(missing_ok=True)
 marker=d/'!! README_EXTRACT ALL FILES TO GAME FOLDER !!.txt'
 if marker.exists():marker.write_text('请先阅读README.txt，备份同名文件后解压全部文件。不能只拷4个DLL。\n',encoding='utf-8-sig')
 # Smoke-only tools and the game's SR DLL are never shipped.
 for n in ['ffx_nr_smoke.exe','ffx_loader_smoke.exe','OptiScaler.log']:(d/n).unlink(missing_ok=True)
 if m['route']=='ptx':(d/'nvngx_dlss.dll').unlink(missing_ok=True)
 if m['route']=='native-ptx':shutil.copy2(Path(__file__).resolve().parents[1]/'magpie-native/release-README.en.txt',d/'README.en.txt')
 (d/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(d).as_posix()}\n' for p in sorted(d.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'),encoding='utf-8')
 # Verify every emitted per-file checksum before archiving.
 for line in (d/'SHA256SUMS.txt').read_text().splitlines():
  digest,rel=line.split('  ',1);assert sha(d/rel)==digest
 path=OUT/(name+'.zip');tmp=path.with_suffix('.zip.tmp')
 with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in sorted(d.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(d).as_posix())
 tmp.replace(path)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  names=z.namelist()
  if m['route'] in ('ptx','native-ptx'):
   assert not any(n.startswith('DLSS5-AMD/') or n.endswith('LmxxfNrRuntime.dll') for n in names)
   assert hashlib.sha256(z.read('nvngx_dlssnr.dll')).hexdigest()==SHA
  else:
   weights=[n for n in names if '/small/' in n and n.endswith(('.f16','.f32'))];assert len(weights)==93
   assert len([n for n in names if '/gfx1201/' in n and n.endswith('.hsaco')])==40
   assert len([n for n in names if '/gfx1200/' in n and n.endswith('.hsaco')])==40
 digest=sha(path);(OUT/(path.name+'.sha256')).write_text(digest+'  '+path.name+'\n')
 print('PACKAGED',path.name,path.stat().st_size,digest,flush=True)
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(OUT.glob('*.zip'))))
print('All three ZIPs verified',flush=True)
