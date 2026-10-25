from pathlib import Path
import subprocess,os,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase13';rows=[]
for kind in ['phase12','f32']:
 for variant in ['legacy256','forced400']:
  out=p/f'artifacts/attention/{kind}-{variant}';out.mkdir(parents=True,exist_ok=True)
  env=os.environ.copy();env.update(DLSS5_PHASE13_ATTN_TAP=str(out),DLSS5_BENCH_WIDTH='1280',DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1' if kind=='phase12' else '0',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='1' if kind=='phase12' else '0',DLSS5_LAB_C256_SPLIT='0' if kind=='phase12' else '1',DLSS5_BENCH_DUMP=str(p/f'artifacts/outputs/attn-{kind}-{variant}'))
  env.pop('DLSS5_PHASE13_ATTN400',None)
  if variant=='forced400':env['DLSS5_PHASE13_ATTN400']='1'
  mods=r/('phase12/artifacts/selected/modules' if kind=='phase12' else 'phase1/artifacts/f32-modules')
  with (p/f'attn-{kind}-{variant}.log').open('w') as f:res=subprocess.run([str(p/'artifacts/diagnostic-host/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(mods),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
  print(kind,variant,res.returncode,flush=True);assert res.returncode==0
  rows.append({'kind':kind,'variant':variant,'flags':{k:v for k,v in env.items() if k.startswith('DLSS5_')},'modules':str(mods)})
(p/'attention-runs.json').write_text(json.dumps(rows,indent=2)+'\n')
