from pathlib import Path
import sys,os,re,json,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));sys.path.insert(0,str(p.parent))
import build_sm86_dlls as b
import v31.codegen as pack
import local_quad,shared_forward
from pe_fatbins import assemble
selected=json.loads((p.parent/'v27/selected.json').read_text());stock=b.override_maxnreg;MODE='baseline'
def worker(task):
 import v22.codegen as v22,v24.codegen as v24
 pack.MODE='pack5';v22.pack=pack.pack;v22.declarations=pack.declarations;v24.quad=pack.quad;local_quad.AUDIT=[]
 if MODE.startswith('quad_local'):v24.fuse_quads=local_quad.fuse_quads
 fb=task[0]
 def override(text,limit):
  text,n=stock(text,limit)
  if fb==0:
   parts=re.split(r'(?=\.visible \.entry )',text)
   for i,part in enumerate(parts):
    m=re.match(r'\.visible \.entry (\w+)',part)
    if m and m[1] in selected['kernel_caps']:parts[i],_=stock(part,selected['kernel_caps'][m[1]])
   text=''.join(parts)
  if 'shared' in MODE:text,changed=shared_forward.apply(text,fb)
  return text,n
 b.override_maxnreg=override;result=b.worker_compile_fatbin(task)
 (p/f'quad-audit-{MODE}-fb{fb:02}.json').write_text(json.dumps(local_quad.AUDIT,indent=2)+'\n');return result

def main():
 global MODE
 root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());assert hashlib.sha256(raw).hexdigest()=='2bc19bc09a7b89dd44f73e2ac0108fcc586e2154bdd0830f242f4f040e28789f';b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));rows=json.loads((p/'candidates.json').read_text()) if (p/'candidates.json').exists() else {}
 for MODE in sys.argv[1:] or ['baseline','quad_fb1','quad_local']:
  target=set(range(15)) if MODE=='baseline' else ({1} if MODE=='quad_fb1' else (set(range(7)) if MODE=='quad_local' else {1,2,3}));cache=p/'artifacts'/MODE;cache.mkdir(parents=True,exist_ok=True);os.environ['DLSSNR_BUILD_CACHE']=str(cache);blobs={}
  for fb in set(range(15))-target:
   for suffix in ['bin','cubin','ptx']:
    dst=cache/f'fatbin{fb:02}.{suffix}';src=p/f'artifacts/baseline/fatbin{fb:02}.{suffix}'
    if not dst.exists():os.link(src,dst)
   blobs[fb]=(cache/f'fatbin{fb:02}.bin').read_bytes()
  tasks=[(i,bytes(raw[locs[i].offset:locs[i].offset+locs[i].size]),True,True,'multidef',False,'lowhigh',selected['base_caps'].get(str(i)),'swar','mbarrier','lowhigh8',12 if MODE in ('quad_fb1','quad_local') or (MODE=='quad_fb1_shared' and i==1) else 8) for i in sorted(target)]
  with ProcessPoolExecutor(max_workers=3) as pool:
   for f in as_completed([pool.submit(worker,t) for t in tasks]):
    i,blob,msg=f.result();assert 'ELF O4' in msg;blobs[i]=blob;print(MODE,i,msg,flush=True)
  data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);assert len(data)==266414592 and all(x[1]=='inline' for x in manifest);out=root/f'nvngx_dlssnr_sm86_v34_{MODE}.dll';out.write_bytes(data);rows[MODE]={'path':str(out),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest,'changed_fbs':sorted(target) if MODE!='baseline' else []};(p/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n')
  if MODE=='baseline':assert rows[MODE]['sha256']=='1190121f18a03080352fcec5d7a0b79ef47da0bb8ef2e00063e3b6999ff65c86'
if __name__=='__main__':main()
