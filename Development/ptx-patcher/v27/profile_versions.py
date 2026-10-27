from pathlib import Path
import os,subprocess,json,re,statistics as st,hashlib,numpy as np,collections
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');work=root/'ptx-v27-profile';work.mkdir(exist_ok=True);core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';fbmap={n:int(f) for f,v in json.loads((p.parent/'v26/resources.json').read_text())['decode'].items() for n in v['kernels']};rows=[];golds={};shapes={};paths={v:root/f'nvngx_dlssnr_sm86_{v}.dll' for v in ['v22','v24','v26']}
for w in [1280,1920]:
 h={1280:720,1920:1080}[w]
 for direction,order in [('forward',['v22','v24','v26']),('reverse',['v26','v24','v22'])]:
  for v in order:
   name=f'{direction}-{v}-{w}';trace=work/(name+'.csv');rgb=work/(name+'.rgb32');env=os.environ.copy();env['V23_TRACE']=str(trace).replace('/mnt/c/','C:/');env['V23_EVENTS']='1';env['WSLENV']=env.get('WSLENV','')+':V23_TRACE:V23_EVENTS';args=[str(root/'nvngx.dll_runner/bench_profile.exe'),core,str(paths[v]).replace('/mnt/c/','C:/'),str(w),str(h),'2','50','20',str(rgb).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
   with (p/f'profile-{name}.log').open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=90)
   assert r.returncode==0;data=np.fromfile(rgb,np.float32);assert np.isfinite(data).all();key=(v,w)
   if key in golds:assert np.array_equal(data.view(np.uint32),golds[key].view(np.uint32))
   else:golds[key]=data.copy()
   rgb.unlink();frames=collections.defaultdict(list);kept=[];raw=trace.read_bytes()
   for line in raw.decode().splitlines():
    a=line.split(',')
    if a[0] in ['CHAIN','KERNEL'] and 0<=int(a[1])<50:continue
    kept.append(line)
    if a[0]=='KERNEL' and int(a[1])>=50:frames[int(a[1])].append({'FB':fbmap[a[4]],'name':a[4],'grid':list(map(int,a[5:8])),'block':list(map(int,a[8:11])),'gpu_ms':float(a[12])})
   assert len(frames)==20 and all(len(rs)==82 for rs in frames.values());signature=[(x['name'],x['grid'],x['block']) for x in next(iter(frames.values()))]
   if w in shapes:assert shapes[w]==signature
   else:shapes[w]=signature
   byfb={}
   for fb in sorted({x['FB'] for rs in frames.values() for x in rs}):
    vals=[sum(x['gpu_ms'] for x in rs if x['FB']==fb) for rs in frames.values()];byfb[str(fb)]={'mean_ms':st.mean(vals),'median_ms':st.median(vals),'calls_per_frame':sum(x['FB']==fb for x in next(iter(frames.values())))}
   (p/f'profile-{name}.csv').write_text('\n'.join(kept)+'\n');trace.unlink();summary=(p/f'profile-{name}.log').read_text().split('SUMMARY')[-1];row={'name':name,'version':v,'width':w,'height':h,'warmup':50,'iterations':20,'DLL_sha256':hashlib.sha256(paths[v].read_bytes()).hexdigest(),'raw_csv_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(data.tobytes()).hexdigest(),'nonfinite':0,'by_FB':byfb,'metrics':{k:float(x) for k,x in re.findall(r'(\w+)=([-+\d.eE]+)',summary)},'calls':next(iter(frames.values()))};rows.append(row);(p/'profile-versions.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,round(sum(t['mean_ms'] for t in byfb.values()),4),flush=True)
