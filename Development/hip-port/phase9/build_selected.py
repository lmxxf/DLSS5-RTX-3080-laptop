"""Freeze the complete V build; recompile final C32 policy from default source."""
from pathlib import Path
import sys,shutil,hashlib,json,re
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'));import build_sm86_modules as build
phase=root/'phase9';out=phase/'artifacts/selected/modules';out.mkdir(parents=True,exist_ok=True)
for p in (phase/'artifacts/v-bridge/modules').iterdir():
 if p.suffix in ('.hsaco','.ptx','.cu') or p.name=='AMPERE_WEIGHTS_V2':shutil.copy2(p,out/p.name)
mod=next(m for m in build.parse_ps1_modules(root/'hip/build-modules.ps1') if m['name']=='c32-wave1-fast')
r=build.compile_one_module(mod,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'));print(r,flush=True);assert r[1],r[2]
assert len(list(out.glob('*.hsaco')))==40
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))}
(out.parent/'modules.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out.parent/'build.json').write_text(json.dumps({'parent':'v-bridge full 40/40, 1918 entries, with three shared-Q variants repaired','canonical_recompiled':r,'q_mask':63,'local_fp8_policy':'mapped only; prefix/Up/other kinds retain branchless encode'},indent=2)+'\n')
print('PASS: final default-source C32 policy compiled; 40 final modules, '+str(sum(len(re.findall(r'\.visible\s+\.entry\s+',p.read_text())) for p in out.glob('*.ptx')))+' entries',flush=True)
