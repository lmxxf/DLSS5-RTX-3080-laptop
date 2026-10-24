#!/usr/bin/env python3
"""Run the two fork MIR tests without configuring the entire LLVM test suite."""
from pathlib import Path
import argparse,shutil,subprocess
p=argparse.ArgumentParser(__doc__);p.add_argument('--source',type=Path,default=Path('/home/lmxxf/work/llvm-project'));p.add_argument('--bin',type=Path,default=Path('/home/lmxxf/work/llvm-build-dlss5-gfx12/bin'));p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
for name in ['dlss5-vopd-lookahead.mir','dlss5-vopd-boundaries.mir']:shutil.copy2(a.source/'llvm/test/CodeGen/AMDGPU'/name,a.out/name)
(a.out/'lit.cfg.py').write_text("import os, lit.formats\nconfig.name='DLSS5 LLVM21 MIR'\nconfig.test_format=lit.formats.ShTest(True)\nconfig.suffixes=['.mir']\nconfig.test_source_root="+repr(str(a.out))+"\nconfig.test_exec_root="+repr(str(a.out))+"\nconfig.environment['PATH']="+repr(str(a.bin))+"+os.pathsep+os.environ['PATH']\n")
subprocess.run(['python3',str(a.source/'llvm/utils/lit/lit.py'),'-v',str(a.out)],check=True)
