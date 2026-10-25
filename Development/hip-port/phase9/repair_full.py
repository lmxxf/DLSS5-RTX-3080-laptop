from pathlib import Path
import sys,concurrent.futures,re
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as b
out=root/'phase9/artifacts/v-bridge/modules';mods=b.parse_ps1_modules(root/'hip/build-modules.ps1');missing=[m for m in mods if not (out/(m['name']+'.hsaco')).exists()]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
 for r in ex.map(lambda m:b.compile_one_module(m,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin')),missing):print(r,flush=True);assert r[1],r[2]
assert len(list(out.glob('*.hsaco')))==40
(out/'AMPERE_WEIGHTS_V2').write_text('CPU Ampere FP8 tiles; paired Phase-2 modules\n')
print('SUMMARY: repaired 40/40 modules; entries='+str(sum(len(re.findall(r'\.visible\s+\.entry\s+',p.read_text())) for p in out.glob('*.ptx'))),flush=True)
