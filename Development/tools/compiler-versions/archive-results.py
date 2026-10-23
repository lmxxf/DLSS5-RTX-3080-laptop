#!/usr/bin/env python3
"""Archive original replay files, replacing only redundant PS ETS AE JSON.

PowerShell's Get-Content string metadata bloated adaptive-*.json. The actual
per-slot adaptive.csv files are copied byte-for-byte. The replacement JSON is
the independent Python comparison derived from those CSVs.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('--version',required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
dest=a.out/f'replay-{a.version}.zip'
with zipfile.ZipFile(a.raw) as src,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        name=item.filename.replace('\\','/')
        if name==f'adaptive-{a.version}.json':continue
        dst.writestr(name,src.read(item))
    dst.write(a.out/f'adaptive-{a.version}.json',f'adaptive-{a.version}.json')
record=dict(raw_archive=str(a.raw),raw_sha256=hashlib.sha256(a.raw.read_bytes()).hexdigest(),archive_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),changed_entry=f'adaptive-{a.version}.json',reason='Replace redundant PowerShell ETS expansion with independently recomputed comparison; per-slot source CSVs unchanged')
(a.out/f'archive-{a.version}.json').write_text(json.dumps(record,indent=2)+'\n')
