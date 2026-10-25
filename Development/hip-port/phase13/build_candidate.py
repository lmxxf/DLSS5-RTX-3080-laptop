from pathlib import Path
import argparse,sys,shutil,hashlib,json
r=Path(__file__).resolve().parents[1];p=r/'phase13';sys.path.insert(0,str(r/'hip'))
import build_sm86_modules as b
from transform import transform
parser=argparse.ArgumentParser();parser.add_argument('site',choices=['prefix','post','both']);a=parser.parse_args()
base=r/'phase12/artifacts/selected/modules';expected=json.loads((p/'phase12-baseline-manifest.json').read_text());assert all(hashlib.sha256((base/n).read_bytes()).hexdigest()==h for n,h in expected.items())
out=p/f'artifacts/{a.site}/modules';out.mkdir(parents=True,exist_ok=True)
for f in base.glob('*.hsaco'):shutil.copy2(f,out/f.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
orig=b.pack_c32_av;b.pack_c32_av=lambda s:transform(orig(s),a.site)
m=next(m for m in b.parse_ps1_modules(r/'hip/build-modules.ps1') if m['name']=='c32-wave1-fast');m['defines']+=['SM86_PHASE13_'+a.site.upper()+' 1','SM86_PHASE13_HASH 0x'+hashlib.sha256((p/'transform.py').read_bytes()).hexdigest()[:8]]
res=b.compile_one_module(m,str(r/'hip'),str(out),str(r/'hip/sm86_compat.h'),str(r/'hip/ptx2cubin'));print(res,flush=True);assert res[1],res[2]
(out.parent/'modules.sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
