from pathlib import Path
import sys,copy,json,hashlib,os
from concurrent.futures import ProcessPoolExecutor,as_completed
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
base=r/'phase17/artifacts/selected/modules';manifest=json.loads((r/'phase17/selected-modules.sha256.json').read_text())
def job(site):
 name='c32-wave1-fast' if site.startswith('c32-') else 'c64-wave2-fast';out=p/'artifacts'/site/'modules';out.mkdir(parents=True,exist_ok=True)
 for f in base.iterdir():
  if f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_'):continue
  if f.stem==name:continue
  dst=out/f.name
  if not dst.exists():dst.symlink_to(f.resolve())
 b.PHASE18_SITES={name:[site]};b.PHASE18_C256_CAP=None;b.PHASE18_QKV_MASK=None
 mod=copy.deepcopy(next(m for m in b.parse_ps1_modules(str(r/'hip/build-modules.ps1')) if m['name']==name))
 res=b.compile_one_module(mod,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));print(site,res[:3],flush=True);return site,{'module':name,'result':res,'modules':str(out)}
if __name__=='__main__':
 for n,h in manifest.items():assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h
 rows={}
 with ProcessPoolExecutor(max_workers=3) as ex:
  for f in as_completed([ex.submit(job,s) for s in ['contract','result','v','av','byteout','c32-prefix','c32-v']]):
   n,row=f.result();rows[n]=row
 (p/'site-builds.json').write_text(json.dumps(rows,indent=2)+'\n');assert all(r['result'][1] for r in rows.values())
