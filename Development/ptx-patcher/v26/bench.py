from pathlib import Path
import json,subprocess,datetime,hashlib,re,sys,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');outdir=root/'ptx-v26-bench';outdir.mkdir(exist_ok=True);core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
variants={'v1':{'path':str(root/'backups/20261026-v020/production/nvngx_dlssnr_sm86_fast.dll')},'baseline':{'path':str(root/'nvngx_dlssnr_sm86_v24.dll')},'lowhigh':json.loads((p/'build.json').read_text())};rows=[]
for v,d in variants.items():d['sha256']=hashlib.sha256(Path(d['path']).read_bytes()).hexdigest()
assert variants['v1']['sha256']=='3f934a0a9d2196e06e8a2cf772fca3d6da9686fd79a58261fc3b37d1a0ce051a';assert variants['baseline']['sha256']=='1687087ea3b4ae03cdacbd5c1f3cec5142f4b23d7d5c8ead95d502679f91d256'

def run(name,v,w,warm=50,it=80):
 h={1280:720,1600:900,1920:1080}[w];dll=Path(variants[v]['path']);out=outdir/f'{name}-{v}-{w}.rgb32';log=p/f'{name}-{v}-{w}.log';assert not log.exists()
 args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,str(dll).replace('/mnt/c/','C:/'),str(w),str(h),'2',str(warm),str(it),str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 begin=datetime.datetime.now().isoformat()
 with log.open('w') as f:r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 assert r.returncode==0,(name,r.returncode);summary=log.read_text().split('SUMMARY')[-1];metrics={k:float(v) for k,v in re.findall(r'(\w+)=([-+\d.eE]+)',summary)};a=np.fromfile(out,np.float32);assert len(a)==w*h*3 and np.isfinite(a).all() and metrics['nonfinite']==0
 def compare(f):
  b=np.fromfile(f,np.float32);d=a.astype(np.float64)-b;mse=float(np.mean(d*d));return {'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'rmse':float(np.sqrt(mse)),'maxabs':float(np.max(abs(d))),'psnr_db':None if not mse else float(-10*np.log10(mse))}
 own=outdir/f'gold-{v}-{warm}-{it}-{w}.rgb32'
 repeat=compare(own) if own.exists() else None
 if repeat:assert repeat['bitdiff']==0,('non-deterministic',name,v,w,repeat)
 quality={'repeat':repeat,'sha256':hashlib.sha256(a.tobytes()).hexdigest(),'vs':{}}
 for ref in ['baseline','v1']:
  f=outdir/f'gold-{ref}-{warm}-{it}-{w}.rgb32'
  if f.exists():quality['vs'][ref]=compare(f)
 if w==1280:
  im=a.reshape(h,w,3);d=(im[:,:,0]-im[:,:,1]).mean(axis=1);hf=d[1:-1]-.5*(d[:-2]+d[2:]);quality|={'sky_sign_changes':int(np.count_nonzero(np.diff(np.sign(d)))),'sky_hf_rms':float(np.sqrt(np.mean(hf**2)))}
 if not own.exists():out.replace(own)
 else:out.unlink()
 row={'name':name,'variant':v,'width':w,'height':h,'warmup':warm,'iterations':it,'begin':begin,'end':datetime.datetime.now().isoformat(),'metrics':metrics,'quality':quality,'args':args,'DLL_sha256':variants[v]['sha256']};rows.append(row);(p/('smoke.json' if sys.argv[1]=='smoke' else 'bench.json')).write_text(json.dumps(rows,indent=2)+'\n');print(name,v,w,metrics.get('gpu_median_ms'),{k:round(t['psnr_db'],4) if t['psnr_db'] is not None else 'inf' for k,t in quality['vs'].items()},'sky',quality.get('sky_sign_changes'),flush=True)

if __name__=='__main__':
 if sys.argv[1]=='smoke':
  for w in [1280,1600,1920]:
   for v in ['v1','baseline','lowhigh']:run('smoke',v,w,1,1)
 else:
  for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
   for w in widths:
    if direction=='forward':run('reference-'+direction,'v1',w)
    order=['baseline','lowhigh','lowhigh','baseline'] if direction=='forward' else ['lowhigh','baseline','baseline','lowhigh']
    for j,v in enumerate(order):run(f'{direction}-{j}',v,w)
    if direction=='reverse':run('reference-'+direction,'v1',w)
