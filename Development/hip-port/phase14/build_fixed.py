from pathlib import Path
import sys,shutil,json,hashlib,importlib.util
r=Path(__file__).resolve().parents[1];p=r/'phase14';sys.path.insert(0,str(r/'hip'))
from phase14_transform import fix_legacy_attention_abi
sys.dont_write_bytecode=True
for kind in ['fixed','f32-control','f32-fixed']:
 if kind=='fixed':
  import build_sm86_modules as b
  source=r/'hip';base=r/'phase12/artifacts/selected/modules'
 else:
  frozen=r/'phase1/artifacts/f32-source';source=r/'hip';base=r/'phase1/artifacts/f32-modules'
  spec=importlib.util.spec_from_file_location('phase14_frozen_f32_builder',frozen/'build_sm86_modules.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
  original=b.transform_hip_to_sm86_cu
  if kind=='f32-fixed':b.transform_hip_to_sm86_cu=lambda *a:fix_legacy_attention_abi(original(*a))
 out=p/'artifacts'/kind/'modules';out.mkdir(parents=True,exist_ok=True)
 for f in base.glob('*.hsaco'):
  if f.name=='deep_fast-packed-fast.hsaco' and (out/f.name).exists():continue
  shutil.copy2(f,out/f.name)
 if kind=='fixed':shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
 mod=next(m for m in b.parse_ps1_modules(source/'build-modules.ps1') if m['name']=='deep_fast-packed-fast')
 mod['defines']+=['P14_FIXED_ABI 1','P14_ABI_HASH 0x'+hashlib.sha256((r/'hip/phase14_transform.py').read_bytes()).hexdigest()[:8]]
 result=b.compile_one_module(mod,str(source),str(out),str((source if kind=='fixed' else frozen)/'sm86_compat.h'),str(r/'hip/ptx2cubin'));print(kind,result,flush=True);assert result[1],result[2]
 (p/(kind+'-modules.sha256.json')).write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
