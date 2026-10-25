"""Use legacy FP8 expression only in bound-limited modules; keep direct-layout pass."""
from pathlib import Path
import sys,shutil,json,hashlib,re
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
phase=root/'phase8';out=phase/'artifacts/lowreg/modules';out.mkdir(parents=True,exist_ok=True)
source=out.parent/'source';source.mkdir(exist_ok=True)
for p in (root/'hip').iterdir():
 if p.is_file() and p.suffix in ('.h','.hip','.inc','.py','.ps1'):shutil.copy2(p,source/p.name)
shutil.copy2(root/'Development/HIP/swin_persistent_types.h',source/'swin_persistent_types.h')
p=source/'sm86_compat.h';s=p.read_text();a=s.index('SM86_DEV sm86_u32 sm86_f32_to_e4m3_byte(float x) {');b=s.index('\n}',a)+2
old=(root/'phase7/probe.hip').read_text();old=old[old.index('SM86_DEV U old_fp8'):old.index('\nSM86_DEV float old_med')].replace('SM86_DEV U old_fp8','SM86_DEV sm86_u32 sm86_f32_to_e4m3_byte').replace('U b=','sm86_u32 b=').replace('bit_cast(U,','bit_cast(sm86_u32,').replace(';U sub=', ';sm86_u32 sub=')
p.write_text(s[:a]+old+s[b:])
mods=build.parse_ps1_modules(source/'build-modules.ps1');results=[]
for name in ['vit-stream-fast','c512-m32-deep']:
 mod=next(m for m in mods if m['name']==name)
 r=build.compile_one_module(mod,str(source),str(out),str(p),str(root/'hip/ptx2cubin'));print(r,flush=True);results.append(r);assert r[1],r[2]
(out.parent/'build.json').write_text(json.dumps({'compiled':results,'purpose':'Legacy C++ FP8 expression with Phase7 clamp/LOP3 and Phase8 bounds; other modules refreshed from full before benchmark.'},indent=2)+'\n')
