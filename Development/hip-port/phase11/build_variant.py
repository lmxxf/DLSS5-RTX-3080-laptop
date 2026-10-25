from pathlib import Path
import sys,shutil,json,hashlib,argparse
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE11_HALF_FEATURE_PACK=False
from transform import fold_ffn_half_store,pack_ffn_half_features
p=argparse.ArgumentParser();p.add_argument('variant',choices=['half-store','half-feature-pack']);p.add_argument('--keep-ir',action='store_true');a=p.parse_args()
folder=root/'phase11/artifacts'/a.variant;out=folder/'modules';out.mkdir(parents=True,exist_ok=True)
base=root/'phase10/artifacts/selected/modules'
expected=json.loads((root/'phase11/phase10-baseline-manifest.json').read_text())
assert all(hashlib.sha256((base/n).read_bytes()).hexdigest()==h for n,h in expected.items())
for f in base.glob('*.hsaco'):
 if f.stem=='c32-wave1-fast' and (out/f.name).exists():continue
 shutil.copy2(f,out/f.name)
shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
source=folder/'source';source.mkdir(exist_ok=True)
for f in (root/'hip').iterdir():
 if f.is_file() and f.suffix in ('.h','.hip','.inc','.py','.ps1'):shutil.copy2(f,source/f.name)
shutil.copy2(root/'Development/HIP/swin_persistent_types.h',source/'swin_persistent_types.h')
orig=build.phase10_optimize_fp8
candidate={'half-store':fold_ffn_half_store,'half-feature-pack':pack_ffn_half_features}[a.variant]
build.phase10_optimize_fp8=lambda text:candidate(orig(text))
mod=next(m for m in build.parse_ps1_modules(source/'build-modules.ps1') if m['name']=='c32-wave1-fast')
mod['defines'].append('SM86_PHASE11_FINGERPRINT 0x'+hashlib.sha256(Path(__file__).with_name('transform.py').read_bytes()).hexdigest()[:8])
remove=build.os.remove
if a.keep_ir:
 def capture(path):
  if str(path).endswith('.ll'):shutil.copy2(path,folder/(Path(path).name+'.inspect'))
  return remove(path)
 build.os.remove=capture
stamp=out/'c32-wave1-fast.build-key'
if a.keep_ir and not (folder/'c32-wave1-fast.opt.ll.inspect').exists() and stamp.exists():stamp.unlink()
r=build.compile_one_module(mod,str(source),str(out),str(source/'sm86_compat.h'),str(root/'hip/ptx2cubin'));print(r,flush=True);assert r[1],r[2]
(folder/'modules.sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
(folder/'build.json').write_text(json.dumps({'compiled':r,'parent':str(base),'candidate':a.variant},indent=2)+'\n')
