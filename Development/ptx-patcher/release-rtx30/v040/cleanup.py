from common import *
import shutil
v=read(P/'validation.json');assert v['passed'];removed=[]
for d in [STAGE,TOOLS]:
 assert d.is_dir();files=[f for f in d.rglob('*') if f.is_file()];removed.append({'path':str(d),'files':len(files),'logical_bytes':sum(f.stat().st_size for f in files)});shutil.rmtree(d)
assert not list(P.glob('*.log'));assert all(sha(x['installed_NR'])==SHA for x in v['live_sites']);assert all(sha(x['path'])==x['sha256'] for x in v['packages']);assert sha(CORE)==SHA;assert BACKUP.exists() and sha(BACKUP/'nvngx_dlssnr-v0.3.0.dll')==OLD;write(P/'cleanup.json',{'complete':True,'removed':removed,'per_run_log_fragments_remaining':0,'rollback_backup_retained':str(BACKUP),'release_ZIPs_retained':True});v.update(cleanup_complete=True,temporary_staging_removed=True,test_frames_removed=True);write(P/'validation.json',v);print('cleanup PASS;rollback backup and official ZIPs retained;no staging/frames/logfragments')
