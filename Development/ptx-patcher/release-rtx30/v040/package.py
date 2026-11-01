from common import *
import zipfile,copy,struct,shutil
def compressed(src,dst,info):
 assert not info.flag_bits&9
 src.fp.seek(info.header_offset);head=src.fp.read(30);assert head[:4]==b'PK\x03\x04';nl,el=struct.unpack_from('<HH',head,26);extra=src.fp.read(nl+el);clone=copy.copy(info);clone.header_offset=dst.fp.tell();dst._writecheck(clone);dst._didModify=True;dst.fp.write(head+extra);left=info.compress_size
 while left:
  chunk=src.fp.read(min(left,1024*1024));assert chunk;dst.fp.write(chunk);left-=len(chunk)
 dst.filelist.append(clone);dst.NameToInfo[clone.filename]=clone;dst.start_dir=dst.fp.tell()
d=read(P/'deployment.json');packages=[]
for pf in d['profiles']:
 stage=Path(pf['stage']);files={f.relative_to(stage).as_posix():f for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt'};checks={n:sha(f) for n,f in files.items()};(stage/'SHA256SUMS.txt').write_text(''.join(f'{h}  {n}\n' for n,h in sorted(checks.items())));files['SHA256SUMS.txt']=stage/'SHA256SUMS.txt';archive=OUT/(pf['name']+'.zip');assert not archive.exists();tmp=archive.with_suffix('.zip.tmp');assert not tmp.exists();reused=0
 with zipfile.ZipFile(pf['source_zip']) as src,zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as dst:
  oldchecks={n:h for h,n in [line.split('  ',1) for line in src.read('SHA256SUMS.txt').decode('utf-8-sig').splitlines()]}
  for n,f in sorted(files.items()):
   if n in src.namelist() and n in checks and oldchecks.get(n)==checks[n]:compressed(src,dst,src.getinfo(n));reused+=1
   else:dst.write(f,n)
 with zipfile.ZipFile(tmp) as z:
  assert z.testzip() is None;assert z.read('SHA256SUMS.txt')==(stage/'SHA256SUMS.txt').read_bytes();assert read(stage/'release.json')['version']=='0.4.0';assert hashlib.sha256(z.read('nvngx_dlssnr.dll')).hexdigest()==SHA
  for n,h in checks.items():
   digest=hashlib.sha256()
   with z.open(n) as f:
    for c in iter(lambda:f.read(8<<20),b''):digest.update(c)
   assert digest.hexdigest()==h,n
  assert not any(n.startswith(('DLSS5-AMD/','shaders/')) or n.endswith(('LmxxfNrRuntime.dll','dlss5-amd.addon64')) for n in z.namelist())
 tmp.replace(archive);digest=sha(archive);(OUT/(archive.name+'.sha256')).write_text(f'{digest}  {archive.name}\n');packages.append({'name':archive.name,'path':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'files':len(files),'unchanged_compressed_entries_reused':reused,'NR_sha256':SHA,'CRC_pass':True,'all_member_SHA_pass':True});write(P/'packages.json',packages);print('built and checked',archive.name,archive.stat().st_size,digest,flush=True)
# Archive v0.3.0 only after all three v0.4.0 ZIPs pass CRC and all member hashes.
old_dir=OUT/'archive/v0.3.0';assert not old_dir.exists();old_dir.mkdir();archived=[]
for pf in d['profiles']:
 old=Path(pf['source_zip']);assert sha(old)==pf['source_zip_sha256']
 for f in [old,old.with_name(old.name+'.sha256')]:
  target=old_dir/f.name;assert f.exists() and not target.exists();oldsha=sha(f);shutil.move(str(f),str(target));assert sha(target)==oldsha;archived.append({'old_path':str(f),'archive_path':str(target),'sha256':oldsha})
 pf['archived_source_zip']=str(old_dir/old.name)
for name in ['SHA256SUMS.txt','README.txt','release-v0.3.0.json']:
 f=OUT/name
 if f.exists():
  target=old_dir/name;shutil.move(str(f),str(target));archived.append({'old_path':str(f),'archive_path':str(target),'sha256':sha(target)})
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{x["sha256"]}  {x["name"]}\n' for x in sorted(packages,key=lambda x:x['name'])));write(OUT/'release-v0.4.0.json',packages);(OUT/'README.txt').write_text('DLSS5 RTX30 当前正式本地版 v0.4.0 / PTX V4.0。三包及逐包SHA已生成；本轮未上传网盘。\n模型GPU配对均值 720p5.61~5.66 /900p8.27~8.30 /1080p10.99~11.00ms，不是游戏FPS或逐帧上界。默认1.0/1.0，增强INI1.5/1.1。\n旧0.3.0三包及清单归档archive/v0.3.0；既有v0.1.0/v0.2.0归档保留。\n',encoding='utf-8-sig');write(P/'deployment.json',d);write(P/'archive.json',{'version':'0.3.0','archive_dir':str(old_dir),'files':archived,'older_archives_unchanged':all(sha(Path(f))==h for f,h in d['historical_archives'].items())})
# Update current identities in pre-existing install manifests; preserve original backup fields.
updates=[];sb=Path('/mnt/c/Program Files (x86)/Steam/steamapps/common/StellarBlade/SB/Binaries/Win64');current=next(x for x in packages if x['name'].startswith('OptiScaler-DLSS5'))
for f in [ROOT/'backups/20261024-StellarBlade-full/manifest.json',OUT/'StellarBlade-install-manifest.json',ROOT/'StellarBlade-install-manifest.json']:
 if not f.exists():continue
 m=read(f);m['archive']=current['path'];m['archive_sha256']=current['sha256']
 for item in m.get('files',[]):
  path=sb/item['file']
  if path.exists():item['new_sha256']=sha(path)
 write(f,m);updates.append({'path':str(f),'sha256':sha(f)})
write(P/'install-manifests.json',updates);print('PASS3 ZIPs;old0.3.0 ZIPs/sidecars/manifests archived;older archives unchanged')
