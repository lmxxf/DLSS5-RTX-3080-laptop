#!/usr/bin/env python3
"""Build an isolated copy of rtc_compile selecting COMGR2; kernels unchanged."""
import argparse,subprocess,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
source=(repo/'hip/rtc_compile.cpp').read_text()
assert source.count('load(L"amd_comgr_3.dll")')==1
source=source.replace('load(L"amd_comgr_3.dll")','load(L"amd_comgr_2.dll")').replace('COMGR3 LoadLibrary','COMGR2 LoadLibrary')
cpp=a.out/'rtc_compile-comgr2.cpp';exe=a.out/'rtc_compile-comgr2.exe';cpp.write_text(source)
cmd=['x86_64-w64-mingw32-g++','-std=c++17','-O2','-static',str(cpp),'-o',str(exe)]
subprocess.run(cmd,check=True)
(a.out/'comgr2-tool.json').write_text(json.dumps(dict(command=cmd,source_sha256=hashlib.sha256(cpp.read_bytes()).hexdigest(),exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest()),indent=2)+'\n')
