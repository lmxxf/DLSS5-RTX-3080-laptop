#!/usr/bin/env python3
"""Verify source identity and package only module objects and their manifest."""
import argparse,hashlib,json,zipfile
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('directory',type=Path);p.add_argument('--reference',type=Path,required=True);p.add_argument('--zip',type=Path,required=True);a=p.parse_args()
d=json.loads((a.directory/'manifest.json').read_text(encoding='utf-8-sig'));ref=json.loads(a.reference.read_text(encoding='utf-8-sig'))
assert len(d['modules'])==60
source={r['module']:r['source_sha256'] for r in ref['modules']}
seen=set()
with zipfile.ZipFile(a.zip,'w',zipfile.ZIP_DEFLATED) as z:
    for r in d['modules']:
        key=r['target'],r['module'];assert key not in seen;seen.add(key)
        assert r['source_sha256']==source[r['module']],key
        f=a.directory/r['target']/(r['module']+'.hsaco')
        assert hashlib.sha256(f.read_bytes()).hexdigest()==r['sha256'].lower(),key
        z.write(f,f.relative_to(a.directory))
    z.write(a.directory/'manifest.json','manifest.json')
assert {a for a,b in seen}=={'gfx1200','gfx1201'}
print('60 source/object hashes verified; archive',hashlib.sha256(a.zip.read_bytes()).hexdigest())
