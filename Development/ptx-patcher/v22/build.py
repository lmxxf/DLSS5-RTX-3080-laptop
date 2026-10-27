from pathlib import Path
import os,subprocess,json,hashlib
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');rows={}
for name,options in [('async',['--bulk-completion','mbarrier']),('swar',['--half-pack','swar']),('combo',['--bulk-completion','mbarrier','--half-pack','swar'])]:
 out=root/f'nvngx_dlssnr_sm86_v22_{name}.dll';args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out)]+options
 for i in [0,3,4,5,6]:args+=['--maxnreg',f'{i}:255']
 env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 with (p/f'build-{name}.log').open('w') as log:subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 rows[name]={'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'args':args,'manifest':json.loads(out.with_suffix('.manifest.json').read_text())};(p/'builds.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,rows[name]['sha256'],flush=True)
