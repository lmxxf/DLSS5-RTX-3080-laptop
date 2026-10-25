from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'hip'))
import build_sm86_modules as build
build.PHASE10_FP8=True
sys.argv=[str(root/'hip/build_sm86_modules.py'),str(root/'hip'),str(root/'phase10/artifacts/optimized/modules')]
build.main()
