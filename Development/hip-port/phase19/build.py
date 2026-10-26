from pathlib import Path
import sys,json,hashlib,copy,subprocess
from concurrent.futures import ProcessPoolExecutor
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
base=r/'phase18/artifacts/selected/modules';src=r/'hip';manifest=json.loads((r/'phase18/selected-modules.sha256.json').read_text())
def job(mask):
 out=p/f'artifacts/m{mask}/modules';out.mkdir(parents=True,exist_ok=True)
 for f in base.iterdir():
  if f.stem=='c64-wave2-fast' or (f.suffix not in ['.hsaco','.ptx'] and not f.name.startswith('AMPERE_')):continue
  dst=out/f.name
  if not dst.exists():dst.symlink_to(f.resolve())
 (out/'AMPERE_WEIGHTS_W19').write_text(str(mask)+'\n');b.PHASE19_WAVE_HALF=mask
 mod=copy.deepcopy(next(m for m in b.parse_ps1_modules(str(src/'build-modules.ps1')) if m['name']=='c64-wave2-fast'))
 res=b.compile_one_module(mod,str(src),str(out),str(src/'sm86_compat.h'),str(src/'ptx2cubin'));print(mask,res[:3],flush=True);assert res[1],res
 return str(mask),{'modules':str(out),'result':res}
if __name__=='__main__':
 for n,h in manifest.items():assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h
 with ProcessPoolExecutor(max_workers=2) as ex:rows=dict(ex.map(job,[1,3]))
 (p/'builds.json').write_text(json.dumps(rows,indent=2)+'\n')
 subprocess.run(['c++','-O3','-std=c++17',str(r/'Development/HIP/benchmark_cuda_nn.cpp'),'-ldl','-o',str(p/'artifacts/benchmark_cuda_nn')],check=True)
