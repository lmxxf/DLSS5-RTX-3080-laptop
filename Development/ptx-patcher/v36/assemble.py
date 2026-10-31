from pathlib import Path
import os,json,hashlib
from analysis_common import b
from pe_fatbins import assemble
p=Path(__file__).resolve().parent;root=Path('/mnt/c/DLSS5-5090-dll');raw=bytearray((root/'nvngx_dlssnr.dll').read_bytes());b.dp.strip_authenticode(raw);ls=b.dp.find_fatbins(raw);b.dp.apply_host_patches(raw,(b.dp.AMPERE,));cs=json.loads((p/'candidates.json').read_text())
for fb in range(7):
 name=f'pack4_fb{fb}';cache=p/'artifacts'/name;cache.mkdir(parents=True,exist_ok=True);blobs={}
 for i in range(15):
  srcmode='pack4_all' if i==fb else 'baseline'
  for suffix in ['cubin','ptx','bin']:
   src=p/f'artifacts/{srcmode}/fatbin{i:02}.{suffix}';dst=cache/f'fatbin{i:02}.{suffix}'
   if not dst.exists():os.link(src,dst)
  blobs[i]=(cache/f'fatbin{i:02}.bin').read_bytes()
 data,manifest=assemble(raw,ls,blobs,b.dp);b.fast_update_pe_checksum(data);f=root/f'nvngx_dlssnr_sm86_v36_{name}.dll';f.write_bytes(data);cs[name]={'path':str(f),'sha256':hashlib.sha256(data).hexdigest(),'manifest':manifest,'target_fbs':[fb],'approximate':True,'branch':5}
(p/'candidates.json').write_text(json.dumps(cs,indent=2)+'\n')
records=json.loads((p/'artifacts/build-records-full.json').read_text());r=[r for m in records['pack_proven'] for r in m['ranges']];assert len(r)==8944;__import__('storage').save_ranges(r)
print('empirical modules assembled; range audit',len(r))
