#!/usr/bin/env python3
"""Deferred-unpack control retaining the original 3-plane shared Q/K/V C32."""
from pathlib import Path
import sys,importlib.util
root=Path(__file__).resolve().parents[1]
src=root/'phase3/artifacts/deferred-control-source'
sys.path.insert(0,str(src))
spec=importlib.util.spec_from_file_location('control_builder',src/'build_sm86_modules.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
out=root/'phase3/artifacts/c32-control-build';out.mkdir(exist_ok=True)
mods=build.parse_ps1_modules(root/'hip/build-modules.ps1')
m=next(m for m in mods if m['name']=='c32-wave1-fast')
r=build.compile_one_module(m,str(src),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'))
print(r)
if not r[1]:sys.exit(1)
