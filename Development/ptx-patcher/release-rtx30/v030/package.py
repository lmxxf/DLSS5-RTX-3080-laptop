from pathlib import Path
import json,hashlib,zipfile,copy,struct,shutil
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');out=root/'发布打包';d=json.loads((p/'deployment.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();packages=[]
def compressed(src,dst,info):
 assert not info.flag_bits&9
 src.fp.seek(info.header_offset);head=src.fp.read(30);assert head[:4]==b'PK\x03\x04';nl,el=struct.unpack_from('<HH',head,26);extra=src.fp.read(nl+el);clone=copy.copy(info);clone.header_offset=dst.fp.tell();dst._writecheck(clone);dst._didModify=True;dst.fp.write(head+extra);left=info.compress_size
 while left:
  chunk=src.fp.read(min(left,1024*1024));assert chunk;dst.fp.write(chunk);left-=len(chunk)
 dst.filelist.append(clone);dst.NameToInfo[clone.filename]=clone;dst.start_dir=dst.fp.tell()
for profile in d['profiles']:
 stage=Path(profile['stage']);name=profile['name'];assert sha(stage/'nvngx_dlssnr.dll')==d['NR_sha256'];files={f.relative_to(stage).as_posix():f for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt'}
 checks={n:sha(f) for n,f in files.items()};(stage/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(checks.items())));files['SHA256SUMS.txt']=stage/'SHA256SUMS.txt'
 archive=out/(name+'.zip');assert not archive.exists(),archive;tmp=archive.with_suffix('.zip.tmp');reused=0
 with zipfile.ZipFile(profile['source_zip']) as src,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as dst:
  oldchecks={rel:h for h,rel in [line.split('  ',1) for line in src.read('SHA256SUMS.txt').decode('utf-8-sig').splitlines()]}
  for n,f in sorted(files.items()):
   if n in src.namelist() and n in checks and oldchecks.get(n)==checks[n]:compressed(src,dst,src.getinfo(n));reused+=1
   else:dst.write(f,n)
 with zipfile.ZipFile(tmp) as z:
  assert z.testzip() is None;assert json.loads(z.read('release.json'))['version']=='0.3.0';assert hashlib.sha256(z.read('nvngx_dlssnr.dll')).hexdigest()==d['NR_sha256']
  assert not any(n.startswith(('DLSS5-AMD/','shaders/')) or n.endswith(('LmxxfNrRuntime.dll','dlss5-amd.addon64')) for n in z.namelist())
  for n,h in checks.items():
   hh=hashlib.sha256()
   with z.open(n) as f:
    for chunk in iter(lambda:f.read(1024*1024),b''):hh.update(chunk)
   assert hh.hexdigest()==h,n
 tmp.replace(archive);digest=sha(archive);(out/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n');packages.append({'name':archive.name,'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'files':len(files),'unchanged_compressed_entries_reused':reused,'NR_sha256':d['NR_sha256']});print(packages[-1],flush=True)
# Archive originals only after all new archives passed CRC and every per-file SHA.
archive_dir=out/'archive/v0.2.0';archive_dir.mkdir(parents=True,exist_ok=True)
for profile in d['profiles']:
 old=Path(profile['source_zip']);assert sha(old)==profile['source_zip_sha256']
 for f in [old,old.with_name(old.name+'.sha256')]:
  target=archive_dir/f.name;assert not target.exists(),target;shutil.move(str(f),str(target))
oldmeta=out/'release-v0.2.0.json'
if oldmeta.exists():
 target=archive_dir/oldmeta.name;assert not target.exists();shutil.move(str(oldmeta),str(target))
if (out/'SHA256SUMS.txt').exists():shutil.copy2(out/'SHA256SUMS.txt',archive_dir/'SHA256SUMS.txt')
(out/'SHA256SUMS.txt').write_text(''.join(f'{r["sha256"]}  {r["name"]}\n' for r in sorted(packages,key=lambda x:x['name'])))
(out/'README.txt').write_text('DLSS5 RTX30 当前正式版本0.3.0；三包统一PTX V3.1_pack5。\n720p5.75ms /900p8.42ms /1080p11.35ms（另轮5.62/8.38/11.07ms）。OptiScaler默认1.0/1.0，附增强风格1.5/1.1。\n三个ZIP及逐包.sha256位于本目录；SHA256SUMS.txt只列0.3.0三个正式包。\n旧0.2.0 ZIP归档在archive/v0.2.0。\n',encoding='utf-8-sig')
(p/'packages.json').write_text(json.dumps(packages,indent=2,ensure_ascii=False)+'\n');(out/'release-v0.3.0.json').write_text(json.dumps(packages,indent=2,ensure_ascii=False)+'\n')
print('PASS3 ZIPs:CRC,all fileSHA,15/15O4 V3.1_pack5 core;old ZIPs archived')
