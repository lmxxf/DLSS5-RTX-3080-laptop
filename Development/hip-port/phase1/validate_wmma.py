#!/usr/bin/env python3
"""Build and run the independent K16/K32 mapping probe on the current GPU."""
import sys
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'hip'))
from build_sm86_modules import compile_one_module
out=root/'phase1/artifacts/probe'
out.mkdir(parents=True,exist_ok=True)
mod=dict(name='wmma_probe',sources=['../Development/HIP/wmma_probe.hip'],defines=[],l23defines=[])
result=compile_one_module(mod,str(root/'hip'),str(out),str(root/'hip/sm86_compat.h'),str(root/'hip/ptx2cubin'))
if not result[1]:
    raise RuntimeError(result[2])
subprocess.run(['g++','-O2',str(root/'hip/wmma_validate_cuda.cpp'),'-L/usr/lib/wsl/lib','-lcuda','-o',str(out/'wmma_validate_cuda')],check=True)
subprocess.run([str(out/'wmma_validate_cuda'),str(out/'wmma_probe.hsaco'),'--fp16-acc'],check=True)
