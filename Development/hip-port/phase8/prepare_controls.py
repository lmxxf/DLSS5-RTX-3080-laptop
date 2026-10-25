"""Compose exact module-level controls, without recompiling identical kernels."""
from pathlib import Path
import shutil,hashlib,json
root=Path(__file__).resolve().parents[1];phase=root/'phase8';base=root/'phase7/artifacts/selected/modules';full=phase/'artifacts/full/modules'
assert len(list(full.glob('*.hsaco')))==40 and (full/'AMPERE_WEIGHTS_V2').exists()
for name,replacements in [('c32-only',['c32-wave1-fast']),('layout-only',['c32-wave1-fast','c64-wave2-fast'])]:
 out=phase/'artifacts'/name/'modules';out.mkdir(parents=True,exist_ok=True)
 for src in base.glob('*.hsaco'):shutil.copy2(full/src.name if src.stem in replacements else src,out/src.name)
 shutil.copy2(base/'AMPERE_WEIGHTS_V2',out/'AMPERE_WEIGHTS_V2')
 (out.parent/'modules.sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.hsaco'))},indent=2)+'\n')
 (out.parent/'composition.json').write_text(json.dumps({'baseline':str(base),'new_modules':replacements},indent=2)+'\n')
