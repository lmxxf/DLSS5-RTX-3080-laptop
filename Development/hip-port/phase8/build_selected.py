"""Compile the final three changed modules; preserve the full-build other 37."""
from pathlib import Path
import sys,shutil,json,hashlib
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
phase=root/'phase8';out=phase/'artifacts/selected/modules';out.mkdir(parents=True,exist_ok=True)
for p in (phase/'artifacts/full/modules').iterdir():
 if p.suffix in ('.hsaco','.ptx','.cu') or p.name=='AMPERE_WEIGHTS_V2':shutil.copy2(p,out/p.name)
mods=build.parse_ps1_modules(root/'hip/build-modules.ps1');results=[]
for name in ['vit-stream-fast','c512-m32-deep','c32-wave1-fast']:
 mod=next(m for m in mods if m['name']==name)
 r=build.compile_one_module(mod,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));print(r,flush=True);assert r[1],r[2];results.append(r)
assert len(list(out.glob('*.hsaco')))==40
(out.parent/'build.json').write_text(json.dumps({'parent':'full (40/40 compiled)','canonical_recompiled':results},indent=2)+'\n')
(out.parent/'modules.sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
print('PASS: final 40 modules; three fixes compiled from default source.',flush=True)
