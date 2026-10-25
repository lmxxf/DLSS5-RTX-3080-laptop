#!/usr/bin/env python3
from pathlib import Path
import argparse,subprocess,os,datetime,json,hashlib
root=Path(__file__).resolve().parents[1];phase=root/'phase13'
p=argparse.ArgumentParser();p.add_argument('variant');p.add_argument('--width',type=int,choices=[1280,1600,1920]);p.add_argument('--modules',type=Path);p.add_argument('--warmup',type=int,default=50);p.add_argument('--iterations',type=int,default=80);a=p.parse_args()
modules=a.modules or (root/'phase12/artifacts/selected/modules' if a.variant.startswith('baseline') else phase/'artifacts'/a.variant/'modules')
expected=json.loads((phase/'phase12-baseline-manifest.json').read_text())
baseline=root/'phase12/artifacts/selected/modules'
assert all(hashlib.sha256((baseline/n).read_bytes()).hexdigest()==h for n,h in expected.items()), 'Phase12 baseline mutated'
assert len(list(modules.glob('*.hsaco')))==40, 'Rebuild/compose the full candidate module set before benching'
(phase/'artifacts/outputs').mkdir(parents=True,exist_ok=True)
for w in ([a.width] if a.width else [1280,1600,1920]):
 env=os.environ.copy();env.update(DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_BENCH_PROFILE='1',DLSS5_LAB_C256_SPLIT='0',DLSS5_LAB_COMPACT_ALL='1',DLSS5_BENCH_DUMP=str(phase/'artifacts/outputs'/a.variant))
 env.pop('DLSS5_BENCH_SYNC_KERNELS',None)
 begin=datetime.datetime.now().isoformat();path=phase/(a.variant+f'-{w}.log')
 assert not path.exists(), 'Use a new variant/run name; refusing to overwrite '+str(path)
 with path.open('w') as f:r=subprocess.run([str(phase/'artifacts/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(modules),str(a.warmup),str(a.iterations)],env=env,stdout=f,stderr=subprocess.STDOUT)
 end=datetime.datetime.now().isoformat()
 (phase/(a.variant+f'-{w}-run.json')).write_text(json.dumps({'variant':a.variant,'processing_width':w,'modules':str(modules),'warmup':a.warmup,'iterations':a.iterations,'begin':begin,'end':end,'returncode':r.returncode,'module_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(modules.glob('*.hsaco'))}},indent=2)+'\n')
 assert r.returncode==0,path
 for line in path.read_text().splitlines():
  if any(k in line for k in ['GPU  (ms)','Wall (ms)','Validity :','PROFILE_TOTAL']):print(a.variant,w,line,flush=True)
