from pathlib import Path
import sys,os,json,hashlib
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parent));import build_sm86_dlls as b
from pe_fatbins import assemble
cs=json.loads((p/'candidates.json').read_text());root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(raw);locs=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,))
for name,target in [('quad_fb0145',{0,1,4,5})]:
 cache=p/'artifacts'/name;cache.mkdir(parents=True,exist_ok=True);blobs={}
 for fb in range(15):
  mode='quad_local' if fb in target else 'baseline'
  for suffix in ['bin','cubin','ptx']:
   src=p/f'artifacts/{mode}/fatbin{fb:02}.{suffix}';dst=cache/f'fatbin{fb:02}.{suffix}'
   if not dst.exists():os.link(src,dst)
  blobs[fb]=(cache/f'fatbin{fb:02}.bin').read_bytes()
 data,manifest=assemble(raw,locs,blobs,b.dp);b.fast_update_pe_checksum(data);f=root/f'nvngx_dlssnr_sm86_v34_{name}.dll';f.write_bytes(data);cs[name]={'path':str(f),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest,'changed_fbs':sorted(target)}
(p/'candidates.json').write_text(json.dumps(cs,indent=2)+'\n')
