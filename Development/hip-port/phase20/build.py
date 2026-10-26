from pathlib import Path
import json,sys,hashlib,shutil
from concurrent.futures import ProcessPoolExecutor
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
base=r/'phase19/artifacts/selected/modules';out=p/'artifacts/candidate/modules';out.mkdir(parents=True,exist_ok=True)
def job(name):
 b.PHASE20_HALF_ACT=True;src=r/'hip';mod=next(x for x in b.parse_ps1_modules(str(src/'build-modules.ps1')) if x['name']==name);res=b.compile_one_module(mod,str(src),str(out),str(src/'sm86_compat.h'),str(src/'ptx2cubin'));print(name,res[:3],flush=True);return res
if __name__=='__main__':
 manifest=json.loads((r/'phase19/selected-modules.sha256.json').read_text())
 for f in base.iterdir():
  if f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_'):continue
  if f.name in manifest:assert hashlib.sha256(f.read_bytes()).hexdigest()==manifest[f.name]
  if f.stem in ['c32-wave1-fast','c64-wave2-fast']:continue
  if not(out/f.name).exists():(out/f.name).symlink_to(f.resolve())
 with ProcessPoolExecutor(max_workers=2) as ex:rows=list(ex.map(job,['c32-wave1-fast','c64-wave2-fast']))
 (p/'builds.json').write_text(json.dumps(rows,indent=2)+'\n');assert all(x[1] for x in rows)
 shutil.copy2(r/'phase19/artifacts/benchmark_cuda_nn',p/'artifacts/benchmark_cuda_nn')
