from pathlib import Path
import json,subprocess,datetime,hashlib,re,sys,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');outdir=root/'ptx-v25-bench';outdir.mkdir(exist_ok=True)
core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
variants={'baseline':{'path':str(root/'nvngx_dlssnr_sm86_v24.dll')},'hybrid':json.loads((p/'build.json').read_text())};rows=[]
def run(name,v,w,warm=50,it=80):
 h={1280:720,1600:900,1920:1080}[w];dll=Path(variants[v]['path']);out=outdir/f'{name}-{v}-{w}.rgb32';log=p/f'{name}-{v}-{w}.log';assert not log.exists()
 args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,str(dll).replace('/mnt/c/','C:/'),str(w),str(h),'2',str(warm),str(it),str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 begin=datetime.datetime.now().isoformat()
 with log.open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert r.returncode==0,(log,r.returncode)
 s=log.read_text();summary=s.split('SUMMARY')[-1];metrics={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',summary)};assert metrics.get('nonfinite')==0,summary
 a=np.fromfile(out,np.float32);assert len(a)==w*h*3 and np.isfinite(a).all();base=outdir/f'gold-{warm}-{it}-{w}.rgb32'
 if not base.exists():assert v=='baseline';out.replace(base)
 b=np.fromfile(base,np.float32);diff=a.astype(np.float64)-b;bits=int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32)));mse=float(np.mean(diff**2));quality={'bitdiff':bits,'maxabs':float(np.max(np.abs(diff))),'psnr_db':float(-10*np.log10(mse)) if mse else None,'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
 if w==1280:
  im=a.reshape(h,w,3);d=(im[:,:,0]-im[:,:,1]).mean(axis=1);hf=d[1:-1]-.5*(d[:-2]+d[2:]);quality|={'sky_sign_changes':int(np.count_nonzero(np.diff(np.sign(d)))),'sky_hf_rms':float(np.sqrt(np.mean(hf**2)))}
 if out.exists():out.unlink()
 row={'name':name,'variant':v,'width':w,'height':h,'warmup':warm,'iterations':it,'begin':begin,'end':datetime.datetime.now().isoformat(),'metrics':metrics,'quality':quality,'args':args};rows.append(row);(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json')).write_text(json.dumps(rows,indent=2)+'\n');print(name,v,w,metrics.get('gpu_median_ms'),bits,flush=True);assert bits==0,(v,w,quality)
if sys.argv[1]=='smoke':
 for w in [1280,1600,1920]:
  for v in variants:run('smoke',v,w,1,1)
else:
 for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
  for w in widths:
   for v in ['hybrid']:
    order=['baseline',v,v,'baseline'] if direction=='forward' else [v,'baseline','baseline',v]
    for j,version in enumerate(order):run(f'{direction}-{v}-{j}',version,w)
