"""Full source rebuild: original hot255 plus four explicit C32 entry caps."""
from pathlib import Path
import sys,os,re,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
selected=json.loads((p/'selected.json').read_text());stock_cap=b.override_maxnreg

def worker(task):
 fb=task[0]
 def override(text,limit):
  text,count=stock_cap(text,limit);parts=re.split(r'(?=\.visible \.entry )',text);matched=set()
  for i,part in enumerate(parts):
   m=re.match(r'\.visible \.entry (\w+)',part)
   if m and m[1] in selected['kernel_caps']:
    parts[i],n=stock_cap(part,selected['kernel_caps'][m[1]]);assert n==1;matched.add(m[1])
  assert matched==(set(selected['kernel_caps']) if fb==0 else set());return ''.join(parts),count
 b.override_maxnreg=override;return b.worker_compile_fatbin(task)
if __name__=='__main__':
 raw=bytearray(Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));os.environ['DLSSNR_BUILD_CACHE']=str(p/'artifacts/selected');tasks=[(i,bytes(raw[l.offset:l.offset+l.size]),True,True,'multidef',False,'lowhigh',selected['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',8) for i,l in enumerate(locs)];blobs={}
 with ProcessPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(worker,t) for t in tasks]):
   i,blob,msg=future.result();assert 'ELF O4' in msg;blobs[i]=blob;print(i,msg,flush=True)
 data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);out=Path(selected['path']);out.write_bytes(data);sha=hashlib.sha256(data).hexdigest();assert sha==selected['sha256'],(sha,selected['sha256']);assert len(data)==266414592 and len(manifest)==15 and all(x[1]=='inline' for x in manifest);out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(p/'rebuild-manifest.json').write_text(json.dumps({'path':str(out),'sha256':sha,'bytes':len(data),'manifest':manifest},indent=2)+'\n');print('PASS full 15/15 O4 rebuild SHA',sha)
