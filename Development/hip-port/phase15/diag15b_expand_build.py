from diag15b_paths import ROOT
from pathlib import Path
import importlib.util,sys
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));sys.dont_write_bytecode=True
for kind in ['native','f32']:
 if kind=='native':
  import build_sm86_modules as b
  header=r/'hip/sm86_compat.h'
 else:
  source=r/'phase1/artifacts/f32-source';spec=importlib.util.spec_from_file_location('diag15b_f32',source/'build_sm86_modules.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);header=source/'sm86_compat.h'
 out=ROOT/'expand'/kind;out.mkdir(parents=True,exist_ok=True);mod=dict(name='expand-canonical',sources=['../phase15/diag15b_expand.hip'],defines=[],l23defines=[]);result=b.compile_one_module(mod,str(r/'hip'),str(out),str(header),str(r/'hip/ptx2cubin'));assert result[1],result[2];print(kind,result[:3],flush=True)
