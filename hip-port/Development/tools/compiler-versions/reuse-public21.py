#!/usr/bin/env python3
"""Reuse just-completed LLVM21 regression after source/module identity checks.

The driver rebuild is separately proven equal in .text/.rodata/.note to that
regression's baseline. Preserve original logs; rename only collection labels.
"""
import argparse,csv,hashlib,io,json,shutil,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser(__doc__);p.add_argument('--old',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--zip',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
repo=Path(__file__).resolve().parents[3]
identity=json.loads((repo/'Development/results/compiler-versions-20260929/driver-identity-pass.json').read_text());assert identity['pass_identity'] and len(identity['modules'])==60
old=repo/'Development/results/llvm-fork-20260929'
assert json.loads((old/'regression-summary.json').read_text())['pass']
for src in a.old.rglob('*'):
    if not src.is_file():continue
    relative=str(src.relative_to(a.old)).replace('runtime-regression-L-','runtime-regression-L21-')
    if relative in ['hashes.csv','snapshot.json']:continue
    if relative.startswith('regression-'):relative=relative.replace('regression-','regression-L21-',1)
    dst=a.out/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
rows=list(csv.DictReader((old/'hashes.csv').open()))
for r in rows:r['batch']=r['batch'].replace('runtime-regression-L-','runtime-regression-L21-')
with (a.out/'hashes-L21.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
subprocess.run(['python3',str(Path(__file__).with_name('analyze-results.py')),'--version','L21','--collected',str(a.out),'--out',str(a.out)],check=True)
provenance=dict(reused=True,reason='Same 30 generated source hashes; same 60 public21 module hashes; rebuilt driver code/metadata equals previous baseline; same production host and fixtures.',source_results='Development/results/llvm-fork-20260929',raw_archive_sha256=hashlib.sha256((old/'replay-evidence.zip').read_bytes()).hexdigest())
(a.out/'reuse-L21.json').write_text(json.dumps(provenance,indent=2)+'\n')
with zipfile.ZipFile(a.zip,'w',zipfile.ZIP_DEFLATED) as z:
    for f in a.out.rglob('*'):
        if f.is_file():z.write(f,f.relative_to(a.out))
