#!/usr/bin/env python3
"""Prepare an isolated all-case runner from the proven kernel-map replay.

Only comparison behavior changes: report every finite-output mismatch instead
of stopping at the first case. Compile/runtime failures still stop the suite.
"""
from pathlib import Path
import argparse
import hashlib
import json

p=argparse.ArgumentParser(__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[3]
source=root/'Development/HIP/experiments/kernel-map/regression.ps1'
s=source.read_text(encoding='utf-8-sig')
old='if($different){throw "Output changed $t ($different/12)"};"SAME $b $t"'
new='if($different){Write-Output "DIFFERENT $b $t $different/12"}else{Write-Output "SAME $b $t"}'
assert s.count(old)==1
s=s.replace(old,new)
# Expand the existing idle guard for other isolated lab runners.
s=s.replace('^microbench|^runtime-smoke','^microbench|^runtime-smoke|^jobbench|^recorder')
(a.out/'regression.ps1').write_text(s)
(a.out/'runner-provenance.json').write_text(json.dumps(dict(source=str(source.relative_to(root)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(s.encode()).hexdigest()),indent=2)+'\n')
