"""Reproduce V2.4 without touching production fast.dll or release ZIPs."""
from pathlib import Path
import json,subprocess,os,hashlib
p=Path(__file__).resolve().parent;s=json.loads((p/'selected.json').read_text());out=Path(s['path']);args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out),'--half-pack',s['half_pack'],'--bulk-completion',s['bulk_completion'],'--fp8-decode',s['fp8_decode'],'--v24-mask',str(s['mask'])]
for i,cap in s['caps'].items():args+=['--maxnreg',f'{i}:{cap}']
env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts/selected');subprocess.run(args,env=env,check=True)
sha=hashlib.sha256(out.read_bytes()).hexdigest();assert sha==s['sha256'],(sha,s['sha256']);assert out.stat().st_size==s['bytes'];print('PASS selected rebuild',sha)
