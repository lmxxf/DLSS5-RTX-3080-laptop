from pathlib import Path
import subprocess,shutil
r=Path(__file__).resolve().parents[1];p=r/'phase14';out=p/'artifacts/host';out.mkdir(exist_ok=True)
for f in (r/'Development/HIP').glob('*.h'):shutil.copy2(f,out/f.name)
s=(r/'Development/HIP/hip_reference_network.h').read_text().replace('"../../src/','"'+str((r/'src').resolve())+'/')
(out/'hip_reference_network.h').write_text(s);shutil.copy2(r/'Development/HIP/benchmark_cuda_nn.cpp',out/'benchmark_cuda_nn.cpp')
subprocess.run(['c++','-O3','-std=c++17',str(r/'Development/HIP/benchmark_cuda_nn.cpp'),'-ldl','-o',str(p/'artifacts/benchmark_cuda_nn')],check=True)
