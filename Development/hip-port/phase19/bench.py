from pathlib import Path
import argparse,subprocess,os,datetime,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase19';a=argparse.ArgumentParser();a.add_argument('variant');a.add_argument('--width',type=int,choices=[1280,1600,1920]);a.add_argument('--modules',type=Path);a.add_argument('--cap',type=int,choices=[256,400],default=None);a.add_argument('--f32',action='store_true');a.add_argument('--warmup',type=int,default=50);a.add_argument('--iterations',type=int,default=80);a=a.parse_args()
base=r/'phase18/artifacts/selected/modules';expected=json.loads((r/'phase18/selected-modules.sha256.json').read_text());assert all(hashlib.sha256((base/n).read_bytes()).hexdigest()==h for n,h in expected.items())
modules=a.modules or (base if a.variant.startswith('baseline') else p/'artifacts/selected/modules');assert len(list(modules.glob('*.hsaco')))==40
(p/'artifacts/outputs').mkdir(exist_ok=True)
for w in ([a.width] if a.width else [1280,1600,1920]):
 log=p/f'{a.variant}-{w}.log';assert not log.exists(),str(log)+' already exists'
 env=os.environ.copy();env['DLSS5_AMPERE_C32_F16']='1' if (modules/'AMPERE_WEIGHTS_V3').exists() else '0';env.update(DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='0' if a.f32 else '1',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='0' if a.f32 else '1',DLSS5_LAB_C256_SPLIT='1' if a.f32 and w!=1920 else '0',DLSS5_BENCH_PROFILE='1',DLSS5_BENCH_DUMP=str(p/'artifacts/outputs'/a.variant))
 for k in ['DLSS5_BENCH_SYNC_KERNELS','DLSS5_PHASE13_ATTN400','DLSS5_PHASE13_TRACE','DLSS5_PHASE13_CLOCK','DLSS5_PHASE14_CAPTURE_ATTN']:env.pop(k,None)
 if a.cap is None:env.pop('DLSS5_LAB_ATTN400',None)
 else:env['DLSS5_LAB_ATTN400']='1' if a.cap==400 else '0'
 start=datetime.datetime.now().isoformat()
 with log.open('w') as f:ret=subprocess.run([str(p/'artifacts/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(modules),str(a.warmup),str(a.iterations)],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90)
 end=datetime.datetime.now().isoformat()
 row={'variant':a.variant,'width':w,'modules':str(modules),'cap':a.cap or 400,'cap_forced':a.cap is not None,'host_sha256':hashlib.sha256((p/'artifacts/benchmark_cuda_nn').read_bytes()).hexdigest(),'f32':a.f32,'warmup':a.warmup,'iterations':a.iterations,'begin':start,'end':end,'returncode':ret.returncode,'flags':{k:v for k,v in env.items() if k.startswith('DLSS5_')},'module_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(modules.glob('*.hsaco'))}}
 (p/f'{a.variant}-{w}-run.json').write_text(json.dumps(row,indent=2)+'\n');assert ret.returncode==0,log
 for line in log.read_text().splitlines():
  if any(s in line for s in ['Validity :','GPU  (ms)','Wall (ms)','PROFILE_TOTAL']):print(a.variant,w,line,flush=True)
