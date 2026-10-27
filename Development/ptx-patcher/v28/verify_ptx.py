from pathlib import Path
import json,hashlib,re,sys
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import build
raw=Path('/mnt/c/DLSS5-5090-dll/nvngx_dlssnr.dll').read_bytes();locs=build.b.dp.find_fatbins(raw);tasks=[]
for fb in (0,4,5):
 l=locs[fb];tasks.append((f'verify{fb}',fb,{},raw[l.offset:l.offset+l.size]))
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=3) as pool:
  for f in as_completed([pool.submit(build.worker,t) for t in tasks]):
   name,fb,caps,blob,msg=f.result();print(msg,flush=True)
 def sha(b):return hashlib.sha256(b).hexdigest()
 out={}
 for fb in (0,4,5):
  a=(p/f'artifacts/verify{fb}/fatbin{fb:02}.cubin').read_bytes();b=(p/f'artifacts/baseline/fatbin{fb:02}.cubin').read_bytes();assert a==b;out[f'FB{fb}']={'baseline_cubin_SHA256':sha(a),'rebuilt_baseline_identical':True,'candidates':{}}
  baseline=(p/f'artifacts/verify{fb}/fatbin{fb:02}.ptx').read_text();norm=lambda s:re.sub(r'\.maxnreg\s+\d+','.maxnreg CAP',s)
  for tag,r in json.loads((p/'candidates.json').read_text()).items():
   if r['FB']!=fb:continue
   text=(p/f'artifacts/{tag}/fatbin{fb:02}.ptx').read_text();assert norm(text)==norm(baseline),tag;out[f'FB{fb}']['candidates'][tag]={'only_maxnreg_changes':True,'ptx_sha256':sha(text.encode()),'caps':r['caps']}
 (p/'ptx-controls.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS V27 baseline cubins identical; all ten candidates differ only in maxnreg')
