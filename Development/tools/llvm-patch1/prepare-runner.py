#!/usr/bin/env python3
"""Reuse the gated compiler comparison runner; add paired public/driver ABBA."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser(__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
for name in ['run-version.ps1','run-checked.ps1']:
    s=(repo/'Development/tools/compiler-versions'/name).read_text()
    s=s.replace("'L20','L21','L22'","'P'").replace('compiler-versions-20260929','llvm-patch1-20260929')
    if name=='run-version.ps1':
        s=s.replace("foreach($batch in 'timing1','timing2')", "foreach($batch in 'public1','public2','driver1','driver2')")
        s=s.replace("'correct','adaptive','timing1','timing2'", "'correct','adaptive','public1','public2','driver1','driver2'")
        s=s.replace('-TimingFrames 1000 *>','-TimingFrames 1000 -Base $(if($batch -like \'public*\'){\'O\'}else{\'A\'}) *>')
        s=s.replace('completed two 900/1080 ABBA batches','completed two 900/1080 ABBA batches against each baseline')
        anchor=' $driver=Get-Content '
        pos=s.index(anchor)
        s=s[:pos]+''' $off=Get-Content "$root\\manifest-O.json" -Raw|ConvertFrom-Json
 foreach($m in $off.modules|Where-Object{$_.target -eq 'gfx1201'}){if((Get-FileHash "$root\\flat-O\\$($m.module).hsaco").Hash.ToLower() -ne $m.sha256){throw 'Public baseline changed'}}
'''+s[pos:]
    (a.out/name).write_text(s)
