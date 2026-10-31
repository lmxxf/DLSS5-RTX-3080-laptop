"""Serial runner: complete process text is embedded in aggregate JSON, never .log fragments."""
from pathlib import Path
import json,subprocess,datetime,hashlib,re,sys,numpy as np
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');outdir=root/'ptx-v39-bench';outdir.mkdir(exist_ok=True)
core=r'C:\Windows\System32\DriverStore\FileRepository\nvtfi.inf_amd64_039ce3d14607c6bc\_nvngx.dll'
cs=json.loads((p/'candidates.json').read_text());variants={'baseline':{'path':str(root/'nvngx_dlssnr_sm86_v38.dll'),'approximate':False}}|{k:v for k,v in cs.items() if k!='baseline'};stage=sys.argv[1] if len(sys.argv)>1 else 'smoke';joint_run=stage=='joint';stage='timed' if joint_run else stage;rows=json.loads((p/'bench.json').read_text()) if joint_run else []
def run(name,v,w,warm,it):
 h={1280:720,1600:900,1920:1080}[w];dll=Path(variants[v]['path']);out=outdir/f'{stage}-{len(rows):04}-{v}-{w}.rgb32';args=[str(root/'nvngx.dll_runner/bench_sky.exe'),core,str(dll).replace('/mnt/c/','C:/'),str(w),str(h),'2',str(warm),str(it),str(out).replace('/mnt/c/','C:/')]+(['sky'] if w==1280 else [])
 start=datetime.datetime.now().isoformat();result=subprocess.run(args,capture_output=True,text=True,timeout=180);end=datetime.datetime.now().isoformat();s=result.stdout+result.stderr;metrics={k:float(x) for k,x in re.findall(r'(\w+)=([-+\d.eE]+)',s.split('SUMMARY')[-1])};assert result.returncode==0,(args,result.returncode,s)
 a=np.fromfile(out,np.float32);assert len(a)==w*h*3;gold=outdir/f'gold-{warm}-{it}-{w}.rgb32'
 if not gold.exists():assert v=='baseline';out.replace(gold)
 b=np.fromfile(gold,np.float32);d=a.astype(np.float64)-b;finite=bool(np.isfinite(a).all());mse=float(np.mean(d*d));q={'bitdiff':int(np.count_nonzero(a.view(np.uint32)!=b.view(np.uint32))),'maxabs':float(np.max(abs(d))) if finite else None,'PSNR_db':float(-10*np.log10(mse)) if mse and np.isfinite(mse) else None,'nonfinite':int(np.count_nonzero(~np.isfinite(a))),'sha256':hashlib.sha256(a.tobytes()).hexdigest()}
 if w==1280:
  im=a.reshape(h,w,3);rg=(im[:,:,0]-im[:,:,1]).mean(axis=1);hf=rg[1:-1]-.5*(rg[:-2]+rg[2:]);q.update(sky_sign_changes=int(np.count_nonzero(np.diff(np.sign(rg)))) if finite else None,sky_hf_rms=float(np.sqrt(np.mean(hf*hf))) if finite else None)
 approximate=variants[v].get('approximate',False);gate=json.loads((p/'acceptance.json').read_text())['approximate'];q['quality_pass']=finite and (q['bitdiff']==0 if not approximate else q['maxabs']<=gate['maxabs_max'] and (q['PSNR_db'] is None or q['PSNR_db']>=gate['PSNR_min_db']) and (w!=1280 or q['sky_sign_changes']==0))
 row={'name':name,'variant':v,'dll_sha256':hashlib.sha256(dll.read_bytes()).hexdigest(),'width':w,'height':h,'warmup':warm,'iterations':it,'begin':start,'end':end,'metrics':metrics,'quality':q,'args':args,'returncode':result.returncode,'process_output':s};rows.append(row);(p/(('bench' if stage=='timed' else stage)+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
 if out.exists() and (q['quality_pass'] or approximate):out.unlink()
 print(stage,name,v,w,metrics.get('gpu_median_ms'),q['bitdiff'],q['PSNR_db'],flush=True)
 assert finite and metrics['nonfinite']==0,(v,q)
 if not approximate:assert q['bitdiff']==0 and q['maxabs']==0,(v,q)
if __name__=='__main__':
 candidates=json.loads((p/'timing-candidates.json').read_text()) if stage!='smoke' and (p/'timing-candidates.json').exists() else list(variants)[1:]
 if joint_run:candidates=[json.loads((p/'joint-selection.json').read_text())['joint']]
 if stage=='repeat':candidates=json.loads((p/'repeat-eligible.json').read_text())
 if stage=='smoke':
  for w in [1280,1600,1920]:
   for v in ['baseline']+candidates:run('smoke',v,w,1,1)
 else:
  for direction,widths in [('forward',[1280,1600,1920]),('reverse',[1920,1600,1280])]:
   for w in widths:
    for v in candidates:
     order=['baseline',v,v,'baseline'] if direction=='forward' else [v,'baseline','baseline',v]
     for j,version in enumerate(order):run(f'{direction}-{v}-{j}',version,w,50,80)
