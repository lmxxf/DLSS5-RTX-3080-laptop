from pathlib import Path
import subprocess,os
r=Path(__file__).resolve().parents[1];p=r/'phase13';out=p/'artifacts/clocks-steady';out.mkdir(exist_ok=True)
env=os.environ.copy();env.update(DLSS5_PHASE13_CLOCK=str(out),DLSS5_PHASE13_CLOCK_SKIP='50',DLSS5_BENCH_WIDTH='1920',DLSS5_BENCH_GRAPH='0',DLSS5_AMPERE_WEIGHTS='1',DLSS5_BENCH_SMALL_ONLY='1',DLSS5_LAB_COMPACT_ALL='1',DLSS5_LAB_C256_SPLIT='0',DLSS5_BENCH_DUMP=str(p/'artifacts/outputs/clock-steady'))
with (p/'clock-steady-1920.log').open('w') as f:res=subprocess.run([str(p/'artifacts/diagnostic-host/benchmark_cuda_nn'),'/home/lmxxf/work/dlss5-assets/native-game-tiled-assets',str(p/'artifacts/instrumented/modules'),'50','1'],env=env,stdout=f,stderr=subprocess.STDOUT)
assert res.returncode==0
subprocess.run(['python3',str(p/'analyze_clocks.py')],check=True)
