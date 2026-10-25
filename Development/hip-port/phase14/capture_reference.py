from pathlib import Path
import subprocess,os,json,numpy as np,hashlib
from reference import attention,decode
r=Path(__file__).resolve().parents[1];p=r/'phase14';folder=p/'artifacts/gold-capture';folder.mkdir(exist_ok=True)
env=os.environ.copy();env.update(DLSS5_PHASE14_CAPTURE_ATTN=str(folder),DLSS5_BENCH_WIDTH='1280',DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='0',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='0',DLSS5_LAB_C256_SPLIT='1',DLSS5_LAB_ATTN400='0',DLSS5_BENCH_DUMP=str(p/'artifacts/outputs/gold-capture'))
with (p/'gold-capture.log').open('w') as f:ret=subprocess.run([str(p/'artifacts/capture-host/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(p/'artifacts/f32-fixed/modules'),'0','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
assert ret.returncode==0
assert np.array_equal(np.fromfile(p/'artifacts/outputs/gold-capture-1280.rgb32',np.uint32),np.fromfile(p/'artifacts/outputs/gold-f32-1280.rgb32',np.uint32))
rows=[]
for i in range(8):
 qkv=np.fromfile(folder/f'{i}-qkv.bin',np.uint8);got=np.fromfile(folder/f'{i}-av.bin',np.uint8).reshape(240,1024);ref=attention(qkv);delta=decode(got).astype(float)-decode(ref)
 row={'block':31+i,'bytes':got.size,'byte_diff':int(np.count_nonzero(got!=ref)),'maxabs':float(np.max(abs(delta))),'rmse':float(np.sqrt(np.mean(delta*delta))),'reserved_nan_inputs':int(np.count_nonzero((qkv&127)==127)),'qkv_sha256':hashlib.sha256(qkv.tobytes()).hexdigest(),'av_sha256':hashlib.sha256(got.tobytes()).hexdigest()};rows.append(row);print(row,flush=True)
(p/'gold-cpu-results.json').write_text(json.dumps({'capture_whole_output_bitdiff':0,'rows':rows,'CPU_rounding':'Double matrix accumulation thenF32; exact division roundedF32. GPU usesF32 TensorCore partial accumulation and rcp.approx.'},indent=2)+'\n')
