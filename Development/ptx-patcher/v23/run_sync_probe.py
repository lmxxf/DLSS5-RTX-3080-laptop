from pathlib import Path
import subprocess,json,re,numpy as np,hashlib,datetime,sys
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll';mode=sys.argv[1] if len(sys.argv)>1 else 'bypass';stem='sync' if mode=='bypass' else 'nosleep';candidate=json.loads((p/('sync-probe-build.json' if mode=='bypass' else 'nosleep-build.json')).read_text())['path'];rows=[]
for w in [1280,1920]:
 h={1280:720,1920:1080}[w];gold=None
 for i,tag in enumerate(['baseline','probe','probe','baseline']):
  dll=str(root/'nvngx_dlssnr_sm86_v22.dll') if tag=='baseline' else candidate;out=root/f'v23-{stem}-{tag}-{w}.rgb32';log=p/f'{stem}-{i}-{tag}-{w}.log';args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,dll.replace('/mnt/c/','C:/'),str(w),str(h),'2','50','20',str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
  with log.open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
  assert r.returncode==0,(tag,w,r.returncode);summary=log.read_text().split('SUMMARY')[-1];m={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',summary)};x=np.fromfile(out,np.float32)
  if gold is None:gold=x.copy()
  d=x.astype(float)-gold;diff=int(np.count_nonzero(x.view(np.uint32)!=gold.view(np.uint32)));mse=float(np.mean(d*d));rows.append({'width':w,'tag':tag,'index':i,'metrics':m,'bitdiff':diff,'maxabs':float(np.max(np.abs(d))),'psnr_db':None if not mse else float(-10*np.log10(mse)),'sha256':hashlib.sha256(x.tobytes()).hexdigest(),'warmup':50,'iterations':20,'diagnostic_only':True});out.unlink();(p/f'{stem}-probe-bench.json').write_text(json.dumps(rows,indent=2)+'\n');print(w,tag,m.get('gpu_median_ms'),'bitdiff',diff,flush=True)
