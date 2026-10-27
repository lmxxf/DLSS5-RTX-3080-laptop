from pathlib import Path
import sys,os,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
root=Path('/mnt/c/DLSS5-5090-dll')
def compile_one(task):
 name,fb,cap,blob=task;os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/name)
 i,out,msg=b.worker_compile_fatbin((fb,blob,True,True,'multidef',False,'evenodd',cap,'swar','mbarrier','prmt8',15));return name,fb,cap,out,msg
if __name__=='__main__':
 source=(root/'nvngx_dlssnr.dll').read_bytes();locs=b.dp.find_fatbins(source);base=(root/'nvngx_dlssnr_sm86_v24_abc.dll').read_bytes();tasks=[];rows={}
 for fb in [1,2,4,5]:
  for cap in ([192,224,255] if fb in [1,2] else [168,192,224]):
   name=f'd{fb}-{cap}';loc=locs[fb];tasks.append((name,fb,cap,source[loc.offset:loc.offset+loc.size]))
 with ProcessPoolExecutor(max_workers=3) as pool:
  futures=[pool.submit(compile_one,task) for task in tasks]
  for future in as_completed(futures):
   name,fb,cap,blob,msg=future.result();assert 'ELF O4' in msg;data,manifest=assemble(base,locs,{fb:blob},b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and manifest[0][1]=='inline';out=root/f'nvngx_dlssnr_sm86_v24_{name}.dll';out.write_bytes(data);rows[name]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'mask':15,'FB':fb,'cap':cap,'compile':msg,'manifest':manifest};(p/'caps.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,msg,flush=True)
