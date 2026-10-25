"""Verify the exact two-byte host hotfix and record rollback/deployment evidence."""
from pathlib import Path
import hashlib,json,datetime,re
phase=Path(__file__).resolve().parent
game=Path('/mnt/c/XboxGames/Onimusha- Way of the Sword/Content')
backup=Path('/mnt/c/DLSS5-5090-dll/backups/Onimusha-ptx-0.1.0')
def sha(b):return hashlib.sha256(b).hexdigest()
original=(backup/'dxgi.dll').read_bytes();old_sha=sha(original)
assert old_sha=='aa3761f2cdb0d9a4653732bd430019ff421b3ce9471fe3697b553dc6d71714a2'
assert original[0x2b549:0x2b54b]==bytes.fromhex('75 03')
targets=[]
for rel in ['dxgi.dll','_storage_/dxgi.dll']:
 data=(game/rel).read_bytes();assert len(data)==len(original)
 offsets=[i for i,(a,b) in enumerate(zip(original,data)) if a!=b]
 assert offsets==[0x2b549,0x2b54a] and data[0x2b549:0x2b54b]==bytes.fromhex('90 90')
 targets.append({'relative_path':rel,'bytes':len(data),'sha256':sha(data),'differing_offsets':[hex(i) for i in offsets]})
assert targets[0]['sha256']==targets[1]['sha256']=='f3fe9bfbfd3b4add7460713521d4e16d6d95c6fa3bf90db27e7338b6d255f35d'
leftovers=[str(p.relative_to(game)) for p in game.rglob('*') if p.is_file() and p.name.lower() in ['nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']];assert not leftovers,leftovers
bmanifest=json.loads((backup/'backup-manifest.json').read_text())
for name in ['nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']:
 assert sha((backup/name).read_bytes())==bmanifest[name]['sha256']
runtimes={n:sha((game/n).read_bytes()) for n in ['LmxxfNrRuntime.dll','_storage_/LmxxfNrRuntime.dll']};assert len(set(runtimes.values()))==1
patch={'scope':'local Onimusha OptiScaler host AmdBridge physical-adapter admission','original_backup':str(backup/'dxgi.dll'),'original_sha256':old_sha,'patched_sha256':targets[0]['sha256'],'bytes':len(original),'compare_va':'0x18002c13f','compare_file_offset':'0x2b53f','branch_va':'0x18002c149','branch_rva':'0x2c149','branch_file_offset':'0x2b549','before':'75 03','after':'90 90','meaning':'Skip AMD-only rejection; CMP remains; vendor stays 0x10DE. Only two bytes differ.','targets':targets}
cleanup={'performed_by':'Zero initial hotfix, independently verified absent in this audit','relative_paths':['_storage_/nvngx.dll_dlssnr.dll','_storage_/nvngx_dlssnr.dll'],'previous_file_identity':'Zero reported removed files matched PTX v0.1.0 backups; deleted bytes cannot now be re-read. Backup hashes independently verified.','expected_old_hashes':{n:bmanifest[n]['sha256'] for n in ['nvngx.dll_dlssnr.dll','nvngx_dlssnr.dll']},'recursive_remaining_files':leftovers}
log=(game/'OptiScaler.log').read_bytes();text=log.decode('utf-8-sig','replace');lines=text.splitlines()
need=['physical adapter vendor: 10DE, AMD: true','after PrepareFrame HIP/net geometry status=lmxxf modules_ok=40 hip=1','lastEnqueueRc=0'];assert all(x in text for x in need)
kept=[]
for n,line in enumerate(lines,1):
 if any(k in line for k in ['NrBackend: lmxxf','physical adapter vendor:','LmxxfBackend::LmxxfBackend','assets/modules dir=','after Create status=','after PrepareFrame HIP/net','lmxxf nr: eval=','lmxxf status: lmxxf: shutdown','Created DLSSContext feature (1280,720)']):kept.append(f'{n}: {line}')
(phase/'hotfix-live-evidence.txt').write_text('OptiScaler.log snapshot SHA256: '+sha(log)+'\nCurrent run 15:17:21; differs from initial 854x480/31 FPS user report.\n'+'\n'.join(kept)+'\n')
report={'audit_time':datetime.datetime.now().isoformat(),'host_patch':patch,'recursive_cleanup':cleanup,'runtime_sha256':runtimes,'live_log_sha256':sha(log),'live_log_run':'15:17:21 to shutdown 15:19:58; SR input1280x720 output2560x1440','initial_run_evidence':'User-provided original line515 IsAmd 10DE false; original log replaced by new run. First FPS about31 at854x480->2560x1440 was old PTX fallback, not independent-engine FPS.'}
(phase/'hotfix-audit.json').write_text(json.dumps(report,indent=2)+'\n')
bmanifest['dxgi.dll']={'sha256':old_sha,'bytes':len(original),'patched_sha256':targets[0]['sha256'],'patch':{'file_offset':'0x2b549','before':'75 03','after':'90 90'},'deployed_relative_paths':['dxgi.dll','_storage_/dxgi.dll']}
(backup/'backup-manifest.json').write_text(json.dumps(bmanifest,indent=2)+'\n')
for p in [backup/'phase10-deployment.json',phase/'deployment.json']:
 j=json.loads(p.read_text());j.setdefault('original',{})['dxgi.dll']={'sha256':old_sha,'bytes':len(original)}
 j.get('unchanged_host_dlls',{}).pop('dxgi.dll',None)
 j['host_compatibility_patch']=patch;j['recursive_nr_cleanup']=cleanup;j['runtime_copies']=runtimes;j['hotfix_audit_time']=report['audit_time'];j['post_hotfix_live_evidence']=report['live_log_run'];j['ini_sha256']=sha((game/'OptiScaler.ini').read_bytes())
 j['verification']='Original host backup SHA + exact two-byte diff in both hosts + no recursive NR DLL leftovers + both runtime SHA + live LmxxfBackend/hip1/enqueueRc0 verified'
 p.write_text(json.dumps(j,indent=2)+'\n')
print(json.dumps({'original':old_sha,'patched':targets[0]['sha256'],'targets':len(targets),'recursive_old_NR_DLLs':len(leftovers),'runtime_copies_match':True},indent=2))
