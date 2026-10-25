from pathlib import Path
import subprocess,os,json,numpy as np,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase13';rows=[]
for w in [1600,1920]:
 env=os.environ.copy();env.update(DLSS5_PHASE13_ATTN400='1',DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='0',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='0',DLSS5_LAB_C256_SPLIT='0' if w==1920 else '1',DLSS5_BENCH_DUMP=str(p/'artifacts/outputs/f32-calibrated'))
 log=p/f'f32-calibrate-{w}.log'
 with log.open('w') as f:res=subprocess.run([str(p/'artifacts/diagnostic-host/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(r/'phase1/artifacts/f32-modules'),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
 assert res.returncode==0
 a=np.fromfile(p/f'artifacts/outputs/f32-calibrated-{w}.rgb32',np.uint32);b=np.fromfile(r/f'phase1/artifacts/outputs/f32-{w}.rgb32',np.uint32);diff=int(np.count_nonzero(a!=b));assert diff==0;rows.append({'width':w,'gold_bitdiff':diff})
(p/'f32-calibration.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
