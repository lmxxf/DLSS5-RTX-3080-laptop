from pathlib import Path
import zipfile,hashlib,json,shutil
from build_release import OUT,ROOT,sha
GAME=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64')
BACKUP=ROOT/'backups/20261024-StellarBlade-full'
ZIP=OUT/'OptiScaler-DLSS5-RTX30-0.1.0.zip'
BACKUP.mkdir(parents=True,exist_ok=True)
assert (GAME/'SB-Win64-Shipping.exe').is_file()
assert not (BACKUP/'manifest.json').exists(), 'Backup exists: do not overwrite an earlier installation record'
records=[]
with zipfile.ZipFile(ZIP) as z:
 assert z.testzip() is None
 for info in z.infolist():
  if info.is_dir():continue
  rel=info.filename;assert '..' not in Path(rel).parts and not Path(rel).is_absolute()
  target=GAME/rel;data=z.read(info);new=hashlib.sha256(data).hexdigest()
  old=sha(target) if target.exists() else None
  status='unchanged' if old==new else 'replaced' if old else 'new'
  record={'file':rel,'status':status,'old_sha256':old,'new_sha256':new}
  if status=='replaced':
   backup=BACKUP/'original'/rel;backup.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(target,backup);assert sha(backup)==old
  records.append(record)
 # Every conflict is backed up before the first target write.
 manifest={'game':str(GAME),'backup':str(BACKUP),'archive':str(ZIP),'files':records}
 (BACKUP/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 for r in records:
  if r['status']=='unchanged':continue
  target=GAME/r['file'];target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_suffix(target.suffix+'.rtx30-install.tmp')
  tmp.write_bytes(z.read(r['file']));assert sha(tmp)==r['new_sha256'];tmp.replace(target)
 for r in records:assert sha(GAME/r['file'])==r['new_sha256']
print('Verified files',len(records),'replaced',sum(r['status']=='replaced' for r in records),'new',sum(r['status']=='new' for r in records),flush=True)
ffx=next(r for r in records if r['file']=='amd_fidelityfx_dx12.dll')
print('Original FFX backup',BACKUP/'original/amd_fidelityfx_dx12.dll',ffx['old_sha256'],flush=True)
restore='''from pathlib import Path
import json,hashlib,shutil
m=json.loads(Path(__file__).with_name("manifest.json").read_text());game=Path(m["game"]);backup=Path(m["backup"])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[r for r in m["files"] if r["status"]!="unchanged"]
for r in changed:
 p=game/r["file"]
 assert p.exists() and sha(p)==r["new_sha256"], "安装后文件已改变，停止覆盖: "+str(p)
 if r["status"]=="replaced":assert sha(backup/"original"/r["file"])==r["old_sha256"]
for r in changed:
 p=game/r["file"]
 if r["status"]=="new":p.unlink()
 else:shutil.copy2(backup/"original"/r["file"],p)
print("已恢复安装前文件；新增的空目录可自行删除。")
'''
(BACKUP/'restore.py').write_text(restore)
(BACKUP/'恢复说明.txt').write_text('先退出《剑星》，在WSL运行：\npython3 /mnt/c/DLSS5-5090-dll/backups/20261024-StellarBlade-full/restore.py\n脚本恢复被替换文件（包括原版amd_fidelityfx_dx12.dll），删除本次新增文件；安装后又被改动的文件会触发哈希检查，避免覆盖后续修改。\n',encoding='utf-8-sig')
(OUT/'StellarBlade-install-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
