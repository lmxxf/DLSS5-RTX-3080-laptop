"""Repackage metadata only; copy unchanged compressed entries byte-for-byte."""
from pathlib import Path
import zipfile,copy,struct,hashlib,json,shutil,re
OUT=Path('/mnt/c/DLSS5-5090-dll/发布打包')
VERSION='0.1.0'
sha=lambda b:hashlib.sha256(b).hexdigest()
changes={};new_archives=[]

def copy_compressed(src,dst,info):
 assert not info.flag_bits & 9, 'Unexpected encrypted/data-descriptor ZIP entry'
 src.fp.seek(info.header_offset);header=src.fp.read(30)
 assert header[:4]==b'PK\x03\x04'
 name_len,extra_len=struct.unpack_from('<HH',header,26)
 extra=src.fp.read(name_len+extra_len)
 clone=copy.copy(info);clone.header_offset=dst.fp.tell()
 dst._writecheck(clone);dst._didModify=True
 dst.fp.write(header+extra)
 left=info.compress_size
 while left:
  chunk=src.fp.read(min(left,1024*1024));assert chunk;dst.fp.write(chunk);left-=len(chunk)
 dst.filelist.append(clone);dst.NameToInfo[clone.filename]=clone;dst.start_dir=dst.fp.tell()

def english(name,route):
 return f'''DLSS5 RTX 30 Series - Project Release {VERSION}\n\nPackage: {name}\nRoute: {route}\nOnly the 31-block Small model is enabled.\n\nClose the game/application and back up existing files before extracting all files.\nFor OptiScaler, extract beside the actual game executable; do not mix the standard and REFramework packages. F6 toggles NR.\nThe standard package includes complete FFX support files and uses DLSS as its output backend. In-game DLSS and supported FFX inputs can reach NR. Quality mode is recommended for clarity; 4K Ultra Performance still renders internally near 720p.\nMagpie uses the CUDA sm_86 independent engine. Its small/ directory retains all 93 weights; legacy model switching is disabled.\nExisting binaries and runtime settings are unchanged by this version renumbering. See README.txt for detailed settings, validation scope and installation notes.\n'''.encode('utf-8')

for old in sorted(OUT.glob('*-RTX30-0.44.zip')):
 new=old.with_name(old.name.replace('-RTX30-0.44','-RTX30-'+VERSION));temp=new.with_suffix('.zip.tmp')
 with zipfile.ZipFile(old) as src:
  names=src.namelist();meta=json.loads(src.read('release.json'));meta['name']=meta['name'].replace('-RTX30-0.44','-RTX30-'+VERSION);meta['version']=VERSION
  updates={'release.json':json.dumps(meta,indent=2,ensure_ascii=False).encode('utf-8')}
  for name in ['DLSS5-AMD-VERSION.txt','DLSS5-RTX30-VERSION.txt']:
   if name in names:updates[name]=(f'{VERSION}\n{meta["name"]}\n31-block Small only\n').encode('utf-8')
  for name in ['README.txt','README.en.txt']:
   if name in names:
    text=src.read(name).decode('utf-8-sig').replace('-RTX30-0.44','-RTX30-'+VERSION).replace('DLSS5 RTX 30 系 0.44','DLSS5 RTX 30 系 '+VERSION)
    text='项目发布版本：'+VERSION+'\n'+text if name=='README.txt' else 'Project release: '+VERSION+'\n'+text
    updates[name]=text.encode('utf-8-sig')
  if 'README.en.txt' not in names:updates['README.en.txt']=english(meta['name'],meta['route'])
  # Preserve the existing checksum rows for all unchanged files.
  checks={rel:digest for digest,rel in (l.split('  ',1) for l in src.read('SHA256SUMS.txt').decode('utf-8-sig').splitlines())}
  for n,b in updates.items():checks[n]=sha(b)
  updates['SHA256SUMS.txt']=''.join(f'{digest}  {n}\n' for n,digest in sorted(checks.items())).encode('utf-8')
  with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as dst:
   for info in src.infolist():
    if info.filename in updates:dst.writestr(info.filename,updates[info.filename])
    else:copy_compressed(src,dst,info)
   for n,b in updates.items():
    if n not in names:dst.writestr(n,b)
  with zipfile.ZipFile(temp) as verify:
   assert verify.testzip() is None
   assert json.loads(verify.read('release.json'))['version']==VERSION
   for n,b in updates.items():assert verify.read(n)==b
   unchanged=[n for n in names if n not in updates]
   for n in unchanged:
    a,b=src.getinfo(n),verify.getinfo(n);assert (a.CRC,a.file_size,a.compress_size)==(b.CRC,b.file_size,b.compress_size)
   for n in ['nvngx_dlssnr.dll','dxgi.dll','dlss5-amd.addon64','OptiScaler.ini']:
    if n in names:assert sha(src.read(n))==sha(verify.read(n)),n
  temp.replace(new)
  oldsha=sha(old.read_bytes());newsha=sha(new.read_bytes())
  (OUT/(new.name+'.sha256')).write_text(newsha+'  '+new.name+'\n')
  changes[old.name]={'name':new.name,'old_sha256':oldsha,'sha256':newsha,'old_size':old.stat().st_size,'size':new.stat().st_size,'unchanged_files':len(unchanged),'metadata':list(updates)}
  new_archives.append(new)
  print('REVERSIONED',new.name,new.stat().st_size,newsha,flush=True)
assert len(new_archives)==3
(OUT/'SHA256SUMS.txt').write_text(''.join(f'{sha(p.read_bytes())}  {p.name}\n' for p in sorted(new_archives)))
Path(__file__).with_name('version-0.1.0.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
(OUT/'验证记录/version-0.1.0.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2))
print('All versioned archives verified; ready for metadata sync',flush=True)
