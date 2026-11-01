from common import *
import shutil
D=read(P/'deployment.json');records=[]
# Write-ahead deployment metadata and one old-core copy already exist in BACKUP.
for s in D['sites']:
 base=Path(s['base']);assert sha(base/s['file'])==s['old_NR_sha256'];assert all(sha(base/n)==h for n,h in s['preserved_files'].items())
 if s['label']=='magpie':
  target=Path(s['new_base']);assert not target.exists();base.rename(target);base=target
 dst=base/s['file'];tmp=dst.with_name(dst.name+'.v040.tmp');assert not tmp.exists();shutil.copy2(CORE,tmp);assert sha(tmp)==SHA;tmp.replace(dst)
 if s['profile']:
  pf=next(x for x in D['profiles'] if x['label']==s['profile']);stage=Path(pf['stage']);write(stage/'nvngx_dlssnr.manifest.json',D['manifest'])
  for n in ['README.txt','README.en.txt','DLSS5-RTX30-VERSION.txt','release.json']:shutil.copy2(stage/n,base/n)
  write(base/'nvngx_dlssnr.manifest.json',D['manifest'])
  names=[f.relative_to(stage) for f in stage.rglob('*') if f.is_file() and f.name!='SHA256SUMS.txt' and (base/f.relative_to(stage)).is_file()]
  (base/'SHA256SUMS.txt').write_text(''.join(f'{sha(base/n)}  {n.as_posix()}\n' for n in sorted(names)))
 else:write(ROOT/'nvngx_dlssnr_sm86_fast.manifest.json',D['manifest'])
 assert sha(dst)==SHA and all(sha(base/n)==h for n,h in s['preserved_files'].items());records.append({**s,'installed_base':str(base),'installed_NR':str(dst),'new_NR_sha256':sha(dst),'support_files_preserved':True});write(P/'live.json',{'sites':records,'complete':len(records)==5,'backup':str(BACKUP),'core_backup':D['core_backup'],'NR_sha256':SHA})
print('PASS five core replacements and SHA; supporting hosts/bridges/INIs byte-identical; Magpie renamed')
