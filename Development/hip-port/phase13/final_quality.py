from pathlib import Path
import json,hashlib,argparse
r=Path(__file__).resolve().parents[1];p=r/'phase13';m=p/'artifacts/selected/modules'
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(m.glob('*.hsaco'))}
assert len(hashes)==40
(p/'selected-modules.sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
base=json.loads((p/'phase12-baseline-manifest.json').read_text())
changed=[n for n,h in hashes.items() if base[n]!=h]
# Fingerprints live only in generated-source comments, not emitted machine code.
assert changed==[],changed
args=argparse.ArgumentParser();args.add_argument('--forward',default='selected');args.add_argument('--reverse',default='selected-reverse');args.add_argument('--baseline',default='baseline-final');args=args.parse_args()
data=json.loads((p/'results.json').read_text());rows={}
for v in [args.forward,args.reverse]:
 rows[v]={}
 for w in ['1280','1600','1920']:
  c=data[v][w];assert len(c['kernels'])==32
  assert all(x['lmem']==0 for x in c['kernels'].values())
  assert c['invalid']==c['first_last_bitdiff']==c['vs_phase12']['bitdiff']==0
  if w!='1280':
   b=data[args.baseline][w]['f32_visible'];assert c['f32_visible']['psnr_peak1']==b['psnr_peak1']
  rows[v][w]={k:c[k] for k in ['invalid','first_last_bitdiff','vs_phase12','f32_visible'] if k in c}
(p/'quality.json').write_text(json.dumps({'changed_modules':changed,'rounds':rows,'720_f32_trusted':False},indent=2)+'\n')
print('PASS: 2 rounds x 3 tiers, 32/32 LOCAL0, bitdiff0; trusted 900/1080 F32 PSNR unchanged')
