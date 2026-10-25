#!/usr/bin/env python3
"""Build only changed modules over a verified 40-module parent set."""
from pathlib import Path
import argparse,sys,shutil,json,hashlib,re
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
p=argparse.ArgumentParser();p.add_argument('variant');p.add_argument('--parent',type=Path,default=root/'phase5/artifacts/selected/modules');p.add_argument('--modules',nargs='+',required=True);p.add_argument('--small-w16',action='store_true');p.add_argument('--q-mask',type=int);p.add_argument('--prefix-bound',type=int);p.add_argument('--c32-bound',type=int);a=p.parse_args()
folder=root/'phase5/artifacts'/a.variant;out=folder/'modules';out.mkdir(parents=True,exist_ok=True)
for f in a.parent.glob('*.hsaco'):
 # Preserve an existing compiled target; overwriting it would invalidate its cache stamp.
 if f.stem in a.modules and (out/f.name).exists():continue
 shutil.copy2(f,out/f.name)
shutil.copy2(a.parent/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
source=folder/'source';source.mkdir(exist_ok=True)
for src in (root/'hip').iterdir():
 if src.is_file() and src.suffix in ('.h','.hip','.inc','.py','.ps1'):shutil.copy2(src,source/src.name)
shutil.copy2(root/'Development/HIP/swin_persistent_types.h',source/'swin_persistent_types.h')
mods=build.parse_ps1_modules(source/'build-modules.ps1');result=[]
remove_original=build.os.remove
# Record post-SSA loop types before normal cleanup; this never changes codegen.
def record_then_remove(path):
 if str(path).endswith('.opt.ll'):
  ir=Path(path).read_text();rows={}
  for m in re.finditer(r'(define[^\n]+\{\n)(.*?)(\n\}\n)',ir,re.S):
   name=re.search(r'@([^ (]+)\(',m[1])
   if name and any(x in name[1] for x in ('c64_wave2','c128_wave2','c256_wave2','vit_stream_contract','vit_stream_project')):
    rows[name[1]]={'phi_u4':len(re.findall(r'= phi <4 x i32>',m[2])),'phi_f8':len(re.findall(r'= phi <8 x float>',m[2]))}
  (folder/(Path(path).name+'.ssa.json')).write_text(json.dumps(rows,indent=2)+'\n')
 return remove_original(path)
build.os.remove=record_then_remove
for name in a.modules:
 mod=next(m for m in mods if m['name']==name)
 if a.small_w16:
  mod['defines']=[('W2_FFN_QT_SMALL_MASK 3' if x.startswith('W2_FFN_QT_SMALL_MASK ') else x) for x in mod['defines']]
  mod['defines'].append('W2_FFN_W16_SMALL 3')
 if a.q_mask is not None:
  mod['defines']=[x for x in mod['defines'] if not x.startswith('SM86_C32_REGISTER_Q_MASK ')]
  mod['defines'].append('SM86_C32_REGISTER_Q_MASK '+str(a.q_mask))
 if a.prefix_bound is not None:
  mod['defines']=[x for x in mod['defines'] if not x.startswith('SM86_C32_PREFIX_MINBLOCKS ')]
  mod['defines'].append('SM86_C32_PREFIX_MINBLOCKS '+str(a.prefix_bound))
 if a.c32_bound is not None:
  mod['defines']=[x for x in mod['defines'] if not x.startswith('SM86_C32_MINBLOCKS ')]
  mod['defines'].append('SM86_C32_MINBLOCKS '+str(a.c32_bound))
 (source/(name+'.json')).write_text(json.dumps(mod,indent=2)+'\n')
 r=build.compile_one_module(mod,str(source),str(out),str(source/'sm86_compat.h'),str(root/'hip/ptx2cubin'))
 print(r,flush=True);result.append(r)
 if not r[1]:sys.exit(1)
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.hsaco'))};assert len(manifest)==40
(folder/'modules.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
(folder/'build.json').write_text(json.dumps({'parent':str(a.parent),'compiled':result},indent=2)+'\n')
print('PASS: modified modules compiled/loaded; complete set contains 40 modules',flush=True)
