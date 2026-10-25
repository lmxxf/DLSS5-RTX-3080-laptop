from pathlib import Path
import sys,argparse,shutil,json,hashlib
root=Path(__file__).resolve().parents[1];phase=root/'phase12';sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE12_C32_AV=False
from transform import transform
p=argparse.ArgumentParser();p.add_argument('site',choices=['c32-av','c32-v','wave2-av','wave2-v']);a=p.parse_args()
base=root/'phase11/artifacts/selected/modules';expected=json.loads((phase/'phase11-baseline-manifest.json').read_text());assert all(hashlib.sha256((base/n).read_bytes()).hexdigest()==h for n,h in expected.items())
folder=phase/'artifacts'/a.site;out=folder/'modules';out.mkdir(parents=True,exist_ok=True);name='c32-wave1-fast' if a.site.startswith('c32') else 'c64-wave2-fast'
for p in base.glob('*.hsaco'):
 if p.stem==name and (out/p.name).exists():continue
 shutil.copy2(p,out/p.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
source=folder/'source';source.mkdir(exist_ok=True)
for p in (root/'hip').iterdir():
 if p.is_file() and p.suffix in ('.h','.hip','.inc','.py','.ps1'):shutil.copy2(p,source/p.name)
shutil.copy2(root/'Development/HIP/swin_persistent_types.h',source/'swin_persistent_types.h')
mod=next(m for m in build.parse_ps1_modules(source/'build-modules.ps1') if m['name']==name)
mod['defines']+=['SM86_PHASE12_SITE_'+a.site.replace('-','_').upper()+' 1','SM86_PHASE12_SOURCE 0x'+hashlib.sha256(Path(__file__).with_name('transform.py').read_bytes()).hexdigest()[:8]]
if a.site.startswith('c32'):
 original=build.pack_ffn_half_features;build.pack_ffn_half_features=lambda text:transform(original(text),a.site)
else:
 original=build.phase10_optimize_fp8;build.phase10_optimize_fp8=lambda text:transform(original(text),a.site)
r=build.compile_one_module(mod,str(source),str(out),str(source/'sm86_compat.h'),str(root/'hip/ptx2cubin'));print(r,flush=True);assert r[1],r[2]
(folder/'build.json').write_text(json.dumps({'site':a.site,'changed_module':r,'parent':str(base)},indent=2)+'\n');(folder/'modules.sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
