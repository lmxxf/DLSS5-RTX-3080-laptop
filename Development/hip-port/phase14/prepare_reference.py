"""Recreate ignored fixtures from the immutable archives, never replace a gold silently."""
from pathlib import Path
import subprocess,sys,datetime,hashlib,json,shutil,numpy as np,argparse
p=Path(__file__).resolve().parent;r=p.parent;a=argparse.ArgumentParser();a.add_argument('--verify-existing',action='store_true');a=a.parse_args();initial=json.loads((p/'initial-quality.json').read_text());manifest=json.loads((p/'gold-manifest.json').read_text())
def check(path,sha):assert path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==sha,path
if not a.verify_existing:
 for name in ['build_host.py','build_fixed.py']:
  subprocess.run([sys.executable,str(p/name)],check=True)
 tag='reference-retest-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
 def bench(v,w,mods,f32=False):
  cmd=[sys.executable,str(p/'bench.py'),v,'--width',str(w),'--modules',str(mods),'--warmup','0','--iterations','1']
  if f32:cmd+=['--f32']
  subprocess.run(cmd,check=True);return p/f'artifacts/outputs/{v}-{w}.rgb32'
 for w in [1600,1920]:
  fresh=bench(tag+'-control',w,p/'artifacts/f32-control/modules',True);check(fresh,initial[str(w)]['F32_sha256'])
 for w in [1280,1600,1920]:
  fresh=bench(tag+'-gold',w,p/'artifacts/f32-fixed/modules',True);check(fresh,initial[str(w)]['F32_sha256']);canonical=p/f'artifacts/outputs/gold-f32-{w}.rgb32'
  if canonical.exists():check(canonical,initial[str(w)]['F32_sha256'])
  else:shutil.copy2(fresh,canonical)
  native=bench(tag+'-native',w,p/'artifacts/selected/modules');check(native,initial[str(w)]['FP16_sha256']);canonical=p/f'artifacts/outputs/fixed-quick-{w}.rgb32'
  if canonical.exists():check(canonical,initial[str(w)]['FP16_sha256'])
  else:shutil.copy2(native,canonical)
 gold=p/'artifacts/gold/f32-720p-1280x768.rgb32';gold.parent.mkdir(exist_ok=True)
 if gold.exists():check(gold,manifest['sha256'])
 else:shutil.copy2(p/'artifacts/outputs/gold-f32-1280.rgb32',gold)
check(p/'artifacts/gold/f32-720p-1280x768.rgb32',manifest['sha256'])
for w in [1280,1600,1920]:
 check(p/f'artifacts/outputs/fixed-quick-{w}.rgb32',initial[str(w)]['FP16_sha256']);check(p/f'artifacts/outputs/gold-f32-{w}.rgb32',initial[str(w)]['F32_sha256'])
print('PASS: corrected fixtures and new720 gold verified; existing900/1080 calibration hashes match')
