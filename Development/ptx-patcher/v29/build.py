from pathlib import Path
import sys,os,re,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
import codegen as gen
from pe_fatbins import assemble
selected=json.loads((p.parent/'v27/selected.json').read_text());stock=b.override_maxnreg
MODE='exact'
def worker(task):
 import v22.codegen as v22
 gen.MODE=MODE;v22.declarations=gen.declarations;v22.pack=gen.pack
 fb=task[0]
 def override(text,limit):
  text,n=stock(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in selected['kernel_caps']:parts[i],_=stock(part,selected['kernel_caps'][m[1]])
   text=''.join(parts)
  return text,n
 b.override_maxnreg=override;return b.worker_compile_fatbin(task)
if __name__=='__main__':
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));rows={}
 for MODE in ['exact','fast']:
  os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts'/MODE);blobs={};tasks=[(i,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',selected['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',8) for i,l in enumerate(locs)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(worker,t) for t in tasks]):
    i,blob,msg=f.result();assert 'ELF O4' in msg;blobs[i]=blob;print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);out=root/f'nvngx_dlssnr_sm86_v29_{MODE}.dll';out.write_bytes(data);rows[MODE]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest};(p/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
