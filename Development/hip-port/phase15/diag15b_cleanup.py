from pathlib import Path
import hashlib,json,shutil
from diag15b_paths import ROOT
p=Path(__file__).resolve().parent;art=(p/'artifacts').resolve();assert ROOT.is_relative_to(art) and ROOT.name.startswith('diagnostic15b')
records=[];removed=[]
def record(f):
 row={'path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};records.append(row);return row
# The original manual run and the full entry replay were independently checked.
old=art/'diagnostic15b'
if old.exists() and old!=ROOT:
 for f in old.rglob('*'):
  if f.is_file():record(f);removed.append(str(f))
 shutil.rmtree(old)
for f in list(ROOT.rglob('*')):
 if not f.is_file():continue
 rel=f.relative_to(ROOT);parts=rel.parts;keep=True
 if parts[0]=='reference' and f.name!='deep_fast-packed-fast.hsaco':keep=False
 if f.suffix in ['.ll'] or f.name.endswith('.phase1.cu'):keep=False
 if parts[0]=='traces':
  # Retain main outputs, actual input proof, firstexpand, allF32attention inputs/outputs.
  keep=f.name in ['0.rgb32','working-input.bin','expand-0-in.bin','expand-0-out.bin'] or ('f32' in parts and f.name.startswith('attention-'))
 if parts[0]=='post':
  if parts[1]!='ramp1024':keep=f.name.endswith('rgb.bin') or f.name in ['0.rgb32','post-head-weights.bin','post-scales.bin','prepare-qkv.bin','prepare-head.bin']
 # Inputs, isolated replay accumulators and actual target post/encoder data remain.
 if not keep:record(f);removed.append(str(f));f.unlink()
(p/'diag15b-cleanup.json').write_text(json.dumps({'diagnostic_root':str(ROOT),'hashed_removed_files':records,'removed_paths':removed,'preserved':'Frozen inputs/outputs and producer SHA proof, actualF32 attention QKV/AV, canonical replay matrices, target1024 post features/low/skip and wave captures, CPU summaries, plots; production/old gold/other phases untouched.'},indent=2)+'\n');print('Removed temporary diagnostic bytes',sum(x['bytes'] for x in records))
