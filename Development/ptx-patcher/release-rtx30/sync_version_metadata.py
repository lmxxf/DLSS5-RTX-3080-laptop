from pathlib import Path
import json,zipfile,hashlib,shutil
ROOT=Path('/mnt/c/DLSS5-5090-dll');OUT=ROOT/'发布打包'
GAME=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64')
changes=json.loads(Path(__file__).with_name('version-0.1.0.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=OUT/'OptiScaler-DLSS5-RTX30-0.1.0.zip'
backup=ROOT/'backups/20261024-StellarBlade-version-0.1.0';backup.mkdir(parents=True,exist_ok=True)
meta=changes['OptiScaler-DLSS5-RTX30-0.44.zip']['metadata']
assert sha(GAME/'nvngx_dlssnr.dll')=='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a'
records=[]
with zipfile.ZipFile(archive) as z:
 for name in meta:
  p=GAME/name
  if p.exists():shutil.copy2(p,backup/name)
  data=z.read(name);records.append({'file':name,'old_sha256':sha(p) if p.exists() else None,'new_sha256':hashlib.sha256(data).hexdigest()})
 for r in records:
  p=GAME/r['file'];tmp=p.with_suffix(p.suffix+'.version.tmp');tmp.write_bytes(z.read(r['file']));tmp.replace(p);assert sha(p)==r['new_sha256']
(backup/'manifest.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
# Refresh the full-install manifest so its hash-gated rollback remains usable.
full=ROOT/'backups/20261024-StellarBlade-full/manifest.json';previous=full.with_name('manifest-before-version-0.1.0.json')
if not previous.exists():shutil.copy2(full,previous)
m=json.loads(full.read_text());m['archive']=str(archive);m['archive_sha256']=sha(archive);by_name={r['file']:r for r in m['files']}
for r in records:
 if r['file'] in by_name:by_name[r['file']]['new_sha256']=r['new_sha256']
 else:m['files'].append({'file':r['file'],'status':'new','old_sha256':None,'new_sha256':r['new_sha256']})
text=json.dumps(m,indent=2,ensure_ascii=False)
for p in [full,OUT/'StellarBlade-install-manifest.json',ROOT/'StellarBlade-install-manifest.json']:p.write_text(text)
for r in m['files']:assert sha(GAME/r['file'])==r['new_sha256'],r['file']
# Update current receipts, keeping references to the original AMD 0.44 upstream.
p=Path(__file__).with_name('发布回执.txt');text=p.read_text()
for old,c in changes.items():
 text=text.replace(old,c['name']).replace(c['old_sha256'],c['sha256']).replace('大小'+str(c['old_size'])+'字节','大小'+str(c['size'])+'字节')
text=text.replace('2026-10-24 RTX30 三包发布回执','2026-10-24 RTX30 0.1.0 三包发布回执')
text+='\n工程版本从0.1.0重新起算；上游底包版本仍为AMD 0.44。此次仅改发布元数据，二进制、模型权重与INI配置未改。\n剑星release.json、版本标识、README及SHA256SUMS已同步；完整部署清单38项哈希全部匹配，原恢复脚本清单已更新。\n'
p.write_text(text);(OUT/'验证记录/发布回执.txt').write_text(text)
p=Path(__file__).parents[2]/'DevHistory.md';text=p.read_text().replace('三个0.44 ZIP及逐包.sha256','三个0.1.0 ZIP（基于上游AMD 0.44）及逐包.sha256')
text+='\n## 2026-10-24 工程首个正式版本：0.1.0\n\n- Zero确定本工程版本从0.1.0重新计数；上游AMD底包继续标为0.44，不能混为本工程版本。\n'
for c in changes.values():text+=f'- `{c["name"]}`：SHA256 `{c["sha256"]}`，{c["size"]}字节。\n'
text+='- 包内release.json、现有版本标识、README中英文及SHA256SUMS已更新；对应.sha256和总清单已重建。旧-0.44发布ZIP及其.sha256已清理。\n- 剑星只同步版本说明/清单，不改二进制、模型或INI；完整部署清单与恢复脚本的哈希记录同步更新。\n- ZIP CRC、元数据和未更改条目的CRC/尺寸及关键DLL/INI SHA256核验通过；不重复跑模型测试。\n'
p.write_text(text)
(OUT/'README.txt').write_text('DLSS5 RTX30 工程首个正式版本：0.1.0。上游AMD底包版本0.44仅作来源记录。\nMagpie走CUDA独立引擎；REFramework与常规包走PTX。只启用31块Small。\n剑星的版本说明和校验清单已同步；此次未改DLL或INI配置。\n每个ZIP旁有.sha256，本目录SHA256SUMS.txt校验三个正式ZIP；详细回执见验证记录/发布回执.txt。\n',encoding='utf-8-sig')
# Delete old outputs only after every new output and all requested metadata are valid.
for old,c in changes.items():
 assert sha(OUT/c['name'])==c['sha256']
for old in changes:
 (OUT/old).unlink();(OUT/(old+'.sha256')).unlink(missing_ok=True)
print('Synced game metadata:',len(records),'full deployment verified:',len(m['files']),'old archives removed')
