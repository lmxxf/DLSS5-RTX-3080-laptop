from pathlib import Path
import json,subprocess,os,sys,hashlib,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');meta=json.loads((p/'counter-build.json').read_text());core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';rows=json.loads((p/'counter-runs.json').read_text()) if (p/'counter-runs.json').exists() else {}
for w in list(map(int,sys.argv[1:])) or [1280,1600,1920]:
 h={1280:720,1600:900,1920:1080}[w];csv=root/f'v25-count-{w}.csv';out=root/f'v25-count-{w}.rgb32';env=os.environ.copy();env['V23_TRACE']=str(csv).replace('/mnt/c/','C:/');env['WSLENV']=env.get('WSLENV','')+':V23_TRACE';args=[str(root/'nvngx.dll_runner/bench_counter.exe'),core,meta['path'].replace('/mnt/c/','C:/'),str(w),str(h),'2','1','1',str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 with (p/f'count-{w}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90)
 assert r.returncode==0,(w,r.returncode);a=np.fromfile(out,np.uint32);gold=np.fromfile(root/f'ptx-v25-bench/gold-1-1-{w}.rgb32',np.uint32);assert a.shape==gold.shape;diff=int(np.count_nonzero(a!=gold));assert diff==0,(w,diff);out.unlink();text=csv.read_text();(p/f'count-{w}.csv').write_text(text);csv.unlink();counts={}
 for line in text.splitlines():
  if line.startswith('COUNT,1,'):
   _,frame,id,bin,value=line.split(',');counts.setdefault(id,{})[bin]=int(value)
 assert any(x.get('0',0) for x in counts.values()),'Counter buffer not updated'
 rows[str(w)]={'height':h,'bitdiff':diff,'warmup':1,'iterations':1,'counts':counts,'diagnostic_only':True};(p/'counter-runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(w,'exact tensor output, nonzero runtime HMMA counters',flush=True)
