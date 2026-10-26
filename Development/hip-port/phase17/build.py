from pathlib import Path
import sys,json,hashlib,shutil,subprocess
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));import build_sm86_modules as b
src=r/'hip';base=r/'phase16/artifacts/tail/modules';out=p/'artifacts/candidate/modules';out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((r/'phase16/selected-modules.sha256.json').read_text())
for n,h in manifest.items():
 assert hashlib.sha256((base/n).read_bytes()).hexdigest()==h,(n,h)
 if not(out/n).exists():shutil.copy2(base/n,out/n)
 if n!="c32-wave1-fast.hsaco":assert hashlib.sha256((out/n).read_bytes()).hexdigest()==h,(n,"existing output changed")
 for ext in ['.ptx']:
  srcfile=(base/n).with_suffix(ext);destfile=(out/n).with_suffix(ext)
  if srcfile.exists() and not destfile.exists():shutil.copy2(srcfile,destfile)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2');(out/'AMPERE_WEIGHTS_V3').write_text('C32_W16_F16_APPEND_V1\n')
b.PHASE17_C32_HALF=True
mod=next(m for m in b.parse_ps1_modules(str(src/'build-modules.ps1')) if m['name']=='c32-wave1-fast')
result=b.compile_one_module(mod,str(src),str(out),str(src/'sm86_compat.h'),str(src/'ptx2cubin'));(p/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True);assert result[1]
# Same source Host supports both the unchanged V2 and V3 namespaces.
subprocess.run(['c++','-O3','-std=c++17',str(r/'Development/HIP/benchmark_cuda_nn.cpp'),'-ldl','-o',str(p/'artifacts/benchmark_cuda_nn')],check=True)
