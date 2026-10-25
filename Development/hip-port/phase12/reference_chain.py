"""Calibrate the current Host+Phase1 F32 modules against BOTH existing golds before720."""
from pathlib import Path
import os,subprocess,json,hashlib,numpy as np
root=Path(__file__).resolve().parents[1];phase=root/'phase12';modules=root/'phase1/artifacts/f32-modules';expected=json.loads((root/'phase1/f32-modules.sha256.json').read_text());assert all(hashlib.sha256((modules/n).read_bytes()).hexdigest()==h for n,h in expected.items())
rows=[]
for w in [1920,1600,1280]:
 env=os.environ.copy();env.update(DLSS5_BENCH_WIDTH=str(w),DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='0',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='0',DLSS5_LAB_C256_SPLIT='0' if w==1920 else '1',DLSS5_BENCH_DUMP=str(phase/'artifacts/outputs/f32-paired'))
 for k in ['DLSS5_BENCH_PROFILE','DLSS5_BENCH_SYNC_KERNELS']:env.pop(k,None)
 log=phase/f'f32-current-paired-{w}.log'
 with log.open('w') as f:r=subprocess.run([str(phase/'artifacts/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(modules),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
 row={'width':w,'returncode':r.returncode,'flags':{k:env[k] for k in ['DLSS5_AMPERE_WEIGHTS','DLSS5_LAB_COMPACT_ALL','DLSS5_LAB_C256_SPLIT']}}
 if r.returncode:rows.append(row);break
 out=phase/f'artifacts/outputs/f32-paired-{w}.rgb32';a=np.fromfile(out,np.uint32)
 if w!=1280:
  g=np.fromfile(root/f'phase1/artifacts/outputs/f32-{w}.rgb32',np.uint32);row['gold_bitdiff']=int(np.count_nonzero(a!=g));rows.append(row)
  if row['gold_bitdiff']:break
 else:
  row['candidate_720_reference_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();rows.append(row)
(phase/'f32-current-paired-status.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
