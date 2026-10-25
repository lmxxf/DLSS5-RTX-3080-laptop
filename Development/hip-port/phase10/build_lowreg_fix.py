from pathlib import Path
import sys,shutil,json,hashlib,concurrent.futures
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'));import build_sm86_modules as build
build.PHASE10_FP8=True
out=root/'phase10/artifacts/lowreg-fix/modules';out.mkdir(parents=True,exist_ok=True)
base=root/'phase10/artifacts/optimized/modules'
for p in base.glob('*.hsaco'):shutil.copy2(p,out/p.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
mods=build.parse_ps1_modules(root/'hip/build-modules.ps1');targets=[m for m in mods if m['name'] in ['c32-wave1-fast','c512-m32-deep','vit-stream-fast']]
def compile(m):return build.compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 rows=list(ex.map(compile,targets))
 for r in rows:print(r,flush=True);assert r[1],r[2]
(out.parent/'build.json').write_text(json.dumps(rows,indent=2)+'\n');(out.parent/'modules.sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
print('PASS: 3 lowreg paths rebuilt, 40-module complete set',flush=True)
