from pathlib import Path
import os,sys,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll');art=p/'artifacts';art.mkdir(exist_ok=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()

def job(args):
 i,limit,blob=args;os.environ['DLSSNR_BUILD_CACHE']=str(art/f'fb{i:02d}-cap{limit}')
 return b.worker_compile_fatbin((i,blob,True,True,'multidef',False,'evenodd',limit))

def main():
 assert sha(root/'nvngx_dlssnr_sm86_v2.dll')=='737af93c2843fe18462c39da36a0a482e4d410493bed0e178fecabf526880f74'
 src=(root/'nvngx_dlssnr.dll').read_bytes();assert hashlib.sha256(src).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f'
 locs=b.dp.find_fatbins(src);base=(root/'nvngx_dlssnr_sm86_v2.dll').read_bytes();results={};rows=[]
 tasks=[(i,limit,src[locs[i].offset:locs[i].offset+locs[i].size]) for i,limit in [(3,168),(3,255),(0,255),(1,255),(2,255),(4,255),(5,255),(6,255)]]
 with ProcessPoolExecutor(max_workers=3) as pool:
  ff={pool.submit(job,t):t[:2] for t in tasks}
  for future in as_completed(ff):
   i,blob,msg=future.result();ii,lim=ff[future];assert i==ii and 'ELF O4' in msg;results[(i,lim)]=blob;rows.append({'FB':i,'limit':lim,'message':msg});print(i,lim,msg,flush=True)
 configs={'c256-168':{3:168},'c256-255':{3:255},'fb00-255':{0:255},'fb04-255':{4:255},'fb05-255':{5:255},'fb06-255':{6:255},'hot255':{i:255 for i in [0,3,4,5,6]},'all255':{i:255 for i in range(7)}}
 outputs={}
 for name,caps in configs.items():
  data,manifest=assemble(base,locs,{i:results[i,cap] for i,cap in caps.items()},b.dp);b.fast_update_pe_checksum(data);out=root/f'nvngx_dlssnr_sm86_v21_{name}.dll';out.write_bytes(data)
  outputs[name]={'path':str(out),'caps':caps,'bytes':len(data),'sha256':sha(out),'manifest':manifest};print(name,len(data),outputs[name]['sha256'],flush=True)
 (p/'build-results.json').write_text(json.dumps({'compiles':rows,'variants':outputs,'baseline_sha256':hashlib.sha256(base).hexdigest(),'unchanged_8_to14':'reuse V2 O4; controls only change indicated FB caps'},indent=2)+'\n')
if __name__=='__main__':main()
