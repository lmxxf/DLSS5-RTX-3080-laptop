from pathlib import Path
import subprocess,os,json,hashlib
p=Path(__file__).resolve().parent;out=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v25_hybrid.dll');args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out),'--half-pack','swar','--bulk-completion','mbarrier','--fp8-decode','hybrid8','--v24-mask','8']
for i in [0,3,4,5,6]:args+=['--maxnreg',f'{i}:255']
env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts/decode')
with (p/'build-decode.log').open('w') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
r={'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'args':args,'manifest':json.loads(out.with_suffix('.manifest.json').read_text())};(p/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(r['sha256'])
