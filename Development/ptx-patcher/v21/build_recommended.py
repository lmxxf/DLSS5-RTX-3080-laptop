"""Rebuild the measured V2.1 recommendation from the original source DLL."""
from pathlib import Path
import subprocess,os,json,hashlib
p=Path(__file__).resolve().parent;selected=json.loads((p/'selected.json').read_text());root=Path('/mnt/c/DLSS5-5090-dll');out=root/'nvngx_dlssnr_sm86_v21.dll'
args=['python3',str(p.parent/'build_sm86_dlls.py'),'--output',str(out)]
for i,cap in selected['caps'].items():args+=['--maxnreg',f'{i}:{cap}']
env=os.environ.copy();env['DLSSNR_BUILD_CACHE']=str(p/'artifacts/final')
subprocess.run(args,env=env,check=True)
sha=hashlib.sha256(out.read_bytes()).hexdigest();assert sha==selected['sha256'],(sha,selected['sha256']);print('PASS final full15 source rebuild SHA equals measured control',sha)
