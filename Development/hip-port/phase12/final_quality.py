from pathlib import Path
import json,hashlib
r=Path(__file__).resolve().parents[1];p=r/'phase12';m=p/'artifacts/selected/modules'
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(m.glob('*.hsaco'))}
assert len(hashes)==40
(p/'selected-modules.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
base=json.loads((p/'phase11-baseline-manifest.json').read_text())
changed=[n for n,h in hashes.items() if base[n]!=h]
# Fingerprints live only in generated-source comments, not emitted machine code.
assert changed==['c32-wave1-fast.hsaco'],changed
assert hashes['c32-wave1-fast.hsaco']==hashlib.sha256((p/'artifacts/c32-av/modules/c32-wave1-fast.hsaco').read_bytes()).hexdigest()
data=json.loads((p/'results.json').read_text());rows={}
for v in ['selected','selected-reverse']:
 rows[v]={}
 for w in ['1280','1600','1920']:
  c=data[v][w];assert len(c['kernels'])==32
  assert all(x['lmem']==0 for x in c['kernels'].values())
  assert c['invalid']==c['first_last_bitdiff']==c['vs_phase11']['bitdiff']==0
  if w!='1280':
   b=data['baseline-final'][w]['f32_visible'];assert c['f32_visible']['psnr_peak1']==b['psnr_peak1']
  rows[v][w]={k:c[k] for k in ['invalid','first_last_bitdiff','vs_phase11','f32_visible'] if k in c}
(p/'quality.json').write_text(json.dumps({'changed_modules':changed,'rounds':rows,'720_f32_trusted':False},indent=2)+'\n')
print('PASS: 2 rounds x 3 tiers, 32/32 LOCAL0, bitdiff0; trusted 900/1080 F32 PSNR unchanged')
