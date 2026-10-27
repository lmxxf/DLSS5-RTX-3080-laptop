from pathlib import Path
import subprocess,os,json,hashlib
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');rows={}
for name,mask in [('a',9),('b',14),('ab',15)]:
 out=root/f'nvngx_dlssnr_sm86_v27_{name}.dll';args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out),'--half-pack','swar','--bulk-completion','mbarrier','--fp8-decode','lowhigh8','--mma-layout','lowhigh','--v24-mask',str(mask)]
 for fb in [0,3,4,5,6]:args+=['--maxnreg',f'{fb}:255']
 env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 with (p/f'build-{name}.log').open('w') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 rows[name]={'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'mask':mask,'args':args,'manifest':json.loads(out.with_suffix('.manifest.json').read_text())};assert rows[name]['bytes']==266414592 and all(x[1]=='inline' for x in rows[name]['manifest']);(p/'factors.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,rows[name]['sha256'],flush=True)
