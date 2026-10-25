from pathlib import Path
import subprocess,os,json
r=Path(__file__).resolve().parents[1];p=r/'phase13'
rows=[]
for w in [1280,1600,1920]:
 for kind in ['phase12','f32']:
  out=p/f'artifacts/traces/{kind}-{w}';out.mkdir(parents=True,exist_ok=True)
  env=os.environ.copy();env.update(DLSS5_PHASE13_TRACE=str(out),DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1' if kind=='phase12' else '0',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='1' if kind=='phase12' else '0',DLSS5_LAB_C256_SPLIT='0' if kind=='phase12' or w==1920 else '1',DLSS5_BENCH_DUMP=str(p/f'artifacts/outputs/trace-{kind}'))
  mods=r/('phase12/artifacts/selected/modules' if kind=='phase12' else 'phase1/artifacts/f32-modules')
  log=p/f'trace-{kind}-{w}.log'
  with log.open('w') as f:proc=subprocess.run([str(p/'artifacts/diagnostic-host/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(mods),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
  print(kind,w,proc.returncode,flush=True);assert proc.returncode==0
  rows.append({'kind':kind,'width':w,'flags':{k:v for k,v in env.items() if k.startswith('DLSS5_')},'modules':str(mods),'returncode':proc.returncode})
(p/'trace-runs.json').write_text(json.dumps(rows,indent=2)+'\n')
