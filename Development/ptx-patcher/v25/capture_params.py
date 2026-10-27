from pathlib import Path
import subprocess,os,json,re,hashlib,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';rows={}
for w in [1280,1600,1920]:
 h={1280:720,1600:900,1920:1080}[w];trace=root/f'v25-params-{w}.csv';out=root/f'v25-params-{w}.rgb32';env=os.environ.copy();env['V23_TRACE']=str(trace).replace('/mnt/c/','C:/');env['WSLENV']=env.get('WSLENV','')+':V23_TRACE';args=[str(root/'nvngx.dll_runner/bench_profile.exe'),core,str(root/'nvngx_dlssnr_sm86_v24.dll').replace('/mnt/c/','C:/'),str(w),str(h),'2','50','1',str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 with (p/f'params-{w}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90)
 assert r.returncode==0;raw=trace.read_bytes();kept=[];params=[];calls=[]
 for line in raw.decode().splitlines():
  x=line.split(',')
  if x[0] in ['CHAIN','KERNEL'] and int(x[1])!=50:continue
  kept.append(line)
  if x[0]=='PARAM':params.append({'name':x[2],'bytes':int(x[3]),'hex':x[4]})
  if x[0]=='KERNEL':calls.append({'name':x[4],'grid':list(map(int,x[5:8])),'block':list(map(int,x[8:11]))})
 assert len(params)==len(calls)==82;data=np.fromfile(out,np.uint32);out.unlink();args[0]=str(root/'nvngx.dll_runner/bench_sky.exe');env.pop('V23_TRACE',None)
 with (p/f'params-reference-{w}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert r.returncode==0;ref=np.fromfile(out,np.uint32);assert np.array_equal(data,ref);out.unlink();trace.unlink();(p/f'params-{w}.csv').write_text('\n'.join(kept)+'\n');rows[str(w)]={'height':h,'warmup':50,'iterations':1,'raw_csv_sha256':hashlib.sha256(raw).hexdigest(),'bitdiff':0,'params':params,'calls':calls};(p/'launch-params.json').write_text(json.dumps(rows,indent=2)+'\n');print(w,'82 parameter blocks, exact reference output',flush=True)
