"""Remove only Phase11's redundant temporary artifacts, preserving final modules/evidence."""
from pathlib import Path
import json,hashlib,os
root=Path(__file__).resolve().parent;removed=[];linked=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for variant in ['half-store','half-feature-pack']:
 folder=root/'artifacts'/variant
 for p in (folder/'modules').glob('*.hsaco'):
  if p.stem=='c32-wave1-fast':continue
  original=root.parent/'phase10/artifacts/selected/modules'/p.name
  assert sha(p)==sha(original)
  removed.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p),'reason':'unchanged candidate copy; build_variant reconstructs from immutable Phase10'})
  p.unlink()
 for p in folder.glob('*.ll.inspect'):
  removed.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p),'reason':'full temporary IR; SSA audit retained and --keep-ir reproduces'})
  p.unlink()
for p in (root/'artifacts/audit').glob('*-c32.sass'):
 removed.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p),'reason':'full derived disassembly; counts/hot extracts retained, audit_sass regenerates'})
 p.unlink()
for w in [1280,1600,1920]:
 canonical=root/f'artifacts/outputs/baseline-a-{w}.rgb32';digest=sha(canonical)
 for p in (root/'artifacts/outputs').glob(f'*-{w}.rgb32'):
  if p==canonical or sha(p)!=digest or os.path.samefile(p,canonical):continue
  size=p.stat().st_size;p.unlink();os.link(canonical,p)
  linked.append({'path':str(p.relative_to(root)),'canonical':str(canonical.relative_to(root)),'bytes':size,'sha256':digest})
report={'removed':removed,'identical_output_hardlinks':linked,'removed_file_bytes':sum(x['bytes'] for x in removed),'deduplicated_output_bytes':sum(x['bytes'] for x in linked),'retained':'Full final40 modules; changed candidate C32 cubins, source, hashes, logs, numeric results, baseline/final raw output paths, unvalidated F32 diagnostic'}
(root/'cleanup-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['removed','identical_output_hardlinks']})
