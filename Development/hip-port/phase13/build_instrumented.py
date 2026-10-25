from pathlib import Path
import sys,shutil,json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase13';sys.path.insert(0,str(r/'hip'))
import build_sm86_modules as b
from instrument import instrument,HELPER
base=r/'phase12/artifacts/selected/modules';out=p/'artifacts/instrumented/modules';out.mkdir(parents=True,exist_ok=True)
for f in base.glob('*.hsaco'):shutil.copy2(f,out/f.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
orig=b.pack_c32_av
b.pack_c32_av=lambda s: instrument(orig(s)).replace('using cw_h2=',HELPER+'\nusing cw_h2=',1)
m=next(m for m in b.parse_ps1_modules(r/'hip/build-modules.ps1') if m['name']=='c32-wave1-fast')
m['defines']+=['SM86_PHASE13_CLOCK 1','SM86_PHASE13_CLOCK_HASH 0x'+hashlib.sha256((p/'instrument.py').read_bytes()).hexdigest()[:8]]
res=b.compile_one_module(m,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));print(res,flush=True);assert res[1],res[2]
(p/'instrumented-build.json').write_text(json.dumps({'result':res,'instrument_sha256':hashlib.sha256((p/'instrument.py').read_bytes()).hexdigest()},indent=2)+'\n')
