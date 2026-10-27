from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;r=json.loads((p/'builds.json').read_text())['combo'];s=json.loads((p/'summary.json').read_text())['combo']
assert all(all(d['gain_percent']>0 for d in tier['directions'].values()) for tier in s.values())
selected={'variant':'combo','path':'/mnt/c/DLSS5-5090-dll/nvngx_dlssnr_sm86_v22.dll','sha256':r['sha256'],'bytes':r['bytes'],'half_pack':'swar','bulk_completion':'mbarrier','caps':{str(i):255 for i in [0,3,4,5,6]},'three_tiers':s,'reason':'Combination wins against paired V2.1 in both forward/reverse rounds at all tiers. Preserve V2.1 compatible CLI defaults; use build_recommended.py for V2.2.'}
(p/'selected.json').write_text(json.dumps(selected,indent=2)+'\n')
