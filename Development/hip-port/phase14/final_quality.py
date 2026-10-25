from pathlib import Path
import json,hashlib,numpy as np,argparse
r=Path(__file__).resolve().parents[1];p=r/'phase14';a=argparse.ArgumentParser();a.add_argument('--forward',default='default400');a.add_argument('--reverse',default='default400-reverse');a=a.parse_args()
mods=p/'artifacts/selected/modules';hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(mods.glob('*.hsaco'))};assert len(hashes)==40
assert hashes==json.loads((p/'selected-modules.sha256.json').read_text());old=json.loads((p/'phase12-baseline-manifest.json').read_text());changed=[n for n,h in hashes.items() if old[n]!=h];assert len(changed)==7
load=json.loads((p/'cuda-load-verification.json').read_text());assert len(load)==40 and sum(x['entries'] for x in load)==1918
manifest=json.loads((p/'gold-manifest.json').read_text());assert hashlib.sha256((p/'artifacts/gold/f32-720p-1280x768.rgb32').read_bytes()).hexdigest()==manifest['sha256']
initial=json.loads((p/'initial-quality.json').read_text());data=json.loads((p/'results.json').read_text());rows={}
for v in [a.forward,a.reverse]:
 rows[v]={}
 for w in ['1280','1600','1920']:
  c=data[v][w];assert c['invalid']==c['first_last_bitdiff']==c['vs_corrected_output']['bitdiff']==0
  assert len(c['kernels'])==32 and all(x['lmem']==0 for x in c['kernels'].values())
  assert c['visible_vs_trusted_F32']['psnr_peak1']==initial[w]['visible_psnr_peak1']
  if w=='1280':assert c['vs_phase12_old']['bitdiff']==2947224 and c['attention_entry']=='vit_attention_fused_400_bytein_bout'
  else:assert c['vs_phase12_old']['bitdiff']==0
  m=json.loads((p/f'{v}-{w}-run.json').read_text());assert m['module_hashes']==hashes and not m['cap_forced'];assert 'DLSS5_LAB_ATTN400' not in m['flags']
  rows[v][w]={k:c[k] for k in ['gpu_min','gpu_median','wall_median','profile_total','invalid','first_last_bitdiff','vs_phase12_old','visible_vs_trusted_F32','attention_entry','telemetry']}
(p/'quality.json').write_text(json.dumps({'changed_modules':changed,'module_count':40,'entry_count':1918,'new_720_F32_gold_sha256':manifest['sha256'],'rounds':rows,'default':'Native Host chooses400 for<=256; corrected256 onlyexplicit benchmark control'},indent=2)+'\n')
print('PASS: default400 two rounds3tiers; 40/1918 loaded;32/32 LOCAL0; corrected720 gold;900/1080old0bit/PSNR unchanged')
