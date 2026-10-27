from pathlib import Path
import subprocess,os,json,hashlib,sys
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');rows=json.loads((p/'builds.json').read_text()) if (p/'builds.json').exists() else {}
def build(name,mask,caps=None):
 out=root/f'nvngx_dlssnr_sm86_v24_{name}.dll';args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out),'--half-pack','swar','--bulk-completion','mbarrier','--fp8-decode','prmt8','--v24-mask',str(mask)]
 caps=caps or {i:255 for i in [0,3,4,5,6]}
 for i,cap in caps.items():args+=['--maxnreg',f'{i}:{cap}']
 env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 with (p/f'build-{name}.log').open('w') as f:subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 r={'path':str(out),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'mask':mask,'caps':caps,'args':args,'manifest':json.loads(out.with_suffix('.manifest.json').read_text())};assert r['bytes']==266414592 and all(x[1]=='inline' for x in r['manifest']);rows[name]=r;(p/'builds.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,r['sha256'],flush=True)
if __name__=='__main__':
 for name,mask in [('a',1),('bias',2),('b',6),('c',8),('abc',15)]:
  if name not in rows:build(name,mask)
